---
titre: "38 000 vulnérabilités trouvées par IA, 217 corrigées : l'audit de Glasswing, la machine à bugs d'Anthropic"
date: 2026-11-11
themes: securite, ia
resume: "Sept mois après l'annonce de milliers de bugs IA-découverts par Anthropic, l'audit indépendant est là : 37 966 findings, 217 corrigés, et un scanner d'octobre qui envoie aux mainteneurs des rapports modèle-seul. Le mainteneur de curl a reçu 45 rapports pour 6 confirmations basse sévérité. Les chiffres live du tracker, recalculés."
source: https://dev.to/slabb/38000-ai-found-vulnerabilities-217-fixed-auditing-glasswing-anthropics-bug-discovery-machine-k65
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fl8x9vhghnsk5gofyx0dy.png
image_alt: "38 000 vulnérabilités trouvées par IA, 217 corrigées : l'audit de Glasswing"
---

> Ce blog a passé le mois d'octobre à célébrer les vulnérabilités découvertes par IA : php2shell a été trouvé par des machines avant les attaquants, un modèle a craqué un bypass WAF en six heures que les humains avaient raté. Voici l'autre moitié de cette histoire, auditée. En avril, Anthropic lançait le Project Glasswing en annonçant « des milliers de vulnérabilités supplémentaires de sévérité haute et critique » à divulguer de façon responsable. La semaine dernière, [VulnCheck a publié son évaluation après sept mois](https://www.vulncheck.com/blog/anthropic-glasswing-november-update), et les chiffres ne se réconcilient pas : **37 966 findings au total, 7 349 publics, 217 corrigés**. Dans les huit semaines du 8 septembre au 2 novembre, le ledger a grossi de **11 813 findings pendant que les fixes grossissaient de 15**. Et depuis le 8 octobre, un scanner OSS envoie par mail aux mainteneurs open source des rapports « entièrement générés par modèle, sans relecture humaine ». Ce post : les chiffres audités, ce que j'ai trouvé en les recalculant depuis le tracker public ce soir, l'étude de cas curl, et l'économie inconfortable de la découverte de vulnérabilités à vitesse machine.

## Le ledger, lu sans le marketing

Depuis le propre ledger d'Anthropic (red.anthropic.com, mise à jour du 2 novembre) et le suivi de VulnCheck :

| Métrique | Valeur | Le ratio qui compte |
|---|---|---|
| Findings totaux | 37 966 | |
| Publics | 7 349 | 19,4 % des findings |
| **Corrigés** | **217** | **0,57 % des findings, 2,9 % des publics** |
| Doublons | 1 654 | 7,6× le nombre de fixes |
| Retirés | 419 | après résistance des mainteneurs |
| Exploités connus (KEV) | 2 | 0,45 % des CVEs créditées |

Le taux de vrais positifs revendiqué par Anthropic est de 94,2 % (contre 90,8 % avant), un chiffre que Patrick Garrity de VulnCheck conteste ouvertement. L'échantillon de vérité terrain le contredit : **curl**. Daniel Stenberg a reçu 45 rapports Glasswing. Sur 34 traités à ce jour : 19 rejetés comme non-vulnérabilités, 6 confirmés (tous de sévérité basse), 9 en attente. Cela fait 55,9 % de rejets sur des rapports envoyés à un des mainteneurs les plus matures en sécurité du monde, et les six vrais étaient tous low. L'épisode Mythos de mai fait écho : cinq findings, un confirmé.

Pour être juste, et ça compte : la liste des CVEs créditées n'est pas du théâtre vide. Il y a dedans des vulnérabilités réelles, créditées, parfois sérieuses, dont deux arrivées au catalogue CISA des exploitations sauvages (CVE-2026-61500, CVE-2026-26980). La machine trouve de vrais bugs. La question que force cet audit n'est pas « est-ce qu'elle sait trouver » mais « qu'est-ce que l'expédition du flux brut fait aux humains qui doivent le trier ».

## Ce que j'ai trouvé en recalculant le tracker ce soir

Le post de VulnCheck est une lecture. Le tracker qu'il cite est public ([patrickmgarrity/Anthropic-Credited-CVEs](https://github.com/patrickmgarrity/Anthropic-Credited-CVEs)), je l'ai donc cloné et j'ai lancé les chiffres moi-même, ce soir, pour ce post :

```text
$ ls cves/*.yaml | wc -l
450          # CVEs créditées en fichier, 8 de plus qu'à l'écriture du post

par mois :   fév 24, mar 15, avr 32, mai 45, jun 48, jul 49,
             aoû 54, sep 59, oct 98, nov 26 (partiel)
sévérité :   critiques 51, hautes 190, moyennes 146, basses 36, non notées 27
top produits : Linux 36, Firefox 32, BC-Java 31, wolfSSL 25,
               coder/coder 19, bc-csharp 18, filelock 16, LibreOffice 13
auto_discovered : 353 sur 450 (78 %)
recoupement KEV : CVE-2026-61500, CVE-2026-26980 présentes
```

Lis la courbe mensuelle : la sortie de la machine a à peu près **doublé en octobre** (98 CVEs) pile quand le taux de fix du ledger s'est effondré (+15 fixes sur la même fenêtre). La découverte scale avec le compute ; le triage et les fixes scalent avec des humains, et les humains de ce pipeline sont des mainteneurs non payés. Un nom de produit dans le haut du classement mérite un flag : `filelock`, un petit utilitaire Python, porte 16 CVEs créditées, ce qui sent le modèle qui re-trouve des variations de la même classe contre une seule cible, 16 fois. (Le fichier d'état du tracker compte encore 127 findings corrigés qui n'ont même jamais eu de CVE.)

## Le pivot d'octobre : de « on valide » à « vous validez »

L'événement structurel est plus discret que les chiffres. Le 8 octobre, Anthropic a lancé un **OSS Scanner** opt-in sur GitHub dont les rapports sont « entièrement générés par modèle, sans relecture humaine », et selon le décompte de l'évaluation, près de **5 000 rapports non vérifiés** étaient déjà partis en masse vers les mainteneurs. La propre formulation d'Anthropic en début d'année était candide : ils étaient « bottlenecked on our human capacity to validate these findings ». Le scanner résout le goulot en le déménageant : la validation est passée du labo qui possède le modèle aux mainteneurs qui possèdent les packages.

Si tu as suivi cette série, tu reconnais la forme. C'est le pattern Gheist inversé, le pattern Postman à l'échelle industrielle : un acteur avec plus de compute que de consentement expédie sa sortie dans les queues des autres et appelle ça un cadeau. Quand la queue est ton CI, ça vole des secrets ; quand la queue est ta boîte mail de mainteneur, ça vole quelque chose de plus rare, l'attention de triage, et les chiffres curl disent que plus de la moitié de ce qui est volé est du bruit.

Il y a aussi un vrai dilemme à énoncer honnêtement, parce que les takes faciles sont faciles : l'alternative à une divulgation automatisée imparfaite, ce n'est pas une divulgation humaine parfaite, c'est *moins* de divulgation. Les 51 critiques de la liste créditée incluent de vraies prises de memory-safety dans du logiciel de classe curl. Personne de sensé ne veut la machine éteinte. La demande est plus petite et plus dure : **validé avant expédition, sévérité honnêtement classée, un rapport par vrai bug, et l'organisation qui trouve paie le coût de triage jusqu'à confirmation du rapport**. Le montage actuel a un labo qui récolte des crédits CVE pendant que des bénévoles font le contrôle qualité.

## Checke ta stack ce soir

```bash
git clone --depth 1 https://github.com/patrickmgarrity/Anthropic-Credited-CVEs
cd Anthropic-Credited-CVEs

# tes dépendances sont-elles dans la liste créditée ?
grep -l -iE "product: (curl|linux|firefox|wolfssl|libreoffice|filelock)" cves/*.yaml | wc -l

# quelque chose de critique ?
grep -l "^cvss: '9" cves/*.yaml | wc -l
for f in $(grep -l "^cvss: '9" cves/*.yaml); do grep -H "^cve:\|^product:" $f; done

# recoupe les deux exploitées-connues avec ton environnement
grep -A2 "CVE-2026-61500\|CVE-2026-26980" cves/*.yaml
```

Mon run de ce soir : les deux entrées KEV sont là, les critiques se concentrent dans du code exposé au réseau (le 9,2 d'iperf3 vient des propres fichiers du tracker), et 78 % de la liste porte `auto_discovered: true`, donc si tu maintiens un package OSS, considère ta boîte mail comme le prochain front et écris ta politique de triage maintenant : ce que tu rejettes, ce que tu escalades, et la phrase que tu utiliseras pour les rapports non sollicités générés par machine.

## TL;DR

Le tableau de bord audité de Glasswing : 37 966 findings, 217 corrigés, 1 654 doublons, 2 exploités dans la nature, et un scanner qui externalise la validation vers les mainteneurs avec des rapports modèle-seul ; l'expérience curl (45 rapports) montre une majorité de bruit sous une claim de « 94 % de vrais positifs ». Le tracker public (450 CVEs créditées ce soir, octobre le mois pic) se questionne en un clone, et c'est la façon honnête de répondre à « ma stack est-elle touchée » sans le communiqué de presse. L'ère de la découverte à vitesse machine est là ; l'audit dit que la facture est payée par les mauvaises personnes.

Sources : [VulnCheck : Tracking Anthropic-discovered vulnerabilities, November update](https://www.vulncheck.com/blog/anthropic-glasswing-november-update) · [le tracker (patrickmgarrity/Anthropic-Credited-CVEs)](https://github.com/patrickmgarrity/Anthropic-Credited-CVEs), stats recalculées ce soir · [ledger Anthropic](https://red.anthropic.com) · recoupement KEV : CVE-2026-61500, CVE-2026-26980
