---
titre: "Gheist : 13 500 workflows de vol de secrets plantés avec des tokens GitHub volés — audite les tiens en 5 minutes"
date: 2026-10-26
themes: securite, github
resume: "La campagne Gheist a planté 13 500 workflows d'exfiltration avec des tokens GitHub volés — le base32 bat le masquage, permissions:{} ne protège rien, et le canal d'exfiltration est GitHub lui-même. L'audit qui te dit en 5 minutes si tu es touché."
source: https://dev.to/slabb/gheist-13500-secret-dumping-workflows-planted-with-stolen-github-tokens-audit-yours-in-5-minutes-299f
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fztfygwgyki6eaaqty4nq.png
image_alt: "Gheist : 13 500 workflows de vol de secrets plantés avec des tokens GitHub volés — audite les tiens en 5 minutes"
---

> Pendant que tout le monde regardait LiteLLM, une campagne plus discrète passait cinq semaines à faire pire : prendre des tokens GitHub volés et committer un **workflow d'exfiltration de secrets dans chaque repository accessible** — **13 500 branches plantées sur 850+ comptes compromis**, projets perso et **repos privés d'entreprise** compris. Wiz a publié l'autopsie complète hier. La campagne s'appelle Gheist, elle vide tes secrets d'org, tes credentials cloud et — la ligne qui m'a fait écrire cet article — elle chasse spécifiquement **les clés des fournisseurs d'IA : Anthropic, Hugging Face, Groq, NVIDIA**. Les clés de tes agents, sorties directement de ton CI.

Cet article, c'est la mécanique et l'audit. Le check complet tourne en cinq minutes avec `gh`, ce soir, sur ton compte et tes orgs.

## L'attaque, en quatre mouvements

L'outillage de Gheist prend un token volé (venu de logs d'infostealer et d'incidents supply-chain — la même famille qui a frappé Trivy en mars), énumère chaque repo accessible, et plante une branche `ci-sync-XXXXXX` contenant un workflow, commité `ci: sync config`, non signé. Le workflow fait deux lignes bêtes : dumper `env` et `toJSON(secrets)`, **encodés en base32**, imprimés dans le log du workflow. Puis l'outil récupère le log via l'API GitHub et supprime le run.

Quatre détails le rendent malin, et les quatre méritent d'être internalisés :

1. **Le base32 bat le masquage.** GitHub ne masque les valeurs de secrets dans les logs que si elles apparaissent *verbatim*. Encode-les et le masquage ne voit rien. Ta `$SECRET` s'imprime tranquillement pour l'attaquant.
2. **`permissions: {}` ne protège rien ici.** Ça limite le GITHUB_TOKEN auto-généré — pas le contexte `secrets`. La moitié des conseils de hardening d'internet répondent à une autre attaque.
3. **La matrice d'environnements.** L'outil B liste les deployment environments du repo, pour que les secrets scopés par environnement — souvent la prod, souvent les joyaux — s'impriment aussi.
4. **Zéro C2, nulle part.** Les secrets sortent par l'API de GitHub elle-même, depuis les IP de GitHub, authentifiés avec un token que TU as émis. Il n'y a aucun domaine attaquant à bloquer, aucun hôte d'exfiltration à alerter. Le canal, c'est la plateforme.

Sur les runners self-hosted, le payload allait plus loin — recherche de 31 formats de tokens (clés privées, fichiers `.env`, state Terraform, `/proc/*/environ`, sockets Docker, tokens Kubernetes) et les clés des fournisseurs d'IA spécifiquement. Wiz note que cette variante est buguée — mauvais chemins de runner, regex cassée, pas de collecte GCP/Azure — ce qui est pire : la campagne est un produit en itération active, qui shippe des fonctionnalités.

## L'asymétrie public/privé

Le fait le plus intéressant de l'autopsie : **les repos publics ont été largement sauvés par un garde-fou discret de GitHub**. Depuis le 28 juillet, les runs de workflow de premiers contributeurs dans les repos publics restent en `action_required` en attendant l'approbation d'un collaborateur — et chaque run Gheist public vérifié par Wiz y était, payload jamais exécuté.

Ce garde-fou **ne s'applique pas aux repos privés ni à GitHub Enterprise Server**. Là, les workflows ont tourné, les secrets ont été vidés, et Wiz a prouvé l'assumption de rôles AWS consécutive via CloudTrail. Le garde-fou que tu n'as jamais configuré a protégé ton open source ; rien n'a protégé le privé, qui est là où vivent les secrets.

Deux autres trouvailles qui valent le détour : `permissions: {}` sur le workflow malveillant était mis *par l'attaquant* — cosmétique, puisque les secrets s'en fichent — et environ deux tiers des comptes impliqués ont depuis disparu de GitHub, signe que la réponse est en cours pendant que la campagne continuait d'évoluer au 24 octobre.

## L'audit — cinq minutes, ce soir

Le radar : le message de commit est cherchable dans l'historique public, et c'est bruyant (des `sync config` légitimes partout), donc traite-le comme un générateur de pistes, pas comme un verdict :

```bash
gh api 'search/commits?q="ci: sync config"' --jq '.total_count'
# → 321 hits en ce moment. La plupart sont des scripts de sync innocents. Ton travail, c'est le check des branches ci-dessous.
```

L'audit réel — branches plantées sur ton compte (boucle sur tes repos, grep du pattern de branche) :

```bash
gh repo list --limit 200 --json nameWithOwner --jq '.[].nameWithOwner' | while read r; do
  gh api "repos/$r/branches" --paginate --jq '.[].name' 2>/dev/null | grep -E '^ci-sync-[0-9a-z]{6}$' && echo "  ↑ HIT dans $r"
done
```

Pour les **organisations** (réservé aux owners — l'API audit-log n'existe pas pour les comptes persos ; le journal de sécurité de l'interface web est le repli perso) :

```bash
# Les runs de workflow supprimés dans la minute suivant leur fin — la signature de nettoyage de Gheist
gh api 'orgs/TONORG/audit-log?include=all&phrase=workflow_run' \
  --jq '.[] | select(.action=="workflow_run.deleted")'
# Le user agent de l'outil
gh api 'orgs/TONORG/audit-log?include=all' --jq '.[] | select(.user_agent=="gheist")'
```

Et la **chasse côté cloud qui marche même sans les logs GitHub** — la meilleure astuce de Wiz : les assumptions de rôles OIDC dont le subject contient `ci-sync-` (le subject OIDC de GitHub inclut la ref, donc le nom de la branche plantée voyage jusqu'à ton CloudTrail) :

```bash
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRoleWithWebIdentity \
  --start-time 2026-09-15 --max-results 20 | grep -i 'ci-sync'
```

Si quelque chose sort : **rotate chaque secret que le repo pouvait voir** — supprimer les runs ne les dé-vident pas — révoque les tokens qui ont pushé, et checke les machines des propriétaires de tokens pour des infostealers, parce que c'est de là qu'ils venaient.

## Se blinder pour la prochaine

De la liste de Wiz, classé par coût : exiger des **reviewers sur les secrets scopés par environnement** (tue la matrice d'environnements) ; scopier les trust policies OIDC aux **branches protégées uniquement** (tue l'assumption de rôle `ci-sync-*`) ; préférer les **GitHub Apps ou des tokens fine-grained à durée courte** plutôt que des PAT classiques (réduit ce qu'un seul token volé atteint) ; faire tourner les runners self-hosted **éphémèrement, sans socket Docker, sans metadata non restreinte** (tue le pivot hôte). Et n'approuve jamais un run `sync-check` en attente dans `action_required` — c'est la porte d'entrée du piège.

## TL;DR

Gheist = tokens volés + un workflow de deux lignes + base32 + GitHub-comme-C2, à l'échelle de 13 500 branches. Les repos publics ont eu de la chance via le hold premiers-contributeurs ; les repos privés ont payé. L'audit fait cinq minutes de `gh` et une requête CloudTrail — et si tu fais tourner des agents IA dans ton CI, la liste de courses de la campagne nomme littéralement ton fournisseur. Checke ce soir.

Sources : [Wiz — Gheist : attempted scaled abuse of stolen GitHub tokens](https://www.wiz.io/blog/gheist-attempted-scaled-abuse-of-stolen-github-tokens-stumbles) · [CISA alerts](https://www.cisa.gov/news-events) · audit commit-search via `gh api` (commandes ci-dessus, vérifiées en live)
