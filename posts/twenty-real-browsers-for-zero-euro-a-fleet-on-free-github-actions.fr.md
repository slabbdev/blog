---
titre: "Vingt vrais navigateurs pour 0 € — une flotte sur les runners gratuits de GitHub Actions"
titre_en: "Twenty real browsers for $0 — a fleet on free GitHub Actions runners"
date: 2026-10-29
themes: devops, agents
resume: "Une issue labelisée mission déclenche 20 navettes en parallèle sur les runners gratuits — le cap exact du free plan. Mission réelle mesurée : 43 secondes de bout en bout, rapport agrégé sur l'issue."
resume_en: "A mission-labelled issue triggers 20 parallel navettes on free runners — exactly the free-plan cap. A real measured mission: 43 seconds end to end, one aggregated report back on the issue."
source: https://github.com/slabbdev/starflotte
---

Une flotte de navigateurs réels, pilotables à la demande, pour zéro euro ? La réponse était dans le plan gratuit de GitHub Actions tout du long : 20 jobs concurrents, c'est le cap exact du free plan — et sur un repo public, les minutes sont gratuites. [starflotte](https://github.com/slabbdev/starflotte) transforme ce plafond en produit : vous ouvrez une issue, vingt scouts démarrent en parallèle, chacun navigue une cible dans un vrai moteur, et un job d'agrégation reposte un rapport unique sur l'issue.

## Comment on lance une mission

1. Ouvrez une issue. Le corps est la mission : des URLs, une par ligne (les 20 premières sont prises).
2. Posez le label `mission`. La flotte décolle.

Ou en smoke test depuis l'onglet Actions : `workflow_dispatch` avec des URLs brutes — le rapport atterrit dans le summary du run.

## Ce que fait chaque scout

Le scout *k* prend la cible *k*. Il démarre l'image multi-arch `ghcr.io/slabbdev/navette` (WebKitGTK sous Xvfb), pilote le daemon par son API HTTP, et classe le résultat :

- **OK** — page chargée, titre et extraction markdown capturés ;
- **WALL** — un mur anti-bot a été détecté (captcha, DataDome, Cloudflare). **Aucun contournement n'est jamais tenté : le mur est le résultat** ;
- **ERROR** — la navigation a échoué.

Chaque scout upload un artifact (`scout-N`) avec sa capture, l'extraction complète et un `result-N.json` machine. Le job de synthèse télécharge tout et poste **un** tableau sur l'issue.

Les missions peuvent aussi *faire* : un bloc JSON dans l'issue donne à chaque scout des `steps` ordonnés (clic, saisie, scroll, evaluate — tout ce que l'API navette accepte) et une expression `extract` dont le résultat remonte dans le rapport. Le README montre l'exemple complet : chercher un whois RIPE, cliquer, attendre, extraire.

## Mission réelle, chiffres réels

Hier à 16:03 UTC, smoke test : 4 cibles (example.com, blog.slabb.dev, noirebox.eu, rfc-editor.org). Résultat mesuré :

- **43 secondes** de bout en bout, queue comprise — 21 jobs au total (20 scouts + synthèse) ;
- les scouts actifs ont navigué leur cible en **~18 secondes** chacun, y compris le boot du conteneur ;
- verdicts : 4 × OK, 16 scouts IDLE (plus de scouts que de cibles — ils se déclarent inactifs au lieu de brûler des minutes) ;
- coût : 0 €. Minutes gratuites, repo public.

## Pourquoi c'est honnête

Les limites sont dans le README, pas cachées : les runners sortent par des IP Azure de datacenter — les sites derrière DataDome/Cloudflare mureront la plupart des runs (Leboncoin, Vinted…). C'est une **fonctionnalité** : l'issue documente le mur, elle ne le fraude pas. Le cron des runs programmés est approximatif ; les workflows se désactivent après 60 jours d'inactivité ; tout est éphémère — pas de cookies, pas de sessions, pas d'état entre les runs.

Et les politiques tiennent en deux lignes : pages publiques en lecture seule, pas de logins, pas de création de comptes, pas d'inflation de métriques. Un captcha est un résultat, pas un problème à résoudre.

## Ce que ça débloque

Pour les agents IA, la question n'est plus « est-ce que mon fetch passe » mais « qu'est-ce qu'un vrai navigateur voit, depuis un datacenter, à l'instant T, en parallèle sur 20 cibles » — avec la preuve (captures, extractions) attachée à l'issue pour toujours. Monitoring de flotte, veille, vérification de déploiements, cartographie de murs : l'issue devient le runbook, le rapport devient la preuve.

La brique en dessous — [navette](https://github.com/slabbdev/navette), le navigateur daemon pour agents — méritait hier son propre article : la preuve qu'une vraie session passe les murs qui arrêtent le monitoring synthétique.
