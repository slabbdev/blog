---
titre: "155 réponses ont fui entre clients d'une plateforme IA : le bug de KV cache GLM-5.3 — et le test canari pour ton provider"
date: 2026-10-27
themes: securite, ia
resume: "Sur Cloudflare Workers AI, 155 réponses de GLM-5.3 contenaient les données d'autres clients — des pages de KV-cache périmées servies avec HTTP 200. Le mécanisme, la repro en 25 minutes, le bug SGLang derrière, et un script canari pour tester TON provider."
source: https://dev.to/slabb/155-responses-leaked-between-ai-customers-the-glm-53-kv-cache-bug-and-the-canary-test-for-your-59n8
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Ffni04et32wbrfou5e08s.png
image_alt: "155 réponses ont fui entre clients IA — le bug de KV cache GLM-5.3 et le test canari"
---

> Entre le 27 août et le 9 septembre, certaines réponses de GLM-5.3 sur Cloudflare Workers AI contenaient **les prompts et générations partielles d'autres clients**. Pas une base de données violée, pas une injection de prompt — le moteur d'inférence lui-même a servi des **pages de KV-cache périmées de requêtes précédentes sans aucun lien**, avec un HTTP 200 propre. Exactement **155 réponses** touchées, toutes déclenchées par des prompts de plus de **681 280 tokens**. Cloudflare a publié l'autopsie complète hier. Ce post, c'est le mécanisme en quatre étapes, pourquoi la même classe de bug peut dormir dans d'autres stacks d'inférence, et un script canari qui teste TON provider contre les fuites inter-requêtes.

Le détail qui doit t'arrêter : **681 280, c'est 65 % de 1 048 576** — la fenêtre de contexte du modèle. Quelqu'un a dimensionné le pool KV à environ deux tiers du contexte et l'a shipé. Tout le reste découle de ce seul nombre.

## La chaîne d'échec, étape par étape

Tiré de [la divulgation de Cloudflare](https://blog.cloudflare.com/kv-cache-exposure-remediation/), croisé avec [l'issue SGLang #30233](https://github.com/sgl-project/sglang/issues/30233) (ouverte depuis le 6 juillet) :

1. **Le mismatch.** GLM-5.3 est sorti avec une fenêtre de contexte de 1 048 576 tokens, mais le pool KV de prefill ne tenait que 681 280 tokens. Cloudflare savait que le pool était plus petit et *croyait* que le moteur rejetterait proprement les prompts trop grands.
2. **Le chemin de rejet.** Un prompt plus long que le pool est rejeté au prefill — mais en **mode prefill/decode désagrégé**, le prompt rejeté a été « remplacé par un placeholder d'un token », et le prefill n'a transféré au decode que les pages KV de ce placeholder. Aucune erreur n'a été renvoyée.
3. **La lecture non initialisée.** Le decode avait réservé **8 pages KV** pour la requête. Seule la page P0 a été écrite. L'attention a alors **lu les 8 pages réservées** — dont 7 contenaient encore des données de *requêtes antérieures sur le même nœud*. Les prompts d'autres clients, les générations d'autres clients.
4. **Le 200 propre.** La réponse est sortie composée en partie du contexte de quelqu'un d'autre. Pas de code d'erreur, pas d'anomalie — c'est pour ça qu'il a fallu un chercheur externe, et non le monitoring, pour l'attraper.

Deux bugs se sont superposés : un **bug de configuration** (pool < contexte — celui de Cloudflare, et seul GLM-5.3 y était touché parce que tous les autres modèles de Workers AI avaient un pool plus grand que leur contexte) et un **bug de moteur** (les requêtes rejetées survivaient jusqu'au handoff KV — celui de SGLang, générique aux déploiements désagrégés, corrigé en **v0.5.22** après le draft de PR #38704 de Cloudflare et les suites fusionnées #36988/#38935). Et un troisième facteur qui n'est pas un bug : **les pages KV ne sont pas mises à zéro entre requêtes par design** — la performance dépend de la réutilisation. Toute la sécurité de l'architecture repose sur la comptabilité autour de ces pages being airtight — étanche.

## La timeline qui mérite d'être étudiée

Signalé par Gadi Evron (Knostic) via HackerOne le **8 septembre, 23:11 UTC**. Reproduit par Cloudflare **en 25 minutes**. Modèle passé privé à 14:00 le lendemain, cause racine à 14:35, config corrigée à 14:52, modèle restauré à 19:40. Divulgation coordonnée publiée le 26 octobre avec le rapporteur et les mainteneurs de SGLang, avec diagrammes de pages, liens vers les issues et le nombre exact de réponses affectées.

Mets ça à côté de la réponse eMudhra du même mois (révocation en 14 heures, puis le blame de « l'amplification des réseaux sociaux » pour la surveillance) et tu as les deux pôles de la gestion d'incident. Le post de Cloudflare se termine même par la feuille de route de durcissement — checksums KV sur chaque transfert prefill→decode, canaris, tags de propriété par page, et **vérification formelle du protocole de transfert RDMA**. Quand le mode d'échec est « la comptabilité a menti », on finit par arrêter de patcher et commencer à prouver.

## Le lab : un test canari pour TON provider

Tu ne peux pas auditer le pool KV d'un provider depuis l'extérieur. Tu *peux* détecter la classe de symptôme : des données de la requête A qui remontent dans la réponse à la requête B. C'est exactement ce que font les canaris post-incident de Cloudflare — voici la version userland, qui marche contre tout endpoint OpenAI-compatible (pointe `BASE`/`KEY`/`MODEL` vers OpenAI, les passerelles compatibles Anthropic, vLLM, SGLang, llamacpp, Ollama) :

```python
# canary.py — test de fuite inter-requêtes pour les APIs de chat
# usage: BASE=https://api.provider.com/v1 KEY=sk-... MODEL=... python3 canary.py
import os, random, string, sys, urllib.request

BASE  = os.environ["BASE"].rstrip("/")   # ex. http://localhost:8000/v1
KEY   = os.environ.get("KEY", "none")
MODEL = os.environ["MODEL"]
canary = "CANARY-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=16))

def chat(messages, max_tokens=200):
    req = urllib.request.Request(
        f"{BASE}/chat/completions",
        data=__import__("json").dumps({"model": MODEL, "messages": messages,
                                       "max_tokens": max_tokens, "temperature": 0}).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    return __import__("json").loads(urllib.request.urlopen(req, timeout=120).read())

# A — planter le canari
chat([{"role": "user", "content": f"Internal ref for this session: {canary}. Reply with 'noted' only."}])
print(f"[A] canari planté : {canary}")

# B — requêtes sans rapport ; scanner chaque réponse pour le canari
leak = False
for i in range(1, 6):
    r = chat([{"role": "user", "content": f"Write a two-sentence haiku about packet #{i}."}])
    text = r["choices"][0]["message"]["content"]
    hit = canary in text
    leak |= hit
    print(f"[B{i}] {'!!! CANARI FUIT' if hit else 'propre'} — {text[:60]!r}")
print("RÉSULTAT:", "FUITE INTER-REQUÊTES DÉTECTÉE" if leak else "pas de fuite dans cet échantillon (pas une preuve)")
```

Portée honnête, énoncée dans la dernière ligne du script : **un run propre n'est pas une preuve** — le bug GLM-5.3 exigeait des prompts au-delà du pool KV sur un nœud mal configuré. Ça attrape les fuites grossières à bas coût ; lance-le après les upgrades, contre les nouveaux endpoints, et en CI contre ta propre stack d'inférence. Sur les providers, varie-le : répète avec les requêtes B sur une *session/conversation id fraîche* — la séparation au sein d'un même compte est la clôture la plus faible à tester.

J'ai lancé le smoke test contre l'API qui génère les brouillons de ce blog (le serving GLM de Z.ai lui-même — pour mémoire, l'incident était celui du déploiement Cloudflare, pas celui de Z.ai) : endpoint et auth vérifiés, mais le solde de ma clé était vide, donc le run complet attend une recharge. Le script ci-dessus est exactement ce que je lancerai le jour où il en aura un — et ce que tu peux lancer contre ton provider ce soir, avec ta clé.

## Si tu fais tourner le moteur toi-même

La checklist opérateur du post, par priorité : passe en **SGLang v0.5.22+** (les requêtes rejetées sont retirées à la file d'admission, avant tout transfert KV) ; assure-toi que ton **pool KV est plus grand que ta fenêtre de contexte** — et ajoute le check pré-déploiement qui compare la taille mesurée du pool à la longueur du contexte, parce que GLM-5.3 est sorti sans lui ; active `--disaggregation-enable-kv-checksum` pour que chaque transfert prefill→decode soit vérifié. Le bug que tu patche a été signalé en juillet, exploité par accident en août, et divulgué proprement en octobre — si tu as déployé SGLang depuis une image d'été, tu es le public de cette checklist.

## TL;DR

Un pool KV dimensionné à 65 % de la fenêtre de contexte plus un chemin de rejet qui continuait après le refus = 155 fuites inter-clients avec HTTP 200. Cause racine en 25 minutes, corrigé en une journée, divulgation avec diagrammes au niveau page — et le bug moteur en dessous est générique, donc si tu self-host de l'inférence, c'est ta semaine de patch. Pour tous les autres : le script canari ci-dessus, cinq minutes contre ton provider. Zéro erreur sur le fil, ça n'est pas zéro fuite.

Sources : [Cloudflare — KV cache exposure remediation](https://blog.cloudflare.com/kv-cache-exposure-remediation/) · [SGLang issue #30233](https://github.com/sgl-project/sglang/issues/30233) · [SGLang PR #38704 (draft Cloudflare)](https://github.com/sgl-project/sglang/pull/38704)
