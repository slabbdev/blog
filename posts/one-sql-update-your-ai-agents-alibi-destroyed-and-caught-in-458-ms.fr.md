---
titre: "Un seul UPDATE SQL. L'alibi de ton agent IA, détruit — et attrapé en 458 ms"
date: 2026-10-22
themes: agents, preuve
resume: "Les décisions de ton agent IA vivent dans un fichier qu'il peut éditer. On donne à un attaquant une console SQLite contre un journal scellé et on réécrit une décision — la chaîne l'attrape en 458 ms, au numéro près. Le lab, les limites, et les petits caractères qui comptent."
source: https://github.com/noirebox/noirebox
image: https://blog.slabb.dev/img/one-sql-update-noirebox.png
image_alt: "Un seul UPDATE SQL : un attaquant réécrit le journal scellé d'un agent IA — altération détectée en 458 ms"
---

> LiteLLM a été compromis deux fois sur PyPI cette année — en mars (1.82.7/1.82.8, TeamPCP), puis à nouveau cette semaine (1.107.0, cette fois en passant par la CI des mainteneurs). Dans la même semaine, OpenAI admettait que ses propres agents avaient affaibli leur monitoring interne. Deux histoires, un trou dont personne ne parle : **quand un agent IA fait quelque chose qui t'engage, qu'est-ce qui prouve exactement ce qu'il a fait ?** La réponse qui dérange : dans la plupart des installations, la « trace » est un fichier posé à côté de l'agent — et l'agent, ou quiconque tient ses identifiants, peut l'éditer.

Ce post, c'est l'attaque. Pas une expérience de pensée — un lab à lancer en deux minutes : sceller un journal, donner la console SQLite à l'attaquant, réécrire une décision, et regarder le verdict. Puis la partie honnête : ce que ça protège vraiment, et ce que ça ne protège pas.

C'est la suite pratique de [l'article boîte noire](https://blog.slabb.dev/fr/i-built-the-flight-data-recorder-for-ai-agents.html), et l'outil c'est [NoireBox](https://github.com/noirebox/noirebox) — MIT, `pip install noirebox`, tout ce qui suit tourne sur un laptop.

## Le setup : un journal qui ressemble à tous les autres

Trois événements, du genre ennuyeux qui s'avère compter : un appel, une sortie, une évaluation.

```python
from noirebox.store import EventStore
from noirebox.chain import KeyPair, verify_chain
from noirebox.attestation import build_attestation

store = EventStore("cr.db")
key = KeyPair.load_or_create("cr.key")

store.append("llm_call", {"agent": "cr-reunion", "prompt": "Résume la réunion", "model": "gpt-demo"}, key)
store.append("llm_output", {"summary": "Le client VALIDE le devis, prochaine étape : signature."}, key)
store.append("eval", {"score": 0.94, "dataset": "golden-cr-v1"}, key)

att = build_attestation(store, key)
print(att["total_events"], att["chain_valid"])   # 3 True
```

Un événement, brut, contient tout le trick :

```json
{
  "seq": 2,
  "ts": "2026-10-22T11:55:05.856+00:00",
  "type": "llm_output",
  "payload": {"summary": "Le client VALIDE le devis, prochaine étape : signature."},
  "prev_hash": "5f164b1ab574fb89e84d2f88d93bdd5a1a80282ae4710fda89fb92282ca33c59",
  "event_hash": "37093f3e23b64c1c7f3ed621ce448c9eba178b5a732ee57f4ad1d0c47b0850e8",
  "signature": "2ecfdb1233a43d08d8bf836db494dc5cbaf2c53674eae409ed…"
}
```

`event_hash` = `SHA-256` de tout : seq, timestamp, type, payload **et le hash de l'événement précédent**. La signature est Ed25519 sous la clé de l'instance, dont la partie publique voyage dans chaque export. L'historique n'est pas stocké — il est *engagé*.

## L'attaque

Pas d'exfiltration, pas de chaîne d'exploits. L'attaquant, c'est n'importe qui avec un accès fichier : l'agent lui-même qui tient un shell, un script rogaton, un insider, une « backup restaurée ». Il ouvre la base et change une décision :

```sql
UPDATE events SET payload = '{ "summary": "Le client REFUSE le devis, aucune action requise." }'
WHERE seq = 2;
```

Le compte-rendu dit maintenant que le client est parti. Aucune action requise. Rien dans le fichier ne paraît anormal — chaque ligne est du JSON bien formé, les timestamps sont intacts.

Puis n'importe qui peut demander un verdict :

```text
>>> verify_chain(public_key, store.all())
[✗] DETECTED — event 2: invalid hash (content was modified)
```

Pas « quelque chose a changé quelque part » — **event 2, contenu modifié**. Chaque octet après cet événement était chainé aux octets avant lui ; la réécriture casse l'engagement et il n'y a aucun moyen de le recoller sans la clé, ou sans refaire toute la queue du journal.

## Passons à l'échelle : 1 000 événements, un UPDATE

La démo ci-dessus fait trois événements. Voici la même attaque sur un journal de 1 000 événements, altération en plein centre :

```text
1 000 événements, vérification propre :      242 ms, valid=True
1 000 événements, un UPDATE
  au seq=500, vérification altérée :         458 ms → {"seq": 500, "reason": "invalid hash (content was modified)"}
```

458 ms pour localiser une seule décision falsifiée parmi mille, sur un laptop, avec SQLite et la crypto de la stdlib. La vérification est O(n) et le coût du mensonge sur un événement, c'est le coût de rehacher la moitié du journal — par tentative.

## L'autre côté du verre : l'auditeur

Le but n'est pas que *toi* tu fasses confiance à ton propre journal. C'est qu'un tiers — client, DPO, tribunal — puisse le vérifier **sans te faire confiance** :

```bash
curl -s http://127.0.0.1:8768/api/v1/export > export.json
python3 verifier/verifier.py export.json
```

```text
[✓] INTACT — 3 events verified, attestation valid, 0 anchor tokens …
    head of chain: db9f04dd80b81d7b…        exit code: 0
```

Et sur l'export altéré :

```text
[✗] TAMPERING DETECTED
    event 2: invalid hash (content modified)   exit code: 1
```

Le vérificateur recalcule toute la chaîne depuis le fichier d'export. Pas de dashboard, pas d'appel API vers la maison, pas de « fais-moi confiance, les logs sont bons ». Exit 0 ou exit 1.

## Les petits caractères — à lire avant de dépendre de ça

Altérable-**détectable** n'est pas altérable-**preuve**, et la différence, c'est tout le produit :

- **La clé est la couronne.** Dans la démo, `cr.key` est posée à côté du store — un attaquant avec accès fichier peut réécrire *et re-signer* chaque événement avec. C'est là que le modèle de menace compte : le sceau tient contre quiconque ne tient pas la clé, donc la custody de la clé est la vraie frontière de sécurité.
- **La régénération complète de la chaîne est la version sophistiquée de l'attaque** : tout effacer, rejouer, re-signer avec ta clé. C'est exactement ce à quoi répond l'**ancrage RFC 3161** — périodiquement, le journal scelle son propre hash de tête auprès d'une autorité d'horodatage externe, dans un événement *à l'intérieur* du journal. « Cette tête exacte existait à la date T », signé par une clé que l'attaquant n'a pas. Rejouer le passé et les ancres ne matchent plus.
- **Supprimer tout le store** supprime la preuve — aucun journal ne survit à la destruction de son stockage. Les ancres et exports gardés ailleurs sont la mitigation ; c'est de la discipline opérationnelle, pas du code.
- Et la ligne légale, exprès : c'est de l'ingénierie de la preuve, pas une certification de conformité. Ça ne rend rien « AI Act compliant » — ça rend les affirmations *vérifiables*, ce qu'il faut avant même que quelqu'un puisse commencer à vérifier.

## Des agents, pas des dashboards

Les quatre mêmes opérations existent en serveur MCP (`noirebox-mcp`) : `noirebox_scan` (garde-fou sur les transcripts en entrée), `noirebox_log_event`, `noirebox_verify`, `noirebox_attestation`. N'importe quel agent qui parle MCP reçoit une boîte noire comme il reçoit un filesystem — et c'est le but : le journal n'est pas une fonctionnalité d'un produit, c'est une infrastructure que l'agent ne peut pas désactiver.

On arrive toujours à la même conclusion sous un autre angle : *qui garde le gardien quand le gardien est un fichier dans le repo ?* La réponse n'a jamais été « un meilleur fichier ». C'est une structure dont la clé vit hors de portée de ce qu'on regarde.

## Run it yourself

```bash
pip install noirebox            # MIT, 0.24.0 — le lab ci-dessus, c'est toute l'API
git clone https://github.com/noirebox/noirebox
cd noirebox && .venv/bin/python demo/demo_tamper.py    # la chaîne explose
python3 verifier/verifier.py export.json               # exit 0 / 1 / 2
```

Modèle de menace, specs et limites honnêtes : [docs/THREAT-MODEL.md](https://github.com/noirebox/noirebox/blob/main/docs/THREAT-MODEL.md) · Blog du projet : **[blog.noirebox.eu](https://blog.noirebox.eu)** · Repo : [github.com/noirebox/noirebox](https://github.com/noirebox/noirebox)

**TL;DR** — les logs de ton agent sont modifiables jusqu'à ce qu'ils soient chainés et signés, et la preuve doit se vérifier sur la machine de quelqu'un d'autre sans te faire confiance. Un UPDATE SQL suffit pour essayer. 458 ms suffisent pour se faire attraper.
