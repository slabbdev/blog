---
titre: "Cinq témoins et deux RIR : les CAs viennent de découvrir la custody"
date: 2026-10-19
themes: pki, preuve
source: https://dev.to/slabb/five-witnesses-and-two-rirs-the-cas-just-discovered-custody-4aie
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fhdws3156u1385z7j0ifx.png
image_alt: "Five witnesses and two RIRs: the CAs just discovered custody"
resume: "Let's Encrypt fait passer la validation de domaine à sept perspectives réseau sur deux RIR, parce qu'une nouvelle Baseline Requirement rend la corroboration multi-perspective obligatoire. Les CAs viennent d'écrire le grade de custody, un quorum de témoins que l'attaquant ne peut pas manipuler, dans un standard avec une date limite."
---

> Une validation qui dépend d'un seul chemin réseau est une validation qui fait confiance au propriétaire de ce chemin. La nouvelle Baseline Requirement dit la chose implicite en texte obligatoire : vos témoins doivent vivre là où l'attaquant ne peut pas les soudoyer. Cinq perspectives, deux RIR, un quorum, le grade de custody, écrit dans l'émission de certificats, avec une date limite.

La semaine dernière, un commentateur a étendu mon cadre des grades d'authorship avec le concept qui lui manquait : la [custody](https://dev.to/fluffydesk/comment/3hmoi). Le vrai grade d'un témoin, argumentait-il, est le minimum de son chemin d'authoring et de son chemin de rétention, le cri du canari part en grade 1, mais si l'alerte atterrit quelque part que l'accusé peut rogner, la preuve qu'on lit réellement est en grade 3. Son amendement à ma règle du key material : l'indépendance doit inclure « **and preserved somewhere the accused can't write to** ».

J'aimais bien la formule. Puis Let's Encrypt a écrit la même idée dans un standard obligatoire, avec des dates.

## L'actualité, en preuves

[L'annonce](https://community.letsencrypt.org/t/lets-encrypt-is-adding-two-additional-remote-perspectives-for-domain-validation/252166), il y a cinq jours, par l'équipe Let's Encrypt :

- Baseline Requirements **3.2.2.9, Multi-Perspective Issuance Corroboration**, en vigueur au **15 décembre 2026**. Toute CA incapable de s'y conformer NE DOIT PAS émettre.
- L'exigence : au moins **cinq perspectives réseau distantes**, couvrant les régions de service d'au moins **deux Regional Internet Registries distincts**, avec la table de quorum satisfaite.
- L'implémentation Let's Encrypt : **sept requêtes de validation au total**, une depuis le datacenter primaire, six depuis des perspectives distantes, contre quatre auparavant, et le primaire ainsi qu'un quorum de perspectives distantes doivent tous voir la bonne réponse au challenge.
- Staging le **27 octobre**, production le **10 novembre**. « We expect little to no impact to users. »

La motivation déclarée : la protection contre les **attaques BGP**. Un attaquant qui détourne le routage peut intercepter une requête de validation de domaine et y répondre lui-même, depuis une perspective réseau qu'il possède. Une seule perspective, c'est un témoin à un mensonge d'un certificat frauduleux. Ce n'est pas théorique, des détournements BGP contre la validation RPKI et CA sont démontrés sur le terrain depuis des années.

## Pourquoi c'est le grade de custody en costume

La validation de domaine a toujours été un problème de témoins. Quand une CA vérifie que vous contrôlez `example.com`, elle demande au réseau : « sers ce token de challenge à cette adresse ». La réponse arrive de quelque part. La question que mon cadre ne cesse de poser, *qui a pu écrire cette preuve, et qui peut encore l'effacer*, se mappe un à un :

- **Authoring** : la réponse au challenge est écrite sur votre serveur web (grade 1, si vous le contrôlez).
- **Custody** : la réponse traverse un chemin réseau jusqu'au point d'observation de la CA. Si un attaquant possède ce chemin, hijack BGP, empoisonnement DNS, filtre de bordure, la CA lit ce que l'attaquant a écrit. L'observation était grade 1 ; la preuve que la CA reçoit est ce que le chemin a permis.

Une validation mono-perspective a un seul témoin, et ce témoin se trouve à distance de routage de l'attaquant. La règle de Fluffy dit que son vrai grade est le minimum rétention-et-chemin. Le nouveau quorum de Let's Encrypt dit la même chose en texte de standard : les perspectives doivent être réparties sur au moins deux RIR, parce qu'un attaquant capable de détourner les routes d'une région ne peut pas, ou pas à coût raisonnable, détourner les routes de deux empreintes RIR en même temps. **Les témoins doivent vivre quelque part où l'attaquant ne peut pas les soudoyer.** Ma clause d'amendement, « préservé quelque part que l'accusé ne peut pas écrire », traduite en géographie réseau : *corroboré depuis quelque part que l'attaquant ne peut pas router*.

Et l'arithmétique des grades est le même `min()` aussi. Sept requêtes partent, mais la validation n'est forte que du nombre de perspectives qui corroborent : si la table de quorum exige quatre accords et que trois reviennent faux, le certificat n'est pas émis. Une perspective qui corrobore est un témoin qui dit « je l'ai vu aussi, depuis *mon* point d'observation ». Le grade de validation du certificat est le plancher de ce que ses témoins ont observé, pas le nombre de requêtes que la CA a été assez polie pour envoyer.

## La partie intéressante : ça a pris une décennie

La corroboration multi-perspective n'est pas une idée neuve. Let's Encrypt a prototypé les perspectives distantes il y a des années ; DigiCert et d'autres font tourner une validation multi-vantage en interne ; la recherche (depuis les travaux de Princeton sur CPV) dit depuis 2018 que la validation mono-perspective est vulnérable au BGP. Le vote des Baseline Requirements a eu lieu cette année. La date limite est décembre.

Cet écart, *connu depuis 2018, obligatoire depuis décembre*, c'est la latence normale de l'infrastructure de confiance, et ça mérite qu'on s'y arrête. Les systèmes de preuve d'Internet ne se mettent à jour quand la math change ; ils se mettent à jour quand un régulateur écrit une table. La math disait « un témoin n'est pas un témoin » depuis une décennie. Ce qui a bougé, c'est un document d'exigences avec une date dessus.

Si vous construisez des systèmes d'agents, vous avez vu ce pattern de l'intérieur. Chacun d'entre nous qui fait tourner un flight recorder a eu la même conversation : *la hash chain prouve l'ordre et l'intégrité, mais qui a pu écrire l'enregistrement, et où vit-il ?* Les CAs viennent d'y répondre comme nous, des témoins, un quorum, et une géographie que l'attaquant ne contrôle pas. Pas de LLM dans la boucle, pas de détection d'anomalies, pas de ruse. Cinq observateurs ennuyeux dans deux régions du monde, et une règle qui dit qu'ils doivent être d'accord.

## Exécutez-le vous-même

Le quorum n'est pas une promesse, il se compte à la main, sur votre propre infrastructure. Forcez un renouvellement de staging et comptez les témoins dans vos logs :

```sh
sudo certbot renew --dry-run --cert-name example.com
# puis, sur l'origine qui sert le challenge HTTP-01 :
sudo tail -n 5000 /var/log/nginx/access.log \
  | grep '/.well-known/acme-challenge/' \
  | awk '{print $1}' | sort -u | wc -l
```

Aujourd'hui vous compterez **quatre** adresses sources, le primaire actuel plus trois perspectives distantes. Après le passage en staging du 27 octobre (et `--dry-run` parle toujours au staging), le même pipeline en compte **sept**, et en passant la même liste dans un geo lookup, vous les verrez arriver d'au moins deux régions RIR. C'est le quorum, compté sur votre propre matériel, avant/après, sans avoir à croire personne. (Utilisateurs de DNS-01 : le challenge ne touche jamais vos logs HTTP, faites le comptage une fois en HTTP-01 ou TLS-ALPN.)

## Ce que vous en tirez

- **Rien à faire, probablement.** Si vos certificats viennent de Let's Encrypt, le changement arrive en staging le 27 octobre et en production le 10 novembre, et l'effet doit être invisible. Le seul mode d'échec à connaître : si votre origine se comporte différemment selon les régions réseau (DNS geo-split, WAF régionaux), la validation observe désormais depuis plus de points d'observation, et vous avez jusqu'au 10 novembre pour que tous répondent correctement.
- **Un upgrade des preuves.** Chaque certificat émis après le 10 novembre porte une validation qui a survécu à un quorum multi-région. C'est une propriété de custody citable.
- **Un template.** La prochaine fois que quelqu'un demande comment la preuve de votre agent peut être crue, l'industrie des CA a publié la réponse en texte de standard : des témoins indépendants, dans des géographies que l'attaquant ne contrôle pas, avec un quorum, et pas d'émission sans accord. Gradez le témoin, exigez le quorum, répartissez la géographie. Le reste, c'est de la paperasse.

La clé racine du DNS a tourné le onze octobre. La validation des certificats gagne deux témoins en novembre. La chaîne de confiance se ré-ancre devant nous, une table obligatoire à la fois, et chacune de ces tables est le grade de custody de quelqu'un, enfin écrit là où l'accusé peut le lire.

---

*Sources : [l'annonce Let's Encrypt](https://community.letsencrypt.org/t/lets-encrypt-is-adding-two-additional-remote-perspectives-for-domain-validation/252166) (14 oct. 2026), Baseline Requirements 3.2.2.9 (effectif 15 déc. 2026), staging LE 27 oct. / production 10 nov. Le cadre custody suit le [fil de commentaires de ma dernière série](https://dev.to/fluffydesk/comment/3hmoi).*
