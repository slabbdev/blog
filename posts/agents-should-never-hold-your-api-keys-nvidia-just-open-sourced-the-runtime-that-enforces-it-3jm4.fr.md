---
titre: "Les agents ne devraient jamais détenir tes clés API. NVIDIA vient d'open-sourcer le runtime qui l'impose"
date: 2026-10-23
themes: agents, securite
resume: "NVIDIA open-source OpenShell : des sandboxes au niveau kernel pour les flottes d'agents, des credentials détenues par la gateway au lieu de l'agent, et chaque changement de policy vérifié par un prover Z3 SMT avant approbation humaine. Un walkthrough du repo, mécanisme par mécanisme."
source: https://dev.to/slabb/agents-should-never-hold-your-api-keys-nvidia-just-open-sourced-the-runtime-that-enforces-it-3jm4
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fj3f6fdyzoum3s4nrfb2l.png
image_alt: "Les agents ne devraient jamais détenir tes clés API — NVIDIA OpenShell : sandboxes, credentials en gateway, policies vérifiées par Z3"
---

> Chaque agent IA que tu fais tourner détient aujourd'hui tes secrets dans son environnement de process : clés API, credentials cloud, tokens. À une injection de prompt de l'exfiltration — et 2026 l'a prouvé deux fois, avec deux compromissions distinctes du proxy LLM le plus populaire de PyPI, en mars puis cette semaine. La réponse de NVIDIA est arrivée sur GitHub cette semaine : **OpenShell** (Apache 2.0) — un runtime où les flottes d'agents tournent dans des sandboxes au niveau kernel, **ne voient jamais de vraies credentials**, et où chaque changement de policy est vérifié par un **prover Z3 SMT** avant validation humaine.

Ce n'est pas un framework d'agents de plus. C'est la couche en dessous : confinement, custody, et preuves pour des flottes d'agents qui existent déjà. J'ai passé la soirée dans le repo — voici ce que ça fait vraiment, mécanisme par mécanisme.

## Les trois pièces

OpenShell, c'est trois composants : une **gateway** (le plan de contrôle), un **supervisor**, et des **sandboxes** (Ubuntu minimal par défaut, passthrough GPU optionnel, Kubernetes via Helm si tu es de taille flotte). Le modèle de policy couvre les règles filesystem, réseau et process ; l'enforcement est au kernel — chaque accès fichier, syscall et connexion réseau est vérifié au runtime, pas par une bibliothèque wrapper que l'agent pourrait oublier d'appeler.

Le quickstart fait deux commandes, sur macOS Apple Silicon, Linux ou WSL2 :

```bash
curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh
openshell sandbox create --name demo
```

La sandbox par défaut ne contient aucun agent — tu amènes le tien. Le walkthrough « premier agent » de la doc fait tourner OpenCode contre un modèle OpenRouter gratuit, ce qui permet de sentir toute la bête sans clé payante.

## Mécanisme un : les credentials quittent l'agent

C'est l'inversion qui compte. Le défaut actuel : tu exportes `OPENAI_API_KEY` dans l'environnement de l'agent, et tu pries. Le process détient les joyaux de la couronne dans `/proc/self/environ`, à une injection de prompt de les exfiltrer vers n'importe quelle URL que le modèle a décidée de fetcher.

La crate `providers` d'OpenShell restructure la custody :

- La **gateway** persiste les records de providers — clés API, bearer tokens, configs de comptes locaux — découverts dans ton environnement et tes fichiers de config, normalisés, et tenus hors des logs (« les appelants qui affichent des données de provider doivent redacter les champs sensibles par défaut » est écrit dans le contrat de la crate).
- Le **supervisor de sandbox** va chercher la config providers résolue auprès de la gateway et injecte les credentials dans les process enfants de l'agent.
- L'agent **ne détient aucune credential brute pour le monde extérieur** : chaque connexion réseau passe un check de policy avant de sortir de la sandbox, et les vraies credentials ne sont ajoutées qu'aux requêtes liées aux endpoints approuvés.

 Relis ça sous l'angle custody : le rayon d'explosion d'un agent compromis cesse d'être « toutes les clés de l'environnement » et devient « les endpoints que la policy de cette sandbox a nommés ». Ton agent peut toujours travailler — lire des fichiers, installer des paquets, appeler les APIs que tu as approuvées — mais les clés de tout le reste ne sont simplement plus dans la pièce.

## Mécanisme deux : un prover Z3 aux portes des changements de policy

La partie à laquelle je ne m'attendais pas à cette maturité : la crate `openshell-prover` est un **vérificateur formel des policies de sandbox**. De son propre README :

> Encode une policy + son jeu de credentials attaché + un registre de capacités binaires en **modèle Z3 SMT**, puis lance des requêtes de reachability pour détecter les changements de « credentialed-reach » et de capacités qu'un reviewer doit connaître.

Concrètement : quand un changement de policy est proposé — par toi, ou par l'agent lui-même — OpenShell ne se contente pas de diff le YAML. Il encode l'état projeté en SMT et pose les questions de reachability : *cette sandbox peut-elle maintenant joindre un nouveau hôte avec des credentials attachées ? appeler une nouvelle méthode d'API ?* Les deltas risqués **attendent une revue humaine**. Il y a aussi une API de containment : donne-lui une policy frontière d'opérateur et une candidate, il répond `Within` ou non — avec contre-exemples quand la réponse est non.

Et le mode d'échec est le bon : le modèle a des bornes (littéraux ASCII dans les sélecteurs réseau, pas d'octets NUL embarqués), et quand une policy utilise une forme qu'il ne peut pas modéliser, il renvoie `unsupported_policy_shape` — **« je ne peux rien prouver là-dessus »** — au lieu d'un feu vert. La propre consigne de la crate : traiter les valeurs inconnues comme fail-closed. Qui a écrit cette phrase s'est déjà fait brûler, dans le bon sens du terme.

Si tu suis le monde de la vérification formelle cette semaine, le timing tombe : Anthropic publiait le même soir que [les LLM rendent la vérification formelle faisable à beaucoup plus grande échelle](https://www.anthropic.com/research/formal-verification). Mets les deux bout à bout et un pattern émerge pour l'ère des agents — **les LLM proposent, les solveurs disposent** : le modèle écrit la policy, le prover tient la porte, l'humain signe les deltas.

## Ce que ça ne fait pas — à lire avant de déployer

Trois limites honnêtes, parce qu'un runtime qui s'appelle « safe, private » invite à en faire trop :

1. **Le confinement n'est pas la preuve.** OpenShell répond à *« que peut faire cet agent ? »* — il ne répond pas à *« qu'a réellement fait cet agent ? »* Un agent enfermé peut quand même prendre de mauvaises décisions dans ses murs, et après coup tu voudras un enregistrement infalsifiable de ce qui s'est passé, pas seulement les murs qui étaient debout. Ce sont des couches complémentaires — les murs et la boîte noire — et une flotte sérieuse finit par vouloir les deux.
2. **La gateway est le nouveau noyau de confiance.** Les credentials vivent maintenant avec la gateway au lieu de l'agent. C'est un rayon d'explosion strictement meilleur, mais ça déplace les joyaux — donc qui fait tourner la gateway, et comment elle est backupée et auditée, devient ta vraie frontière de sécurité. Du self-hosted via Helm est supporté ; traite cette machine comme les clés qu'elle détient.
3. **C'est du 0.1.x.** Cadence stable, vrais tests, process RFC, security policy — mais jeune. Les docs du prover énumèrent exactement quelles formes de policy sont hors modèle. Lis la support matrix avant de pointer une flotte de production dessus.

## Run it yourself

```bash
curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh
openshell sandbox create --name demo
# puis : docs.nvidia.com/openshell → « Run Your First Agent » (OpenCode + modèle OpenRouter gratuit)
```

Et pour le prover, le README de la crate porte un exemple de containment buildable depuis les sources : une policy frontière, une candidate, `check_within_boundary`, et un `CheckResult::Within` ou un contre-exemple. Dix minutes avec le schéma de policy t'apprennent plus sur le confinement d'agents qu'un mois de threads.

Repo : [github.com/NVIDIA/OpenShell](https://github.com/NVIDIA/OpenShell) · Docs : [docs.nvidia.com/openshell](https://docs.nvidia.com/openshell/latest/index.html) · Apache 2.0, SDKs en Python/TypeScript/Go/Rust, skills pour ton agent de code (`npx skills add NVIDIA/OpenShell`).

**TL;DR** — le stack de sécurité des agents s'assemble par couches ce mois-ci : des sandboxes kernel pour le confinement, des credentials détenues par la gateway pour la custody, des provers SMT pour la revue de policy, et (de l'autre camp) des journaux et attestations pour la preuve. Ton agent reste invraisemblable en tant que tel. Mais il peut enfin être *contenu, financé et prouvé* — ce que « trusted » était censé vouloir dire depuis le début.
