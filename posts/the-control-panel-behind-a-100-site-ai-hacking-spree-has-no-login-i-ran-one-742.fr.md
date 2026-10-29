---
titre: "Le panneau de contrôle derrière une vague de piratage IA de 100 sites n'a pas de login. J'en ai fait tourner un."
date: 2026-10-20
themes: securite, agents
resume: "Reuters a regardé une ruée d'agents IA casser 100+ entreprises à cinquante dollars l'intrusion. Le panneau de contrôle open source derrière tout ça, Cairn, ne shippe aucune authentification, j'ai lu le code, puis j'ai fait tourner le panneau chez moi, dents en moins."
source: https://dev.to/slabb/the-control-panel-behind-a-100-site-ai-hacking-spree-has-no-login-i-ran-one-742
image: https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/fv3vcse966huzlbh757r.png
image_alt: "Un blackboard de nœuds facts et intents lumineux, sans aucune porte entre lui et un lecteur extérieur"
---

> La ruée la plus bruyante du mois a visé 1 200 sites pour quelques milliers de dollars de tokens. Son tableau de bord, lui, ne verrouillait rien : pas de login, pas de clé API, rien dans le code. J'ai fait tourner le panneau chez moi pour le vérifier, et pour vous laisser le refaire en quatre commandes.

```text
INFO scheduler.loop dispatched bootstrap project=proj_001 intent=i001 worker=mock-observer-1
INFO tasks.common intent concluded project=proj_001 intent=i001 worker=mock-observer-1 source=bootstrap phase_ms=3000 total_ms=3002
INFO tasks.bootstrap bootstrap completed project=proj_001 intent=i001 worker=mock-observer-1 source=bootstrap from=['f001'] phase_ms=3000 total_ms=3002
INFO scheduler.loop skip project=proj_001 because status=completed
INFO scheduler.loop skip dispatch because no active projects
```

Voilà un essaim d'agents autonomes qui s'amorce tout seul sur mon portable, boucle complète en trois secondes. Le logiciel, c'est [Cairn](https://github.com/oritera/Cairn), le panneau de contrôle open source sous lequel [Reuters raconte](https://www.reuters.com/legal/government/how-one-hacker-used-ai-agents-few-thousand-dollars-break-into-scores-sites-2026-10-19/) qu'a tourné une campagne de piratage qui a percé plus d'une centaine d'entreprises à cinquante dollars l'intrusion environ. Je l'ai fait tourner avec la machinerie offensive débranchée, pas de clé API, pas de Docker, pas un paquet qui sort de la machine, parce que la partie intéressante de cette histoire, ce n'est pas la brèche. C'est que le panneau de contrôle derrière n'a pas de login. Pas un login faible. Aucun login dans le code, nulle part.

## La ruée, observée depuis l'intérieur du panneau

L'histoire, telle que [Reuters l'a racontée le 19 octobre](https://www.reuters.com/legal/government/how-one-hacker-used-ai-agents-few-thousand-dollars-break-into-scores-sites-2026-10-19/) : Snorre Fagerland, principal threat researcher chez NorForge, a passé le début d'octobre à scanner les instances de Cairn exposées par accident, et en a trouvé une vingtaine utilisées pour du maliciel d'activité malveillante, ce qui lui a permis de « quietly peer over the cybercriminals' shoulders », regarder par-dessus l'épaule des cybercriminels pendant qu'ils travaillaient. Le plus prolifique : un hacker sinophone, actif depuis le 25 septembre, braqué sur l'e-commerce américain, canadien, australien et japonais. Tout leur plan de campagne tenait en moins de 100 caractères chinois. Les agents ont fait le reste : plus de 1 200 sites attaqués, plus de 100 entreprises compromises, des intrusions réussies qui prenaient typiquement 23 heures de tâtonnement, pour environ 5 000 $ de tokens sur toute la campagne, environ 50 $ par piratage réussi, sur un mélange de DeepSeek (Chine) et du Claude Code d'Anthropic.

Ce que Fagerland dit avoir trouvé impressionnant n'est pas le volume. Dans un cas, après avoir échoué à trouver une faille dans l'application publique d'une grande entreprise, les agents ont épluché les enregistrements numériques pour cartographier l'infrastructure associée, localisé un panneau de contrôle exposé, repéré une faille subtile dans son traitement des données, et enchaîné des heures d'essais et d'erreurs jusqu'à faire exécuter leurs commandes au serveur. « It's not straightforward to come up with solutions like that », a-t-il dit à Reuters. « It's not script kiddie stuff. » Son résumé de l'état du monde : « It's a new world now. »

Les victimes nommées ressemblent à une liste d'entreprises qui n'ont rien fait d'inhabituel. [Deere a dit](https://ca.finance.yahoo.com/news/exclusive-one-hacker-used-ai-100625294.html) avoir pris les « necessary remediation actions » et n'avoir « no indication that sensitive information was accessed ». SharkNinja dit que le coup a touché un site autonome de support produit, depuis contenu. Cummins dit « investiguer le signalement d'une cyberattaque potentielle sur un site opéré par l'un de nos prestataires ». Reuters n'a pas pu établir si des données avaient été exfiltrées, et deux plus petites entreprises ont reconnu être compromises en plus des trois ci-dessus. Personne dans cette histoire n'a eu besoin de cliquer sur quoi que ce soit.

## Un blackboard, trois primitives, zéro cadenas

Le [README de Cairn](https://github.com/oritera/Cairn) est franc sur l'ambition : « a general-purpose AI state-space search engine, validated first on autonomous penetration testing » (et, détail charmant, « Sometimes misspelled as Carin »). On lui donne un origin et un goal, il cherche un chemin dans un espace d'états inconnu. Le moteur est un blackboard à trois primitives : une **Fact** est une découverte confirmée, écrite au tableau ; une **Intent** est une direction d'exploration déclarée mais pas encore exécutée ; un **Hint** est du jugement humain injecté à n'importe quel moment, absorbé par les agents à leur prochaine lecture. Les workers tournent en boucle OODA, observer tout le graphe, s'orienter, décider des prochaines intents, agir, sans rôles fixes, et les backends supportés sont les CLI Claude Code, Codex et Pi. C'est exactement la forme de la campagne Reuters : des instructions humaines terser, des heures de traversée autonome, un tableau qui se remplit de découvertes.

Voilà la partie que j'ai vérifiée moi-même au lieu de la prendre au fil. La release actuelle, la v0.2.1, shippe son serveur API entier dans un fichier FastAPI de quarante lignes : cinq routers, seize endpoints, et pas un seul ne demande qui appelle. Pas de middleware d'auth. Pas de dépendance d'identifiants. Aucune option de clé API dans tout le paquet serveur. L'API se décrit même toute seule sur `/openapi.json` à quiconque se connecte, j'ai compté les seize routes sur ma propre instance. La formule de Fagerland était « instances involontairement exposées » ; le code explique à quel point c'était involontaire. Un déploiement Cairn qui est joignable est un déploiement Cairn qui est lisible, écrivable, et qui prend des hints d'inconnus. Ma contribution au dossier est étroite mais solide : j'ai lu le code livré, et rien dedans n'aurait arrêté le chercheur. L'exposition était un défaut de déploiement posé sur une plateforme qui n'a jamais rien cadenassé dès le départ.

L'auteur, qui poste sous le pseudo le1xia0, a dit à Reuters que sa plateforme est « an innovative type of multi-agent architecture and was not designed for hacking attacks. If it is used to carry out harmful hacking attacks, that is not my intention. » Les deux moitiés de la phrase sont cohérentes avec le code : c'est un moteur de recherche général, et il se valide sur le pentest parce que les problèmes origin-goal-path, c'est ce qu'est le pentest.

## Septembre avait déjà chiffré ça

Reuters n'est pas le premier instrument à lire ce thermomètre. Le 22 septembre, [l'équipe threat intelligence de Gambit Security](https://gambit.security/blog-posts/autonomous-ai-agents-online-retailers-25-a-company) publiait sa propre reconstruction d'une campagne distincte qui frappait les e-commerçants, bâtie sur le même trio : **Strix** pour la reconnaissance (146 runs contre 138 hôtes, 633 heures de scan en août seul), **Cairn** pour l'intrusion autonome (105 projets d'attaque lancés entre le 10 et le 15 septembre, sur DeepSeek v4.1 Flash), et **Hermes** comme console d'orchestration, mémoire persistante, skills auto-écrites, et une persona sinophone « SOUL - Red Team Operator » chargée de 121 skills, dont 78 liées à l'attaque. L'une de ces skills s'intitulait Database Wipe After Extraction. Chez une victime, un revendeur de vélos, le nettoyage a droppé 180 tables, y compris les backups de la victime.

L'économie de ce rapport est le chiffre qui ne me lâche pas : **25,46 $ de coût marginal moyen par scan complété**, sur 101 scans, de 3,13 $ à 79,31 $, pour une facture de modèles totale estimée entre 12 000 et 18 000 $ sur sept semaines.

| chiffre | valeur | qui l'a mesuré |
|---|---|---|
| sites attaqués | 1 200+ | NorForge, via les instances Cairn exposées |
| entreprises compromises | 100+ | NorForge ; Reuters a identifié Deere, SharkNinja, Cummins |
| temps médian d'une intrusion réussie | ~23 heures | NorForge |
| facture de tokens de la campagne | ~5 000 $ | estimation NorForge |
| coût par succès | ~50 $ | NorForge |
| coût par scan complété (campagne distincte) | 25,46 $ en moyenne, 3,13–79,31 $ | Gambit Security, 101 scans |
| facture de modèles (campagne distincte) | 12–18 k$ sur ~7 semaines | Gambit Security |

Deux firmes de recherche, deux campagnes, zéro donnée partagée, même ordre de grandeur : des dizaines de dollars par brèche. Quand deux instruments indépendants tombent d'accord à ce point, le fait intéressant cesse d'être l'un ou l'autre instrument et devient le prix.

## Le contrepoint : le modèle est le fossé

Avant que ça ne se lise comme « tous les modèles savent faire ça maintenant », il y a un point de correction, et il vient de quelqu'un qui a tenté la version bénigne de bonne foi. Un mainteneur japonais a construit [une étude défensive ouverte de ces outils exacts](https://github.com/w-index-m/ai-agent-attack-defense), règles de détection, outillage de triage, runbook de labo, et a documenté une tentative honnête et ratée de faire tourner l'agent de reconnaissance (Strix) de bout en bout contre son propre labo isolé. Les modèles locaux sur CPU produisaient du JSON d'outils malformé ou des boucles de commandes sans objet. Le tier gratuit de Groq butait sur des caps de tokens par minute qu'aucun choix de modèle n'esquivait. Celui d'OpenRouter passait les appels de test isolés mais 404-ait reproductiblement sur la vraie taille de requête de l'agent. Conclusion : abandonner le scan par agent et livrer un scanner déterministe à la place, qui a immédiatement trouvé ce que l'agent ne trouvait pas.

Mettez ça à côté de ce que tournaient les campagnes qui ont marché : Claude Code comme harnais, DeepSeek v4.1 Flash comme moteur. Pas cher ne veut pas dire jouet. Ça veut dire que la partie chère de l'intrusion a déménagé dans la facture de modèles, et les campagnes qui ont marché l'ont tous payée. Le fossé n'est plus la compétence d'exploitation. C'est le modèle derrière la boucle, phrase étrange à écrire, et les chiffres ci-dessus expliquent pourquoi c'est la bonne.

## Le panneau chez vous, dents en moins

Vous pouvez voir cette architecture travailler sur votre propre machine en quatre commandes, la moitié offensive débranchée. Cairn shippe un type de worker « mock » qui lance des dés pondérés au lieu d'appeler un modèle, même tableau, même boucle, même protocole, zéro clé API, zéro réseau. Voici la configuration exacte de ma run, à coller dans `cairn-mock.yaml` :

```yaml
server: "http://127.0.0.1:8000"

runtime:
  execution: local          # workers en process hôtes, le défaut container exige Docker
  worker_healthcheck: disabled
  max_workers: 2
  max_running_projects: 2
  max_project_workers: 2
  interval: 3
  healthcheck_timeout: 5
  prompt_group: "mock"

tasks:
  bootstrap: {timeout: 9, conclude_timeout: 5}
  reason: {timeout: 5, max_intents: 3}
  explore: {timeout: 9, conclude_timeout: 5}

local:
  completed_action: keep

workers:
  - name: "mock-observer-1"
    type: "mock"
    task_types: [reason, explore, bootstrap]
    max_running: 1
    priority: 0
    env:
      MOCK_HEALTHCHECK: '{"delay":[0,1],"outcomes":{"ok":1.0}}'
      MOCK_BOOTSTRAP: '{"delay":[1,3],"outcomes":{"complete":1.0,"fact":0.0}}'
      MOCK_REASON: '{"delay":[1,3],"outcomes":{"intent":0.7,"noop":0.3}}'
      MOCK_EXPLORE_EXECUTE: '{"delay":[1,3],"outcomes":{"fact":1.0}}'
      MOCK_EXPLORE_CONCLUDE: '{"delay":[1,2],"outcomes":{"fact":1.0}}'
```

```bash
git clone https://github.com/oritera/Cairn && cd Cairn
python3 -m venv .venv && .venv/bin/pip install -e ./cairn
.venv/bin/cairn serve --host 127.0.0.1 --port 8000        # terminal 1
.venv/bin/cairn dispatch --config cairn-mock.yaml          # terminal 2
```

Semez le tableau, notez que l'API veut maintenant un `title`, ce que les vieux runbooks communautaires ne mentionnent pas :

```bash
curl -s -X POST http://127.0.0.1:8000/projects -H 'Content-Type: application/json' \
  -d '{"title":"mock lab","origin":"target http://10.77.0.10 (isolated lab, unreachable)","goal":"get a shell"}'
```

La réponse, verbatim de ma run :

```text
{"project":{"id":"proj_001","title":"mock lab","status":"active","bootstrap_enabled":true,"created_at":"2026-10-20T16:41:50Z","reason":null},"facts":[{"id":"origin","description":"target http://10.77.0.10 (isolated lab, unreachable)"},{"id":"goal","description":"get a shell"}],"intents":[],"hints":[]}
```

Attendez une quarantaine de secondes, puis relisez le tableau avec un simple `curl` non authentifié, ce qui est, encore une fois, tout le propos :

```json
{"project": {"id": "proj_001", "status": "completed"},
 "facts": [
  {"id": "origin", "description": "target http://10.77.0.10 (isolated lab, unreachable)"},
  {"id": "goal", "description": "get a shell"},
  {"id": "f001", "description": "mock fact for bootstrap"}],
 "intents": [
  {"id": "i001", "description": "bootstrap"},
  {"id": "i002", "description": "mock bootstrap complete from fact"}],
 "hints": []}
```

Deux notes pratiques, faites pour vous éviter de marcher sur les deux râteliers. Le mode de dispatch par défaut lance un conteneur Docker par projet, et l'image worker publiée n'a pas de manifeste ARM64, sur une machine Apple Silicon, le défaut échoue, et `execution: local` dans la config ci-dessus est le passage. Et les vraies intrusions chronométrées par Fagerland prenaient en moyenne 23 heures ; la mienne a fini en trois secondes, parce que l'enjeu était des dés. La vitesse n'est pas le propos. La forme l'est : même tableau, même boucle, même protocole, et la même absence complète de porte entre le tableau et quiconque trouve le port.

## Le grade où ça se pose

[L'échelle d'autorité](https://dev.to/slabb/the-authority-ladder-five-rungs-down-four-premises-standing-4p5f) que cette série arpente dit qu'une preuve qui vit sur une infrastructure que vous ne contrôlez pas est une étiquette d'appelant. Un panneau de contrôle d'agents exposé, c'est cette défaillance inversée et braquée vers vous : les découvertes, les plans et les hints de vos agents, posés sur un tableau qui se décrit à quiconque se connecte. [Le post de la semaine dernière parlait d'un contournement qui a été journalisé](https://dev.to/slabb/the-quiz-hook-is-a-level-1-control-and-the-bypass-is-logged-43f) ; celui-ci parle d'une porte qui n'a jamais été posée. Les deux receipts viennent du même endroit, lire ce que le logiciel fait vraiment au lieu de ce que le déploiement suppose.

## Ce qu'il faut piquer

- **Auditez vos propres panneaux avec un curl.** Depuis l'extérieur du segment réseau où un panneau de contrôle d'agents est censé vivre, demandez `GET /openapi.json`. Une réponse veut dire que le panneau se décrit, ses routes et son modèle de données, à quiconque demande. Bindez sur loopback, ou cadenassez derrière le même VPN que tout ce que vous détesteriez perdre, ne comptez pas sur le logiciel pour shipper une porte.
- **Le pack de détection existe déjà.** L'[étude défensive japonaise](https://github.com/w-index-m/ai-agent-attack-defense) shippe des règles Sigma, Falco et Datadog (R1–R8) mappées sur MITRE ATT&CK/ATLAS et l'OWASP Top 10 for LLM, écrites spécifiquement pour les chaînes d'attaque par agents, recon, intrusion, orchestration. Gratuit, et écrit par quelqu'un qui a vérifié son propre travail contre de l'outillage réel.
- **L'egress control sur les workers est la vraie couche de prévention.** Le rapport Gambit et toutes les listes de mitigations de ce space convergent là : un agent qui ne peut joindre que les destinations que vous allowez ne peut pas cartographier votre infrastructure associée à 3 h du matin. Divulgation, parce que série receipts : NorForge, l'employeur de Fagerland, vend de l'egress control pour agents, et son rapport complet n'était pas public quand ce post a été écrit. La découverte tient sur le code ; les incitations sont énoncées pour que vous pondériez.
- **Piquez la primitive Hint pour vos propres outils.** Le seul endroit où un humain rejoint la boucle de Cairn, le jugement atterrit sur le tableau avec tout le reste, versionné, horodaté, absorbé en aval. Les dashboards montrent ce qui se passe ; les tableaux l'enregistrent.

## Deux limites honnêtes

**Le mock prouve le panneau, pas la ruée.** Ma run a généré des facts avec des dés ; aucune attaque n'a été exécutée contre aucune cible, point. Les 1 200 sites attaqués, les 100+ compromissions, la médiane de 23 heures et les 5 000 $ de tokens sont les estimations du chercheur à partir de la télémétrie observée sur des instances exposées, pas des pièces de tribunal, et Reuters n'a pas pu établir si des données ont été exfiltrées. Les déclarations des entreprises nommées ci-dessus sont l'autre moitié de cette incertitude, et elles appartiennent à chaque récit.

**Ma découverte du no-auth est une lecture de code, pas un scan.** J'ai lu Cairn v0.2.1 tel que publié sur GitHub et vérifié que le paquet serveur ne shippe aucune authentification ; je n'ai sondé le déploiement de personne. La release que j'ai lue était l'état du dépôt à son dernier push, le 7 septembre, trois jours avant la fenêtre d'attaque du 10–15 septembre documentée par Gambit, ce qui coupe dans les deux sens : c'est presque certainement ce qui a tourné sur le terrain, et un dépôt peut shipper une couche d'auth d'un jour à l'autre, donc vérifiez le code avant de citer qui que ce soit, moi inclus. La table d'économie mêle deux campagnes indépendantes, outillage et victimes différents ; elles concordent en ordre de grandeur, pas en identité, et je les ai gardées sur des lignes séparées exactement pour ça.

## À vous de jouer

Lancez les quatre commandes, semez un projet, laissez la boucle mock mâcher une minute. Puis postez deux chiffres en commentaire : votre nombre de facts après soixante secondes de dispatch, les dés sont pondérés, pas scriptés, donc votre tableau ne sera pas le mien, et la divergence est la boucle qui marche comme prévu, et le nombre de panneaux de contrôle d'agents sur votre propre réseau qui répondent `/openapi.json` depuis l'extérieur de leur segment. Ma paire : 3 facts, 1 panneau sur loopback où je l'ai mis. Le premier chiffre vous montre à quoi ressemble la traversée autonome quand rien n'est en jeu. Le second vous dit si quelque chose qui vous appartient garde ses découvertes sur un tableau déverrouillé.

---

*Sources : [Reuters, How one hacker used AI agents and a few thousand dollars to break into scores of sites](https://www.reuters.com/legal/government/how-one-hacker-used-ai-agents-few-thousand-dollars-break-into-scores-sites-2026-10-19/) (19/10/2026, Raphael Satter), porté verbatim par [Yahoo Finance](https://ca.finance.yahoo.com/news/exclusive-one-hacker-used-ai-100625294.html). Rapports primaires : [Gambit Security, AI Agents Are Hacking Online Retailers for $25 a Company](https://gambit.security/blog-posts/autonomous-ai-agents-online-retailers-25-a-company) (22/09/2026, Eyal Sela) ; [w-index-m/ai-agent-attack-defense](https://github.com/w-index-m/ai-agent-attack-defense). Plateforme : [oritera/Cairn](https://github.com/oritera/Cairn) (AGPL-3.0, v0.2.1). Le cadre suit les posts [authority ladder](https://dev.to/slabb/the-authority-ladder-five-rungs-down-four-premises-standing-4p5f) et [quiz-hook](https://dev.to/slabb/the-quiz-hook-is-a-level-1-control-and-the-bypass-is-logged-43f). Publié d'abord sur [dev.to](https://dev.to/slabb/the-control-panel-behind-a-100-site-ai-hacking-spree-has-no-login-i-ran-one-742).*
