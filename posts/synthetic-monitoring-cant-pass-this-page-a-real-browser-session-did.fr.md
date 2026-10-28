---
titre: "Le monitoring synthétique ne passe pas cette page — une vraie session navigateur l'a faite en 6 secondes"
titre_en: "Synthetic monitoring can't pass this page — a real browser session did it in 6 seconds"
date: 2026-10-28
themes: web, agents
resume: "Le même check, deux moniteurs : HTTP naïf reçoit 403 cf-mitigated, une session navette passe le challenge Cloudflare et asserte 1 358 cartes produit. La preuve est publique et datée."
resume_en: "Same check, two monitors: naive HTTP gets a 403 cf-mitigated, a real navette session clears the Cloudflare challenge and asserts 1,358 product cards. The evidence is public and dated."
source: https://github.com/slabbdev/navette-monitor
image: https://raw.githubusercontent.com/slabbdev/navette-monitor/main/assets/vinted-check-pass.png
image_alt: "Le check navette-monitor qui passe : challenge Cloudflare clairé, 1 358 cartes produit assertées"
---

Votre monitoring synthétique tourne-t-il encore quelque part d'utile ? La plupart des stacks — Checkly, les checks navigateur des APM, les cron Playwright — exécutent un Chromium headless depuis une IP de datacenter. C'est précisément la signature que les murs bot (Cloudflare, DataDome) sont conçus pour arrêter. Le résultat : vos checks « passent » sur vos propres pages et échouent sur le web réel — ou pire, ils ne surveillent que des pages qui ne sont jamais protégées.

Hier soir, j'ai fait tourner le même check avec deux moniteurs contre `vinted.fr/catalog?search_text=nike` — une marketplace française derrière Cloudflare. Ce n'est pas un labo fabriqué : c'est un site réel, un mur réel, une capture datée.

## Le check, deux fins

**Moniteur 1 — HTTP naïf** (curl-like, comme la majorité des checks « uptime ») :

```
HTTP/2 403
cf-mitigated: challenge
```

Refusé. Pas une erreur passagère : le mur a classé la requête comme bot et a servi le challenge. Un moniteur HTTP ne peut pas le résoudre — il ne parle pas TLS/JA3 comme un navigateur, ne charge pas le JavaScript du challenge, ne prouve rien.

**Moniteur 2 — une session navette** (le moteur WebKit du système, une vraie session isolée) :

```
challenge résolu en ~6 s
page catalogue chargée
1 358 cartes produit assertées
```

Même IP de départ, même cible. La différence n'est pas un user-agent — c'est un vrai moteur de rendu, un vrai cycle challenge/réponse, une vraie session. Le check ne se contente pas de « charger » : il **asserte le contenu métier** (1 358 cartes), parce qu'un check qui ne vérifie pas le contenu ne détecte pas une page d'erreur soft servie avec un 200.

## Pourquoi « headless depuis un datacenter » est mort par design

Les anti-bots ne cherchent plus à distinguer humain et robot de façon parfaite. Ils scorrent un faisceau : empreinte TLS, headers, comportement, réputation d'IP. Un Chromium headless depuis une IP de datacenter coche toutes les cases « automatisé » d'un coup. Ajouter des flags d'automatisation en moins, des proxys résidentiels, des patchs stealth — c'est une course perdue d'avance, et chaque couche rend votre monitor moins représentatif de vos vrais utilisateurs.

La session navette prend le chemin inverse : c'est le navigateur de la machine, avec son moteur système (WebKit sur macOS, WebKitGTK ailleurs), ses sessions isolées, ses cookies dans le trousseau système — piloté par une API HTTP JSON toute simple. Pas de SDK, pas de flags. Ce n'est pas de la discrétion : c'est de l'authenticité structurelle.

## Le repo, la preuve, la reprise

Tout est public : [slabbdev/navette-monitor](https://github.com/slabbdev/navette-monitor). Le check complet fait ~40 lignes de bash (`check.sh [url]`), la capture du run passe est dans le repo, et la [landing](https://slabbdev.github.io/navette-monitor/) affiche l'évidence. Rejouez-le chez vous : un daemon navette sur le port local, et le script fait le reste — les deux moniteurs, le verdict, la capture.

Les limites, dites franchement : c'est **un** site, capturé **une** fois, le 27 octobre 2026 à 18:12 UTC. Les murs évoluent, les heuristiques changent de bord. Un monitor qui passe aujourd'hui n'est pas un droit acquis — c'est exactement pour ça qu'il faut un monitor qui ressemble à vos utilisateurs, pas un qui triche mieux. Et je n'ai aucun lien avec Checkly, Cloudflare, DataDome ou Vinted : le titre nombe le marché, la preuve est reproductible.

## Ce que ça change

Si votre monitoring synthétique échoue sur les pages que vos utilisateurs voient réellement, vous ne surveillez pas votre produit — vous surveillez votre capacité à vous surveiller. Un check qui passe les mêmes murs que vos utilisateurs vous rend trois choses : des alertes qui veulent dire quelque chose, des métriques de contenu métier (pas juste des codes HTTP), et une base honnête pour parler de SLA.

La flotte arrive aussi : [starflotte](https://github.com/slabbdev/starflotte) fait tourner vingt navettes en parallèle sur les runners gratuits de GitHub Actions — le sujet du prochain article.
