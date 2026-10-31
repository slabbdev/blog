---
titre: "On a pris le contrôle de comptes ChatGPT : la chaîne postMessage MathLive, et l'audit de 20 lignes pour tes propres listeners"
date: 2026-10-31
themes: securite, web
resume: "Un lien de conversation partagé, une bibliothèque de clavier math qui écoute n'importe quel expéditeur, un iframe qui hérite de chatgpt.com, un bypass CSP via le oembed YouTube, et le token de session : takeover complet, corrigé le 26 octobre. La chaîne étape par étape, plus un audit statique qui a flaggé les quatre listeners vulnérables dans la bibliothèque elle-même."
source: https://dev.to/slabb/we-took-over-chatgpt-accounts-the-mathlive-postmessage-chain-and-the-20-line-audit-for-your-own-442c
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2F6jt6m9jsxg32ygk1yq46.png
image_alt: "On a pris le contrôle de comptes ChatGPT : la chaîne postMessage MathLive et l'audit des listeners"
---

> La divulgation d'hier de [Parameter](https://www.parameter.ai/labs/we-found-a-gap-at-openai) est l'exploit web le plus élégant du mois : **un takeover complet de comptes ChatGPT où la seule action de la victime était d'ouvrir un lien de conversation partagée**. Pas de copier-coller, pas de login, pas de clic dans la version finale : environ 4,5 secondes entre le lien et du JavaScript qui tourne en tant que chatgpt.com, lisant les conversations privées et le token de session. Rapporté le 18 octobre, escaladé de P2 à P1 le 21, corrigé le 26, bounty 5 000 $. La racine est une classe de bug que presque toutes les web apps shippent aujourd'hui, et c'est pourquoi ce post démonte la chaîne étape par étape, plus un audit statique de 100 lignes que j'ai écrit et lancé contre la bibliothèque vulnérable elle-même : **il flague exactement les quatre listeners qui ont rendu ça possible, et ton codebase peut être scanné pareil ce soir.**

## La chaîne, en sept mouvements

La liste d'ingrédients : une conversation partagée (fonctionnalité publique), **MathLive** (la bibliothèque de saisie mathématique que ChatGPT charge quand un message contient un graphe interactif), et le volet HTML Preview qui tourne sur une origine sandboxée séparée.

1. **Le leurre.** L'attaquant partage une conversation contenant un vrai graphe interactif (ce qui fait charger MathLive sur chatgpt.com et installe son listener de messages clavier virtuel) plus un bloc HTML.
2. **La porte sans garde.** Le volet HTML sandboxé envoie des `postMessage`. Le listener de MathLive **ne vérifiait jamais d'où venait le message** (« depuis n'importe quelle adresse web », selon les chercheurs) et acceptait un message `update-setting` portant du HTML contrôlé par l'attaquant dans le champ `layouts[].markup` du clavier, puis un message `show`.
3. **Le sink.** Le layout se rend via `keyboardContainer.innerHTML`, à travers un helper `createHTML` qui était **un wrapper Trusted Types ou une fonction identité, pas un sanitizer**. J'ai vérifié le sink dans le bundle livré : `s.innerHTML = Qi.createHTML(a)` et compagnie, encore présents dans MathLive 0.100.0.
4. **L'héritage d'origine.** Le payload injecté est un `<iframe srcdoc>` **sans attribut sandbox**. Un iframe srcdoc hérite de l'origine du document qui l'embarque : le nouveau frame *est* chatgpt.com.
5. **Le bypass CSP.** La Content-Security-Policy bloquait les scripts inline mais autorisait YouTube. Le payload charge donc `www.youtube.com/oembed?...&callback=<js>;void`, une réponse façon JSONP dont le corps commence par du JavaScript choisi par l'attaquant. La CSP voit une requête vers youtube.com, autorisée. Le navigateur exécute le callback comme un script.
6. **Le token.** En tournant comme chatgpt.com, le code lit les données d'amorçage de session dans la page (`#client-bootstrap`) et obtient l'access token.
7. **Le takeover.** Avec le token : `GET /backend-api/conversations...`, énumérer, lire, exfiltrer via une requête image d'innocente apparence. « N'importe quelle action au nom du compte ChatGPT de la victime. »

Chaque pièce prise séparément est un finding de manuel. La leçon, c'est la composition : un listener laxiste dans une bibliothèque plus un volet sandboxé plus une CSP permissive plus un srcdoc non sandboxé égalent un takeover de compte sur le site IA le plus visité de la planète.

## L'audit : tes listeners, ce soir

La classe de bug a une signature : les handlers `addEventListener('message', ...)` qui ne référencent jamais `event.origin` ni `event.source`. J'ai écrit un scanner statique autour de cette signature (heuristique, compatible bundles minifiés, ~100 lignes) et je l'ai lancé sur les deux choses qui comptent :

```text
$ python3 postmessage_audit.py mathlive-0.100.0.mjs
[RISK] mathlive-0.100.0.mjs:2841 message listener -> NO SENDER CHECK (.origin/.source absent)
[RISK] mathlive-0.100.0.mjs:2931 message listener -> NO SENDER CHECK (.origin/.source absent)
[RISK] mathlive-0.100.0.mjs:2931 message listener -> NO SENDER CHECK (.origin/.source absent)
[RISK] mathlive-0.100.0.mjs:3084 message listener -> NO SENDER CHECK (.origin/.source absent)

$ python3 postmessage_audit.py mathlive-0.111.1.mjs        # release actuelle
(aucun listener message flaggé dans le bundle principal)

$ python3 postmessage_audit.py ~/code/my-app/src/           # à ton tour
```

Le cœur du check (script complet autonome ci-dessous) :

```python
PATTERNS = [re.compile(r"addEventListener\(\s*['\"`]message['\"`]\s*,"),
            re.compile(r"onmessage\s*=")]
ORIGIN_OK = re.compile(r"(?:event|e|ev|msg|evt)\.(?:origin|source)\b")
DANGEROUS = re.compile(r"innerHTML|insertAdjacentHTML|document\.write|outerHTML|\beval\(|new Function\(")
# pour chaque listener : extraire le corps du handler ; flagger si ORIGIN_OK absent,
# et flagger plus fort si un sink DOM vit dans le même handler
```

Limites honnêtes : c'est une heuristique sur le texte source (handlers proxy, frameworks wrappés ou listeners enregistrés dynamiquement peuvent passer entre les mailles), un scan propre n'est pas une preuve, et le gold standard runtime, c'est d'ouvrir DevTools et de regarder quels listeners réagissent à un `postMessage` synthétique venu d'une origine étrangère. Mais le pattern qu'il flague est précisément celui qui a coûté un P1 à OpenAI ce mois-ci, et il attrape la version qui l'avait tout en passant celle qui ne l'a plus.

Le script complet (dépose-le dans un repo ou lance-le en CI sur tes bundles frontend) :

```python
#!/usr/bin/env python3
# postmessage_audit.py <fichier-ou-dossier> [...] : flague les listeners message sans check d'expéditeur
import re, sys
from pathlib import Path
RX = [re.compile(r"addEventListener\(\s*['\"`]message['\"`]\s*,"), re.compile(r"onmessage\s*=")]
ORIGIN = re.compile(r"(?:event|e|ev|msg|message|evt)\.(?:origin|source)\b")
SINK = re.compile(r"innerHTML|insertAdjacentHTML|document\.write|outerHTML|\beval\(|new Function\(")
def scan(path):
    try: text = path.read_text(errors="replace")
    except Exception: return
    for rx in RX:
        for m in rx.finditer(text):
            win = text[m.end():m.end()+2000]; depth=0; body=""
            for i,ch in enumerate(win):
                if ch=="{": depth+=1
                elif ch=="}":
                    depth-=1
                    if depth==0: body=win[:i+1]; break
            else: body=win[:1500]
            line = text[:m.start()].count("\n")+1
            v=[]
            if not ORIGIN.search(body): v.append("NO SENDER CHECK")
            if SINK.search(body): v.append("DOM sink in handler")
            if v: print(f"[RISK] {path.name}:{line} -> {'; '.join(v)}")
for a in sys.argv[1:]:
    p=Path(a)
    for f in (sorted(p.rglob("*")) if p.is_dir() else [p]):
        if f.suffix in {".js",".mjs",".ts",".jsx",".tsx",".html",".vue",".svelte"}: scan(f)
```

## Les quatre défenses, par ordre de leverage

1. **Vérifie l'expéditeur, toujours.** Première ligne de chaque handler de message : `if (event.origin !== EXPECTED) return;`. Une ligne, ça tue toute la classe. Cette ligne manquait dans une bibliothèque embarquée par un des sites les plus consultés du monde.
2. **Un wrapper Trusted Types qui sanitize, ou rien.** Un `createHTML` qui laisse passer les octets est un badge de conformité sur une porte ouverte. Si tu adoptes Trusted Types, la policy doit vraiment contraindre (DOMPurify ou équivalent), pas juste emballer.
3. **Sandboxe tes srcdocs.** Un `<iframe srcdoc>` sans `sandbox` hérite de ton origine. `sandbox="allow-scripts"` (sans `allow-same-origin`) rend le document injecté impuissant contre le tien. Le volet de preview était sandboxé ; le frame de l'attaquant, non.
4. **La CSP est un budget, audite la allowlist.** Tout endpoint qui echo un paramètre callback est une primitive d'exécution de script (le JSONP n'est pas mort, il vit dans les endpoints oembed). `youtube.com` dans une CSP, ce n'est pas « juste des vidéos » : lis-le comme « YouTube décide quel JavaScript tourne sur ma page ».

## Ce que ça veut dire pour les plateformes IA

Le modèle de confiance d'une app de chat IA est inhabituel : **le contenu généré par les utilisateurs devient l'UI de l'application** (les conversations partagées rendent des graphs, des previews, des embeds à l'intérieur de l'origine first-party). Chaque bibliothèque que la plateforme charge pour rendre ce contenu hérite de l'autorité de la plateforme, et l'attaquant choisit quel contenu déclenche quelle bibliothèque. Le fix d'OpenAI (rejet des messages MathLive inter-frames plus changements de CSP) est correct et shippé en huit jours. Les 5 000 $ de bounty pour un takeover complet de compte sur le produit flagship sont, notons-le au passage, un curieux signal de pricing.

**TL;DR** : un lien de conversation ChatGPT partagé + le listener MathLive qui trustait n'importe quel expéditeur + sink innerHTML + srcdoc non sandboxé + bypass CSP via le JSONP YouTube = le token de session et toutes les conversations privées, patché le 26 octobre. La classe de bug, c'est `addEventListener('message')` sans check d'origine ; l'audit de 100 lignes ci-dessus la flague dans tes bundles (et a correctement flaggé le MathLive vulnérable tout en passant le corrigé). Une ligne de validation `event.origin` par listener, c'est tout le vaccin.

Sources : [Parameter : We took over ChatGPT accounts](https://www.parameter.ai/labs/we-found-a-gap-at-openai) · [MathLive](https://mathlive.dev/) · audit vérifié contre mathlive 0.100.0 (4 listeners, aucun check d'expéditeur, sinks innerHTML présents) et 0.111.1 (pattern absent du bundle principal)
