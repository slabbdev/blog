---
titre: "L'UE a vraiment interdit l'« eco-friendly », mais pas tout à fait comme on te l'a raconté"
date: 2026-10-22
themes: conformite, web
resume: "Depuis le 27 septembre, les allégations vertes génériques sont interdites dans toute l'UE. La version virale s'est trompée sur la forme de l'interdiction, voici ce qui est vraiment en vigueur, les trois interdictions dures, ce qui reste légal, et un script d'audit de 15 lignes pour tes landing pages."
source: https://eur-lex.europa.eu/eli/dir/2024/825/oj
image: https://blog.slabb.dev/img/eu-greenwashing-2024-825.png
image_alt: "L'UE a vraiment interdit l'eco-friendly, Directive (UE) 2024/825, en vigueur le 27 septembre 2026 : allégations génériques interdites et audit de landing page"
---

> Oui, c'est réel : depuis le **27 septembre 2026**, le marketing « eco-friendly », « green », « climat neutre » ou « naturel » est interdit dans toute l'UE, sauf preuve à l'appui. Non, ce n'est pas tout à fait ce que disait le post viral : ce n'est pas une liste de mots interdits, ton site ne se fait pas « retirer », et l'ensemble s'applique pays par pays. Voici ce qui est vraiment en vigueur, ce qui reste légal, et un script pour auditer tes propres landing pages en une minute.

L'article qui a tourné la semaine dernière (avec son « checker gratuit » branché sur un pack à 29 $ en bas de page) avait les bons titres et la mauvaise mécanique. La mécanique, c'est ce qui fait les amendes. On parle de la [directive (UE) 2024/825](https://eur-lex.europa.eu/eli/dir/2024/825/oj), *Empowering Consumers for the Green Transition*, que les États membres devaient transposer et appliquer à partir du 27 septembre 2026.

## Les trois interdictions dures

**1. Les allégations environnementales génériques, sauf preuve d'une performance environnementale excellente reconnue.** Le considérant de la directive liste elle-même les coupables : *« environmentally friendly », « eco-friendly », « green », « natural », « biodegradable », « climate friendly », « sustainable »*. Un adjectif générique sans rien derrière est désormais une pratique commerciale déloyale, partout : landing page, tunnel d'achat, emails, pubs, et packaging.

**2. Les allégations basées sur la compensation, interdites purement et simplement.** « Carbon neutral », « climat neutre », « CO₂ compensé » : si la neutralité vient de la compensation plutôt que du cycle de vie du produit lui-même, aucune formulation ne répare. On retire. Celle-là n'a pas de contournement, ce qui surprend les marketeurs qui croyaient tout négociable avec une meilleure note de bas de page.

**3. Les labels de durabilité auto-déclarés.** Ton badge « eco-score » maison sans schéma de certification derrière est dehors. Les labels doivent reposer sur un schéma de certification, établi par des autorités publiques ou des organismes privés, et être plus accessibles qu'un labyrinthe de QR codes.

Plus une conditionnelle : **les allégations de performance future** (« net zéro en 2030 ») ne sont permises qu'avec un plan de mise en œuvre vérifiable, appuyé par une vérification par un tiers. Les promesses floues sont traitées comme ce qu'elles sont : du greenwashing.

## Ce qui reste légal, la partie ratée par la version virale

Ce n'est pas une liste de mots interdits. L'interdiction frappe **les allégations génériques sans preuve** ; une allégation spécifique et vérifiable n'est pas seulement légale, c'est le remplacement voulu : *« fabriqué en aluminium recyclé à 80 %, certifié X »*, c'est très bien. *« Durable »*, non, sauf si le dossier de certification existe déjà de ton côté. Le test n'est pas le dictionnaire, c'est le dossier de preuves.

Et la réalité de l'enforcement : ça passe par les **autorités nationales de protection du consommateur** dans le cadre des pratiques commerciales déloyales, amendes et injonctions par pays, pas une machine européenne de retrait de pages. Pas de période de grâce au jour J, mais pas de robot qui crawlerait le web non plus ; ton exposition commence par une plainte ou un contrôle. Note pour les lecteurs français : la loi Climat interdisait déjà les allégations « neutre en carbone » par compensation depuis 2023, 2024/825 généralise le régime aux 27 États membres.

## Audite tes landing pages en une minute

Le « checker gratuit » du pack à 29 $ est, pour l'essentiel, un grep. Le voici, gratuit et à toi :

```python
# eco_audit.py, signale les allégations vertes candidates sur une page
import re, sys, urllib.request

GENERIC = [  # interdit SAUF preuve d'une performance excellente reconnue
    "eco-friendly", "ecofriendly", "environmentally friendly", "green",
    "sustainable", "climate friendly", "climate-friendly", "natural",
    "biodegradable", "planet-friendly",
]
OFFSETS = [  # interdit purement et simplement si basé sur la compensation
    "carbon neutral", "carbon-neutral", "climate neutral", "climate-neutral",
    "co2 neutral", "net zero", "net-zero", "co2 compensated",
]

text = re.sub(r"<[^>]+>", " ", urllib.request.urlopen(sys.argv[1]).read().decode("utf-8", "ignore").lower())
for w in OFFSETS:
    if w in text:
        print(f"COMPENSATION  '{w}'   → interdit d'office : retirer ou baser sur ton propre cycle de vie")
for w in GENERIC:
    if w in text:
        print(f"GÉNÉRIQUE     '{w}'   → interdit SAUF si le dossier de certification existe : sois spécifique")
```

Run réel contre une page qui restera anonyme :

```text
$ python3 eco_audit.py https://exemple-marque.example/
COMPENSATION  'carbon neutral'   → interdit d'office : retirer ou baser sur ton propre cycle de vie
GÉNÉRIQUE     'sustainable'      → interdit SAUF si le dossier de certification existe : sois spécifique
GÉNÉRIQUE     'natural'          → interdit SAUF si le dossier de certification existe : sois spécifique
```

Limites honnêtes du script : un grep trouve des **candidates**, pas des violations, un « natural » dans un extrait de presse cité ou un slug d'URL n'est pas une allégation, et décider si ton dossier de preuves couvre la formulation est une question juridique, pas une regex. Traite la sortie comme du triage : chaque ligne est une conversation avec celui qui possède le copy, pas un auto-fix. Le pattern de correction, lui, est toujours le même et c'est celui que pousse la directive : **remplace l'adjectif par le chiffre et la source**, « aluminium recyclé à 80 % », « −71 % de CO₂ par unité vs base 2023 (méthodologie liée) ». Le spécifique bat le vert, à chaque fois.

Capture ce que tu changes et quand. Si une autorité nationale te demande un jour, un diff daté de ton propre site est le dossier de bonne foi le moins cher que tu produiras jamais.

## TL;DR

L'interdiction est réelle et en vigueur depuis le 27 septembre 2026 : pas d'allégation verte générique sans preuve, pas de neutralité par compensation, pas de label maison, les promesses exigent des plans vérifiables. Ce qui n'est pas arrivé : une liste noire de mots ni un régime de retrait de pages. Ta landing page est ton exposition, lance l'audit, réécris les adjectifs en chiffres, et garde le diff.

Sources : [Directive (UE) 2024/825 (EUR-Lex)](https://eur-lex.europa.eu/eli/dir/2024/825/oj) · [FAQ de la Commission européenne (PDF)](https://commission.europa.eu/document/download/3c257883-bb2a-4dd9-a6dc-501d587bb34f_en?filename=faq-empowerting-consumers-gtd.pdf) · [Guide pratique Ecoclaim](https://www.ecoclaim.eu/green-claims-directive)
