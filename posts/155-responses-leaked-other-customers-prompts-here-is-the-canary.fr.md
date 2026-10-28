---
titre: "155 réponses ont fui les prompts d'autres clients. Voici le canari qui détecte ça chez votre provider."
titre_en: "155 responses leaked other customers' prompts. Here is the canary that catches it on your provider."
date: 2026-10-30
themes: ia, securite
resume: "L'incident Cloudflare/SGLang : un pool KV calibré à 65 % du contexte + un rejet qui continuait après refus = 155 fuites croisées avec HTTP 200. Le mécanisme, et le canari qu'on a tourné pour de vrai."
resume_en: "The Cloudflare/SGLang incident: a KV pool at 65% of the context window plus a rejection path that kept going after refusal = 155 cross-customer leaks with HTTP 200. The mechanism, and the canary we actually ran."
source: https://blog.cloudflare.com/kv-cache-exposure-remediation/
---

Entre le 27 août et le 9 septembre, certaines réponses de GLM-5.3 sur Cloudflare Workers AI contenaient **les prompts et des générations partielles d'autres clients**. Pas une base de données percée, pas une injection de prompt : le moteur d'inférence lui-même a servi **des pages de KV-cache périmées de requêtes précédentes, sans lien**, avec un HTTP 200 propre. Exactement **155 réponses** touchées, toutes déclenchées par des prompts de plus de **681 280 tokens**. Cloudflare a publié l'autopsie complète.

Le détail qui doit vous arrêter : **681 280, c'est 65 % de 1 048 576** — la fenêtre de contexte du modèle. Quelqu'un a calibré le pool KV à deux tiers du contexte et a shippé. Tout le reste découle de ce seul nombre.

## La chaîne de défaillance, étape par étape

D'après la [divulgation Cloudflare](https://blog.cloudflare.com/kv-cache-exposure-remediation/), croisée avec [l'issue SGLang #30233](https://github.com/sgl-project/sglang/issues/30233) (ouverte depuis le 6 juillet) :

1. **Le mismatch.** GLM-5.3 est lancé avec 1 048 576 tokens de contexte, mais le pool KV de préfill ne tient que 681 280 tokens. Cloudflare savait que le pool était plus petit et *croyait* que le moteur rejetterait proprement les prompts trop longs.
2. **Le chemin de rejet.** Un prompt plus long que le pool est bien rejeté au préfill — mais en mode **préfill/décode désagrégé**, le prompt rejeté était « remplacé par un placeholder à un token », et le préfill ne transférait que les pages KV de ce placeholder au décode. Aucune erreur remontée.
3. **La lecture non initialisée.** Le décode avait réservé **8 pages KV** pour la requête. Seule la page P0 avait été écrite. L'attention a alors **lu les 8 pages réservées** — dont 7 contenaient encore des données de *requêtes antérieures sur le même nœud*. Les prompts des autres, les générations des autres.
4. **Le 200 propre.** La réponse a streamé, composée en partie du contexte de quelqu'un d'autre. Aucun code d'erreur, aucune anomalie — c'est pourquoi il a fallu un chercheur externe, pas le monitoring, pour l'attraper.

Deux bugs se sont superposés : un **bug de configuration** (pool < contexte — côté Cloudflare) et un **bug moteur** (les requêtes rejetées survivant jusqu'au handoff KV — côté SGLang, générique aux déploiements désagrégés, corrigé en **v0.5.22**). Et un troisième facteur qui n'est un bug pour personne : **les pages KV ne sont pas mise à zéro entre requêtes par design** — la performance dépend de la réutilisation. Toute la sécurité de l'architecture repose sur la comptabilité de ces pages.

## Le canari — et ce qu'il a dit chez nous

On ne peut pas auditer le pool KV d'un provider de l'extérieur. On **peut** détecter la classe de symptôme : des données de la requête A qui remontent dans la réponse à la requête B. Le script (`canary.py`, ~40 lignes, stdlib only) plante un marqueur unique en session A, puis scanne les réponses de requêtes sans rapport à la recherche du marqueur — contre n'importe quel endpoint compatible OpenAI.

On l'a tourné pour de vrai, protocole pré-enregistré, les 27-28 octobre (le run-log complet est public) :

- **Canari planté, 5 requêtes de scan : 5/5 propres** — zéro contenu croisé.
- **Sonde à 671 280 tokens** (le chiffre du pool Cloudflare) : **HTTP 400, erreur 1261 « Prompt exceeds max length », en 12 s** — le rejet fail-closed dont l'absence a produit la fuite.
- **Sonde à ~520k tokens** : acceptée, réponse propre, aucun écho du marqueur.
- **Encadrement du cap réel** : 522 763 tokens acceptés, 671 280 rejetés — un cap volontaire de classe 0,5M, et le seuil de l'incident est inatteignable sur ce provider.
- **Canaris jamais envoyés** ×3 : zéro occurrence dans toute réponse — le contrôle négatif qui confirme que le scanner ne matche pas dans le vide.

La ligne honnête du script s'applique à nous aussi : **un run propre n'est pas une preuve**. Le bug GLM-5.3 demandait des prompts au-delà du pool sur un nœud mal configuré. Ça détecte la fuite grossière pour pas cher ; tournez-le après chaque upgrade, contre chaque nouvel endpoint.

## Si vous faites tourner le moteur vous-mêmes

La checklist opérateur, par priorité : passez à **SGLang v0.5.22+** (les requêtes rejetées sont retirées à la file d'admission, avant tout transfert KV) ; **agrandissez le pool au-delà de la fenêtre de contexte** — avec le check pré-déploiement qui compare les deux, parce que GLM-5.3 est parti sans ; activez `--disaggregation-enable-kv-checksum` pour que chaque transfert préfill→décode soit vérifié. Ce bug a été rapporté en juillet, exploité par accident en août, divulgué proprement en octobre — si vous avez déployé SGLang depuis une image d'été, cette checklist est pour vous.

## TL;DR

Un pool KV à 65 % du contexte + un chemin de rejet qui continuait après le refus = 155 fuites croisées avec HTTP 200. Root-causé en 25 minutes, corrigé en un jour, divulgué avec les schémas page par page. Zéro erreur sur le wire n'est pas la même chose que zéro fuite — et le canari qui vérifie ça chez votre provider prend cinq minutes.

Sources : [Cloudflare — KV cache exposure remediation](https://blog.cloudflare.com/kv-cache-exposure-remediation/) · [SGLang issue #30233](https://github.com/sgl-project/sglang/issues/30233) · [SGLang PR #38704 (draft Cloudflare)](https://github.com/sgl-project/sglang/pull/38704)
