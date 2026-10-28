---
titre: "Chaque page de ce blog est scellée — voici comment le vérifier vous-même"
titre_en: "Every page of this blog is sealed — here is how to verify it yourself"
date: 2026-10-31
themes: preuve, crypto
resume: "101 fichiers, un SHA-256 par fichier, une chaîne, une tête signée Ed25519, un manifest public. La vérification out-of-band tient en 5 lignes de Python stdlib — et le même sceau tourne dans votre navigateur."
resume_en: "101 files, one SHA-256 per file, a chain, an Ed25519-signed head, a public manifest. Out-of-band verification fits in 5 lines of stdlib Python — and the same seal runs in your browser."
source: https://github.com/slabbdev/blog
---

Un blog statique, c'est pratique : pas de base de données, pas de tracking, pas de panne de serveur d'app. Mais ça reste un serveur qui répond — et quiconque contrôle le serveur (l'hébergeur, le CDN, le compte du repo) peut modifier une page silencieusement. Personne ne le remarquerait. C'est le problème que le sceau de ce blog attaque : **prouver que ce que vous téléchargez est exactement ce qui a été publié au dernier déploiement — sans vous demander de me croire.**

## La mécanique

À chaque publication, un script ([seal.py](https://github.com/slabbdev/blog/blob/main/tools/seal.py)) fait trois choses :

1. **Il hache chaque fichier** du site en SHA-256 — aujourd'hui **101 fichiers**, un peu moins d'un méga-octet au total.
2. **Il chaîne les hashes** : chaque fichier hache aussi le précédent. Réordonner, retirer ou réécrire une entrie casse tout ce qui suit.
3. **Il signe la tête de la chaîne en Ed25519** — la clé privée ne quitte jamais ma machine, la clé publique est dans le manifest.

Le résultat est un [`manifest.json`](https://blog.slabb.dev/manifest.json) public : la liste des 101 fichiers avec leurs hashes, la tête de chaîne, la signature, la clé publique, et l'empreinte de la racine de confiance — `sha256:64cba499e2568c97`. Le publish refuse de pousser si la vérification échoue, donc une chaîne cassée ne peut pas partir en production.

## Vérifiez en 5 lignes

La vérification out-of-band ([verify.py](https://github.com/slabbdev/blog/blob/main/verify.py), stdlib only, zéro dépendance) :

```python
import json, hashlib, urllib.request
m  = json.load(urllib.request.urlopen("https://blog.slabb.dev/manifest.json"))
f  = m["files"][0]
b  = urllib.request.urlopen("https://blog.slabb.dev/" + f["name"]).read()
print(f["name"], "OK" if hashlib.sha256(b).hexdigest() == f["sha256"] else "MODIFIÉ")
```

Ça vérifie un fichier. Le script complet rechaîne les 101, revérifie la signature Ed25519, et rend son verdict — `INTÈGRE` ou `MODIFIÉ` — sans rien installer. Pointez-le vers n'importe quel miroir : la question « ce miroir sert-il ce qui a été scellé ? » a une réponse binaire.

Et si vous ne voulez pas ouvrir un terminal : le même sceau se vérifie **dans le navigateur** — [l'inspector de noirebox.eu](https://noirebox.eu/tech.html#inspector) fetch le manifest du blog noirebox, recalcule chaque SHA-256 en WebCrypto localement, et laisse même simuler un octet falsifié pour montrer la chaîne casser en direct.

## Ce que ça prouve — et ce que ça ne prouve pas

L'honnêteté est le produit, donc les limites :

- **Ça prouve** : ce que vous téléchargez est byte pour byte ce qui a été scellé au dernier publish. Une page modifiée en transit, sur le CDN, ou dans un miroir est détectable par n'importe qui.
- **Ça ne prouve pas** : que le contenu scellé est *vrai*. Un sceau sur un mensonge est un mensonge scellé.
- **La racine, c'est la clé privée** — sur ma machine. Si elle fuit, n'importe qui peut resceller une version falsifiée. La parade est classique : l'empreinte `sha256:64cba499e2568c97` est publiée hors band (réseaux, profils), donc un rescellage frauduleux se voit à l'empreinte qui change.
- **Le repo reste le juge de paix** : le manifest servi et le manifest du repo peuvent être comparés ; GitHub devient le témoin tiers du dernier état scellé.

C'est exactement la primitive que [NoireBox](https://code.noirebox.eu/) applique aux décisions des agents IA — hash chaîné, signature Ed25519, vérifiable par un tiers sans accès aux systèmes — appliquée ici à un blog. Le site public le plus simple possible, avec la propriété d'intégrité la plus forte possible sans infrastructure supplémentaire : un script Python, une clé, un manifest.

Zéro cookie, zéro tracking — et maintenant, zéro confiance requise.
