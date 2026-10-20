---
titre: Gouvernance déclarée vs gouvernance démontrable — quelqu'un a écrit le standard, alors on a construit la couche
date: 2026-10-20
themes: preuve, agents
resume: Un working paper sur la plateforme Apply AI Alliance de la Commission européenne nomme l'écart que cette série contourne depuis le début : la gouvernance qui dit ce qui devrait se passer, contre la preuve de ce qui s'est réellement passé. On a construit la couche opérationnelle, en open source — et on aimerait échanger.
---

Chaque cadre de gouvernance que j'ai jamais lu partage une hypothèse silencieuse : que quelque part entre la politique et le résultat, quelqu'un pourrait reconstituer ce qui s'est réellement passé. La plupart du temps, c'est impossible.

Un working paper actuellement sur la plateforme Apply AI Alliance de la Commission européenne nomme cet écart mieux que tout ce que j'ai lu dans la littérature de gouvernance : **"From Declared Governance to Demonstrable Governance"** du Dr Indira Bunic. Sa distinction centrale tient en une phrase :

> La gouvernance déclarée dit ce qui devrait se passer. La gouvernance démontrable peut montrer ce qui s'est réellement passé.

Le papier passe cette distinction à quatre tests opérationnels — redevabilité, auditabilité, échelle, durabilité — et le résultat est une lecture inconfortable pour quiconque signe une politique de gouvernance IA pour vivre. Deux tiers des DSI et CTO déclarent être tenus responsables de systèmes d'IA qu'ils ne contrôlent pas entièrement. 95 % des data leaders admettent manquer de visibilité complète sur les décisions de leur IA. Et l'étude de cas au centre de tout est la plus tranchante : **Robodebt** — un système d'aide sociale australien qui n'était *ni* de l'IA, *ni* une boîte noire, *ni* difficile à expliquer — et qui a fonctionné illégalement à l'échelle nationale pendant des années quand même. Si un système simple, déterministe et pleinement explicable peut échapper à sa gouvernance, alors l'explicabilité n'a jamais été le problème. C'était l'architecture sous l'explication.

Ma phrase préférée du papier est celle que je mettrais au mur :

> Reconstituer ce qui s'est passé après un incident, ce n'est pas de la gouvernance ; c'est de la forensique. La véritable auditabilité exige des preuves au niveau des décisions, en amont du dommage.

## La version praticien était déjà dans les commentaires

Sous le papier sur la plateforme de la Commission, il y a exactement un commentaire, de Jose Carretero, et il dit en trois phrases ce que le monde de l'infra et de la sécurité sait depuis des décennies :

> J'aime le mot « démontrable » ici. Une politique qui dit qu'un humain est dans la boucle n'est pas la preuve qu'un humain a réellement participé à une décision précise. En infrastructure et en sécurité, on a l'habitude de garder les logs, les approbations et l'historique des changements. La gouvernance de l'IA a probablement besoin du même état d'esprit : si quelque chose tourne mal six mois plus tard, on doit pouvoir voir ce qui s'est réellement passé.

C'est tout. C'est tout le secret. La gouvernance de l'IA n'a pas besoin d'une nouvelle discipline — elle a besoin de la discipline que les équipes ops pratiquent déjà, pointée vers les décisions au lieu des serveurs. Le papier l'appelle gouvernance démontrable. Les gens de l'infra appellent ça un historique de changements avec reçus.

## Ce que construire la couche nous a appris

Depuis quelques mois, je construis la couche démontrable pour une tranche de ce problème : les agents IA. Pas comme pitch produit — comme projet open source dont la piste d'audit est publique, y compris les dix vulnérabilités qu'un auditeur externe y a trouvées. Le construire a appris quelques choses que les cadres ne disent pas :

**1. Logger, c'est la moitié facile. L'autre moitié, c'est rendre le log crédible.** N'importe quel processus peut écrire « décision prise, humain a approuvé ». La question que pose un sceptique six mois plus tard : qui a écrit cette ligne, et pouvait-il la modifier ? Notre réponse est ennuyeuse et vieille : une chaîne de hash pour que le passé ne se réécrive pas discrètement, et des horodatages ancrés hors de notre propre infrastructure — parce qu'un reçu contre-signé par la partie qu'il protège, c'est un journal intime, pas une preuve.

**2. Le « par qui » demande des clés, pas des noms.** Un nom dans un log est une étiquette que n'importe qui peut taper. Ce qui rend l'auteur vérifiable, c'est que l'écrivain de chaque enregistrement détient une clé que personne d'autre ne détient — et que la liste des auteurs légitimes est elle-même scellée, pour qu'un agent ne puisse pas se déclarer nouvel auteur en plein vol.

**3. La preuve doit exister avant l'incident.** Chaque histoire de gouvernance qui commence par « après la brèche, on a sorti les logs », c'est le point forensique du papier avec un badge autour du cou. L'enregistrement doit être une condition du système qui tourne, pas une réponse à sa panne.

**4. Il doit survivre au fournisseur.** Le quatrième test du papier — la durabilité — est celui que presque personne ne conçoit. Les outils sont retirés, les modèles remplacés, les startups rachetées, et les preuves de gouvernance partent avec. Un enregistrement de décision ne se cumule que s'il survit au système qu'il enregistre. Sinon, chaque génération repart de zéro — exactement ce que le papier observe sur le terrain.

**5. Il doit être exécutable.** Un schéma que personne ne peut exécuter, c'est de la gouvernance déclarée avec des étapes en plus. Les cinq choses que le papier dit qu'un régime démontrable doit montrer — quand la décision a eu lieu, pourquoi, qui l'a autorisée, quelles conséquences ont été considérées, si le résultat est resté aligné — sont exactement les champs d'un reçu. Quand, pourquoi, qui, ce qui a été touché, et si la fin correspondait au but. On n'a pas inventé ces champs ; le papier et nous y sommes arrivés par les deux bouts, et c'est généralement comme ça qu'on sait qu'une forme est réelle.

## L'invitation

Voilà pourquoi j'écris ce post au lieu de juste linker le papier : l'écart entre gouvernance déclarée et démontrable ne sera pas fermé par des papiers ou des outils seuls — il sera fermé par les gens qui écrivent les politiques et les gens qui construisent les enregistreurs, en comparant leurs notes. Donc :

**Au Dr Bunic** — si la prochaine révision du working paper veut un exemple concret de la couche démontrable pour l'IA agentique, le projet est open source, l'audit est public, et j'accueillerais volontiers cet examen. Les cinq démonstrables de votre section 3 sont, champ pour champ, le schéma auquel nous sommes arrivés ; voir la même forme depuis la gouvernance et depuis l'outillage mérite qu'on l'écrive ensemble.

**À Jose Carretero** — votre commentaire de trois phrases est le pont praticien dont cette discussion a besoin. L'état d'esprit que vous décrivez est exactement ce que nous avons construit ; j'adorerais comparer là où la discipline infra se transfère proprement aux décisions d'IA — et où elle casse.

**À quiconque, dans l'Alliance ou non, travaille sur la gouvernance démontrable** — que devrait contenir la preuve d'une décision d'IA importante pour que *vous* la traitiez comme une preuve plutôt que comme une histoire ? Les commentaires sont ouverts, et je réponds à tout.

## Les limites honnêtes

L'outillage décrit couvre l'IA agentique — des agents logiciels qui agissent — pas toute l'étendue des « systèmes d'IA » adressés par le papier. Une chaîne de hash ancre ce qui a été enregistré ; elle ne rend pas une mauvaise décision bonne. Et le papier a raison sur sa propre base de preuve, riche en enquêtes : notre réponse, ce n'est pas une meilleure enquête, c'est un enregistrement — et c'est tout le propos.

La gouvernance déclarée dit ce qui devrait se passer. La gouvernance démontrable peut montrer ce qui s'est réellement passé. La deuxième est constructible, et certains d'entre nous la construisent en open source. Venez disputer avec le code.

*(Le projet est [noirebox](https://github.com/noirebox/noirebox) — cœur sous licence MIT, audit public, et une suite de tests que vous pouvez exécuter avant de croire un mot de ceci.)*
