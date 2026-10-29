---
titre: "Le CA dont la clé privée valait 4 vient de quitter le business des certificats"
date: 2026-10-23
themes: securite, pki
resume: "Cinq jours après l'histoire de la clé valant 4, le conseil d'eMudhra vote la sortie du business mondial SSL/TLS, en blâmant l'« amplification des réseaux sociaux ». Le même jour, un contournement complet du 1FA OTP surfacait. La suite de : une clé privée de CA valait 4."
source: https://dev.to/slabb/the-ca-whose-private-key-was-the-number-4-just-quit-the-certificate-business-18ba
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fi91c1batadm1msdi4rmm.png
image_alt: "Le CA dont la clé privée valait 4 vient de quitter le business des certificats"
---

> Mardi, on te montrait l'autorité de certification dont la clé privée intermédiaire valait **littéralement 4**, récupérable en quatre essais, valide jusqu'en 2040, chainée à des racines que toutes les grandes plateformes trustworthy. Aujourd'hui, le conseil d'administration d'eMudhra a répondu : l'entreprise **quitte entièrement le business mondial des certificats SSL/TLS**. Et dans un twist que personne n'avait commandé, le même jour a surfacé un **contournement complet du login OTP à un facteur de leur portail de certificats**. Cinq jours de la compromission de clé à la sortie de marché, voilà à quoi ressemble l'industrie de la confiance quand tous ses mécanismes d'exécution partent en même temps.

C'est l'acte deux de [l'article de mardi](https://dev.to/slabb/a-ca-private-key-was-the-number-4-your-curl-still-trusts-it-cve-2026-111943-45o4). L'acte un, c'était la cryptographie ; l'acte deux, c'est l'économie et la réputation, et l'économie était déjà écrite avant que l'incident commence.

## Ce que le conseil a vraiment dit

Le [communiqué](https://emudhra.com/en/press-release/emudhra-to-exit-global-ssl-tls-certificate-business) (22 oct) est un document fascinant, parce qu'il fait trois choses à la fois :

**Il revendique la diligence.** M. V. Srinivasan, président : les intermédiaires affectés révoqués « dans les 14 heures suivant la découverte », divulgation rapide, **aucun certificat end-entity émis depuis les CAs affectées**, infrastructure non compromise, aucune donnée violée.

**Il avoue l'économie.** Le SSL/TLS global, c'est **environ 1 % du revenu d'eMudhra**. Les exigences de souveraineté des données et de conformité font monter le coût d'exploitation d'une CA publique, et, l'éléphant sans nom, *« some of the large entities issue the SSL/TLS free of cost »*. Quand ta concurrence donne le produit, une CA payée à 1 % du revenu est une erreur d'arrondi avec un fardeau d'audit.

**Il blame l'amplificateur.** La phrase qu'on citera pendant des années : *« the level of **social media amplification** around this incident has brought **scrutiny that is out of proportion** to SSL/TLS's place »* dans le business.

Garde cette phrase en tête.

## Les deux mécanismes ont fait leur travail

Ce qui s'est passé cette semaine, c'est le marché de la confiance fonctionnant par ses deux couches d'exécution, dans l'ordre :

1. **La couche technique, rapide** : Mozilla, Apple, Microsoft et Chrome ont bloqué les intermédiaires compromis en trois jours après la divulgation de Wayne (17 → 20 oct). Personne n'avait besoin d'agir ; les navigateurs ont juste cessé de faire confiance à la chaîne. On a vérifié nous-mêmes les trous qui restent, le `curl` macOS stock trust toujours les deux chemins, mais le tissu des navigateurs a tenu.
2. **La couche réputation, plus lente et brutale** : cinq jours plus tard, le conseil sort du business. Pas à cause des clés, à cause des clés qui ont fait regarder tout le monde un business déjà moribond : 1 % du revenu, contre des concurrents gratuits, sous des coûts de conformité croissants.

Les deux sont vrais en même temps : **eMudhra a géré l'incident de manière compétente, et la sortie était inévitable**. L'incident n'a pas cassé le business ; il a avancé l'annonce d'un an ou deux. Et « géré compétemment » a un plafond très dur en confiance publique, à cause de ce que le président a dit ensuite.

## « Une surveillance sans proportion »

Une autorité de certification n'est pas dans le business des certificats. Elle est dans le business de la **surveillance proportionnée** : tout le produit, c'est un système où la surveillance appliquée à « est-ce vraiment ma banque ? » est exactement aussi forte que le tort de se tromper. N'importe qui peut exiger une preuve à tout moment, c'est le deal.

Alors quand le président se plaint que l'amplification a apporté une surveillance *sans proportion* avec la place du business dans le revenu, il décrit le produit qui fonctionne comme prévu. La part de revenu d'une CA est sans rapport avec la surveillance qu'elle mérite ; sa **part de confiance** est ce qui compte, et les intermédiaires d'eMudhra se chainaient à des racines présentes dans chaque trust store majeur de la planète. La surveillance était de la taille de tout le monde parce que la confiance était de la taille de tout le monde. Si tu veux une surveillance proportionnée à ton revenu, vends autre chose, ce qui, soyons justes, est exactement ce que le conseil vient de décider.

## Le même jour : un contournement complet du 1FA OTP

Pendant que le communiqué sortait, un chercheur [divulguait sur Mastodon](https://mastodon.catgirl.cloud/@49016/117475976434068995) ce qu'il présente comme un contournement complet du login OTP à un facteur d'eMudhra, ses mots : *« tu peux littéralement dépouiller n'importe quel certificat emudhra existant avec ça, en OSINTant juste l'email associé et en te loggant »*.

Formulation prudente, parce que c'est une divulgation unique que nous n'avons pas reproduite : pas encore de write-up avec les étapes, et pas de réponse du vendor à l'heure d'écrire. Mais c'est la *catégorie* qui compte plus que les détails : la compromission de clé était contenable par les root programs en 72 heures, ils n'ont pas besoin de la coopération d'eMudhra. Un chemin de takeover vers le **portail d'émission en production**, c'est la forme inverse : une compromission de système métier, que ni la révocation ni le blocage des trust stores n'atteignent. Un incident était un problème de cryptographie ; l'autre serait un problème d'identité. eMudhra quitte le premier sur une bonne semaine.

## Le lab : la claim que tu ne peux pas vérifier, par design

Voici la boucle qui se ferme. La claim centrale de diligence du président : **aucun certificat end-entity émis depuis les intermédiaires affectés**.

Tu peux la vérifier ? Non, et la raison est exactement le fait qui a sauvé les navigateurs lundi : **ces intermédiaires n'ont jamais été dans les logs Certificate Transparency**. Zéro entrée CT sur toute leur vie de 18 mois. Donc :

```bash
# recherche crt.sh de l'intermédiaire affecté, ne renvoie rien,
# PAR CONSTRUCTION : un intermédiaire non loggé ne peut pas avoir de feuilles comptables
curl -s "https://crt.sh/?identity=EM%20OV%20TLS%20CA%20-%20G3C" | grep -c "<TR>" || echo "0 rows"
```

L'absence de preuve ici est structurelle, pas disculpatoire. « Aucun certificat end-entity » est invérifiable de l'extérieur *parce que* la CA a sauté le seul log public qui l'aurait rendu vérifiable. Le même choix de design qui a protégé les navigateurs des certificats forgés protège aussi l'historique d'émission de la CA de l'audit public. Vérifier cette claim exige les registres internes d'eMudhra, c'est-à-dire faire confiance à la CA. La seule chose que cette semaine nous a appris à pricer correctement.

(Ta machine, pendant ce temps, trust toujours la famille : le one-liner d'hier montre encore le `curl` macOS stock se connectant joyeusement aux serveurs de test officiels. Le workaround `cert.pem` de l'article de mardi reste pertinent jusqu'à ce que le bundle sorte.)

## Ce qui change vraiment pour les utilisateurs

Les root programs ne suppriment pas une CA du jour au lendemain quand elle sort volontairement, les certificats eMudhra/emSign existants brûlent vers leur notAfter avec un sunset communiqué, et les clients migrent vers une autre CA (et après cette semaine, « une autre CA » vient maintenant avec une question de due diligence : *montre-moi ta cérémonie de génération de clés*). Le geste pratique pour quiconque tient un certificat émis par emSign aujourd'hui : n'attends pas le sunset. Réémmets depuis une CA dont les intermédiaires se trouvent dans les logs CT. Toute la leçon de la semaine en une ligne d'achat.

## TL;DR

Mardi : la clé de la CA valait 4. Vendredi-mercredi : bloquée par tous les root programs. Aujourd'hui : le conseil quitte le business, cite les concurrents gratuits et 1 % du revenu, et blame l'amplification, et un bypass 1FA tombe le même jour. Le système a fonctionné aux deux étages ; la surveillance était exactement aussi proportionnée que la confiance vendue. Et la seule claim que tu voudrais vérifier est invérifiable par design, parce que la CA n'est jamais entrée dans le log public.

Sources : [communiqué eMudhra](https://emudhra.com/en/press-release/emudhra-to-exit-global-ssl-tls-certificate-business) · [Partie 1, Une clé privée de CA valait 4](https://dev.to/slabb/a-ca-private-key-was-the-number-4-your-curl-still-trusts-it-cve-2026-111943-45o4) · [divulgation du bypass 1FA OTP](https://mastodon.catgirl.cloud/@49016/117475976434068995) · [site de divulgation officiel](https://emudhra.we-have-a-problem.com/)
