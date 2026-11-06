---
titre: "Claude Code expédiait ton adresse email à chaque site web qu'il visitait : la fuite User-Agent, l'issue system-prompt de 5 mois, et le check en 5 points"
date: 2026-11-06
themes: securite, agents
resume: "Claude Code mettait l'email de ton compte dans le User-Agent de ses requêtes web : chaque log de serveur sur le chemin de l'agent récoltait un lead scam-ready, et la même adresse embarque dans le system prompt de chaque session, issue ouverte depuis juillet. Corrigé par un mod intégré en 2.1.317 après le passage viral. Le test runtime pour ton installation."
source: https://dev.to/slabb/claude-code-was-mailing-your-email-address-to-every-website-it-visited-the-user-agent-leak-the-12k6
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fj9oljnyn04qj9tv7bm7u.png
image_alt: "Claude Code expédiait ton adresse email à chaque site web : la fuite User-Agent et le check en 5 points"
---

> Deux issues GitHub, à cinq mois d'écart, décrivent la même fuite par deux tuyaux différents. Celle d'hier, déposée à 22h13 et désormais à 360 réactions : **Claude Code envoie l'adresse email de ton compte à des sites web tiers arbitraires dans le header `User-Agent`** quand ses outils web tournent. La preuve du rapporteur, c'est sa boîte mail : des dizaines de scams par jour, parce que chaque log de serveur sur le chemin de l'agent récoltait une adresse vérifiée, active, d'un développeur utilisateur d'outils IA. Celle de juillet (#81138, toujours ouverte) : **la même adresse email est injectée dans le system prompt du modèle à chaque session**, code cité depuis le bundle livré. Anthropic a shippé un fix, un mod intégré `cc-plugin-privacy` en v2.1.317+, le jour même où la nouvelle issue est devenue virale. Ce post, c'est la mécanique des deux tuyaux, la timeline qui dit que le fix a suivi l'attention plutôt que le rapport de juillet, et les cinq vérifications qui te disent ce que ton installation fait ce soir.

## Tuyau un : le User-Agent qui t'identifiait auprès d'inconnus

Le header `User-Agent` voyage avec chaque requête HTTP que tes outils émettent, et il est loggé par défaut sur quasiment chaque serveur web de la planète. L'outillage web de Claude Code y incluait l'email du compte connecté. Conséquences, par ordre croissant de gravité :

- Chaque site que ton agent fetchait voyait une adresse email vérifiée et fonctionnelle appartenant à un développeur qui paie pour de l'outillage IA. Ce n'est pas un identifiant de tracking ; c'est un **lead pré-qualifié**, et les logs de serveurs s'achètent, se vendent, fuient et s'agrègent à titre routine.
- Il liait **ton trafic d'agent et ton identité humaine dans une seule chaîne**. Les sites qui voulaient limiter les agents avaient tout ce qu'il faut pour limiter *toi* ; les sites qui voulaient cibler les utilisateurs d'IA avaient l'adresse exacte.
- Le flot de scams du rapporteur est le résultat attendu, pas une anomalie : un header UA, c'est un formulaire envoyé à chaque intermédiaire du chemin.

Et le hic, que le rapporteur a énoncé cash : l'identifiant ne servait **à rien**. Il n'aidait pas les services à distinguer le trafic agentique (un marqueur grossier aurait suffi), il détruisait l'anonymat de la session, et c'était une mine d'or pour les scammers. Du PII dans un header, c'est le pire des deux mondes : zéro bénéfice fonctionnel, exposition totale.

## Tuyau deux : l'email dans chaque system prompt

L'issue de juillet (#81138, déposée le 25-07, titrée « [BUG] Account email (PII) is injected into the model's system prompt without consent ») documente l'autre tuyau, avec le code du bundle cité depuis la v2.1.220 :

```js
let n = process.env.ANTHROPIC_UNIX_SOCKET ? void 0 : dc()?.emailAddress
return {
  ...(n && { userEmail: `The user's email address is ${n}.` }),
  ...
}
```

Qui se rend dans le system prompt de chaque session ainsi :

```text
# userEmail
The user's email address is <account email>.
```

Sourcé depuis `~/.claude.json` → `oauthAccount.emailAddress`. Où voyage un system prompt ? Vers l'API, dans les logs des deux côtés, dans tout contexte que la session touche, et de là, potentiellement, dans tout ce que le modèle cite ou transfère. La formulation de l'issue est précise et mérite d'être répétée : des données personnelles données pour **l'authentification**, détournées en **contenu de session**, sans consentement ni divulgation. Ce soir, cette issue est toujours ouverte.

## La timeline qui compte

- **25 juillet** : #81138 dépose l'injection dans le system prompt, avec le source du bundle. Aucun fix ne sort.
- **5 novembre, 22h13** : #107757 dépose la variante User-Agent. Les réactions grimpent dans les centaines dans la journée.
- **5 novembre, le jour même** : un contributeur Anthropic répond : un mod intégré, `cc-plugin-privacy`, introduit en **v2.1.317 et plus**, « bloque déterministiquement ce comportement », est activé par défaut, peut être basculé via `/plugins`, et son source sera publié aux côtés des autres mods intégrés.
- **L'anomalie à surveiller** : le rapporteur tournait **v2.1.318**, soi-disant post-fix, et voyait encore la fuite. Possibilités : le mod était désactivé chez lui, le blocage a un trou (la réponse du staff demande explicitement des rapports de gaps), ou confusion de version. « Activé par défaut » n'est pas « vérifié sur ta machine », et c'est exactement le rôle du check runtime ci-dessous.

Un commentaire du fil nomme le schéma inconfortable : l'issue privacy d'origine est restée cinq mois sans réponse, et le fix est sorti le jour où la nouvelle a atteint la front page. « Vous pouvez littéralement trier les issues par nombre d'emojis et faire du 80/20. » Un agent pourrait trier cette file ; les propriétaires de la file avaient apparemment besoin de HN.

## Les cinq vérifications pour ton installation

À lancer sur toute machine avec Claude Code. Sur la mienne, le CLI est absent mais `~/.claude.json` existe sans `oauthAccount` (donc le champ PII est vide) : tes résultats varieront, et le check 3 tranche tout.

```bash
# 1. Version : le mod privacy intégré arrive en 2.1.317+
claude --version

# 2. Le mod est-il présent et activé ?
#    Dans Claude Code : /plugins   -> chercher cc-plugin-privacy (défaut: activé)

# 3. LE TEST RUNTIME : un listener local te dit ce que ton agent envoie vraiment :
python3 -c "from http.server import *
import sys
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        print('UA =', self.headers.get('User-Agent'), file=sys.stderr, flush=True)
        self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
HTTPServer(('127.0.0.1', 8899), H).serve_forever()"
# puis, DANS Claude Code, demande-lui de fetch :  http://127.0.0.1:8899/probe
# UA contient ton email   -> ça fuit encore (signale: issue #107757)
# UA est une chaîne générique -> bloqué sur ton build

# 4. Ce qui est en jeu localement : ta config porte-t-elle l'email ?
python3 -c "import json,os; d=json.load(open(os.path.expanduser('~/.claude.json'))); \
print('email présent:', 'emailAddress' in d.get('oauthAccount', {}))"

# 5. Le check system-prompt (issue de juillet) : dans une session Claude Code fraîche, demande :
#    \" Quelle est mon adresse email ? \"
#    Si le modèle la connaît sans qu'on la lui donne, le bloc #userEmail est encore dans ton prompt.
```

Le check 5 double comme leçon générale : demande à ton agent ce qu'il sait sur toi. Il lit son system prompt plus honnêtement que le changelog ne se lit.

## Le principe, et le schéma du mois

Ton agent, c'est toi sur le web. Ses headers sont tes headers, ses prompts sont ton contexte, et tout ce qu'il transporte fuit à l'union de chaque saut. Identifier le trafic agentique est un besoin légitime, et la bonne réponse est un **marqueur de classe** (« ceci est un client automatisé, produit X, version Y »), pas **ton identité**. Le fix d'Anthropic, un mod de blocage déterministe, a la bonne forme, et le shipper par défaut est correct ; les cinq mois entre le rapport et le fix, et le fait que ça ne se soit refermé que sous charge virale, c'est la partie à retenir au moment du renouvellement.

Le grand livre de l'ère des agents, une ligne de plus : les transcripts envoyés au modèle, les extensions qui backdoorent au chargement, un vendor qui s'installe dans les agents rivaux, et maintenant l'agent qui balance ton adresse à chaque serveur touché. Même cible à chaque fois : **la surface sortante de l'agent est la surface sortante de l'utilisateur**. Audite-la comme si c'était la tienne, parce que c'est la tienne.

**TL;DR** : Claude Code mettait l'email de ton compte dans le User-Agent de ses requêtes web (chaque log de serveur recevait un lead scam-ready ; l'inbox du rapporteur l'a prouvé) et embarque la même adresse dans le system prompt de chaque session (issue ouverte depuis le 25 juillet). Corrigé par le mod intégré `cc-plugin-privacy` en 2.1.317+ le jour où la nouvelle issue est devenue virale ; le rapporteur était en .318 et la voyait encore, donc lance le check runtime : listener local, ton agent fetch, lis le UA. Cinq checks ci-dessus ; deux minutes ; ta boîte mail te remerciera.

Sources : [Issue #107757 : Privacy violation in User-Agent header](https://github.com/anthropics/claude-code/issues/107757) (rapport + réponse staff sur cc-plugin-privacy) · [Issue #81138 : email dans le system prompt, 25 juillet, code du bundle](https://github.com/anthropics/claude-code/issues/81138) · mods intégrés : [github.com/anthropics/claude-code/tree/main/mods](https://github.com/anthropics/claude-code/tree/main/mods)
