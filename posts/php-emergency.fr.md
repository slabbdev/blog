---
titre: "Un RCE 9.2 non authentifié dans PHP : l'audit, la fenêtre de patch, et l'interrupteur offline"
date: 2026-10-21
themes: securite, webdev
resume: "CERT-EU dit aux sites qui ne peuvent pas patcher de passer hors ligne : deux failles 9.2 dans PHP lui-même, RCE non authentifiée, toutes les versions depuis PHP 5 potentiellement touchées. L'audit, la surveillance, et l'interrupteur — des preuves exécutables pour la fenêtre d'urgence."
---

> Une agence cyber européenne dit aux sites web qu'ils pourraient devoir être mis **hors ligne**. Pas patchés plus tard. Pas surveillés. Hors ligne. Le runtime qui fait tourner WordPress, Drupal, Joomla, Magento et la majeure partie de l'hébergement mutualisé a deux failles notées 9.2 — exécution de code à distance non authentifiée — et le patch sort aujourd'hui à 14h00 GMT.

Mercredi, l'équipe sécurité de PHP publie les correctifs de **deux vulnérabilités critiques notées 9,2 sur l'échelle CVSS v4.0**. [Reuters rapporte](https://www.reuters.com/world/asia-pacific/eu-agency-warns-websites-may-need-be-taken-offline-php-prepares-patches-2026-10-21/) ce que les agences et les fournisseurs disent autour — et la version courte, c'est que c'est aussi grave qu'une urgence web puisse l'être :

- **CERT-EU** : la note 9,2 indique un risque d'**exécution de code à distance non authentifiée** — du code qui tourne sur votre serveur sans login. Leur consigne : préparez le patch immédiat, et **ceux qui ne peuvent pas patcher doivent prendre les sites concernés hors ligne**.
- **ACSC** (Australian Cyber Security Centre) : identifiez chaque système PHP de votre environnement, préparez les patches, surveillez les signes d'exploitation. Actuellement *pas au courant d'exploitation active* — actuellement.
- **GoDaddy** : les failles permettraient d'exécuter du code sur les serveurs depuis Internet — vol de données, défigurement, compromission totale.
- **Huntress** : « PHP est partout. Il fait discrètement tourner WordPress, Drupal, Joomla et Magento, les plateformes d'hébergement mutualisé, les panneaux de contrôle, et énormément de logiciels qui ne disent même pas qu'ils tournent en PHP sous le capot. »
- **Périmètre** : toutes les versions de **PHP 5 onward** pourraient être touchées. Les détails, versions affectées et versions corrigées publiés **quand le patch sort à 14h00 GMT aujourd'hui**.

Si ça sonne dramatique pour une release de langage, c'est que ça l'est — et ça doit l'être. Ce n'est pas un bug de plugin ni un cas limite de framework. C'est le runtime lui-même.

## Pourquoi ça casse le système de grading

Je grade les contrôles sur ce blog en niveaux : ce qu'un contrôle voit, qui l'a écrit, ce qu'il survit. Un contrôle de Level 1 est visible et contournable ; le post quiz-hook en était un. Le niveau en dessous, c'est le sol sur lequel les niveaux tiennent : **le runtime**. Vos règles WAF, votre validation d'entrée, votre checklist de hardening — tous sont du PHP qui exécute votre défense. Une RCE non authentifiée dans PHP, c'est une attaque sur le niveau qui décide ce que « exécuter » veut dire.

Lundi j'écrivais sur [la preuve de memory-safety de Rust](https://dev.to/slabb/the-11-year-old-premise-inside-rusts-memory-safety-proof-4804) — un trou de 11 ans exposant la prémisse sur laquelle la preuve repose. En voici l'image miroir : le langage serveur le plus déployé du web, dont le modèle de sécurité précède entièrement le modèle de menace moderne, qui appelle une fenêtre de patch d'urgence pendant qu'une agence européenne briefe l'interrupteur offline. Deux runtimes, deux philosophies, la même semaine — et les deux histoires sont la même histoire : **la prémisse fait partie de la preuve.**

## Exécutez chez vous : l'audit, la surveillance, l'interrupteur

Les détails de la vulnérabilité sont retenus jusqu'au patch — donc les preuves qui comptent maintenant sont celles de *votre* côté. Trois pipelines :

**1. L'inventaire — trouver chaque PHP sur les machines que vous contrôlez :**

```sh
# ce qui est installé (familles Debian/Ubuntu et RHEL)
dpkg -l | grep -E "php[0-9.]*-" | awk '{print $2, $3}'
rpm -qa | grep -E "^php" | sort

# ce qui s'exécute réellement, et depuis quand
php -v 2>/dev/null; php-fpm -v 2>/dev/null

# chaque binaire PHP sur disque, y compris ceux qu'un panel a installés il y a des années
sudo find / -name "php*" -type f -perm -111 2>/dev/null | grep -vE "/proc|/sys" | head -20
```

Cette dernière commande trouve le PHP 5.6 oublié dans un répertoire de panel que personne n'a touché depuis 2019 — exactement l'actif pour lequel l'avis du CERT-EU existe.

**2. L'exposition — ce qui fait face à Internet en ce moment :**

```sh
# sockets et pools php-fpm
ss -tlnp | grep -E "php|9000"
# chaque vhost qui route vers PHP
grep -rE "php|fastcgi" /etc/nginx/sites-enabled/ /etc/apache2/sites-enabled/ 2>/dev/null | wc -l
```

**3. La surveillance — jusqu'à ce que le patch sorte, les sondes d'exploitation sont votre tripwire.** Vous ne connaissez pas encore la signature, alors surveillez le volume et l'étrangeté :

```sh
# requêtes vers les endpoints PHP, dernière heure, avec codes de réponse
awk -v d="$(date -d '1 hour ago' '+%d/%b/%Y:%H:%M')" '$0 ~ d' /var/log/nginx/access.log \
  | grep -E "\.php" | awk '{print $1, $9}' | sort | uniq -c | sort -rn | head
```

Des pics de POST vers des chemins `.php` sur des sites sans formulaires PHP, ou des 200 sur des chemins qui devraient 404 — c'est votre « pas au courant d'exploitation active » qui devient « au courant ».

**4. L'interrupteur — quand le patch sort à 14h00 GMT :**

```sh
sudo apt update && sudo apt install --only-upgrade "php*"
sudo systemctl restart php8.3-fpm   # votre version
php -v                                # confirmer la nouvelle release
```

Et l'interrupteur offline que le CERT-EU briefe — pour les actifs impossible à patcher dans la fenêtre :

```sh
sudo systemctl stop php8.3-fpm
# servir une page de maintenance statique sans PHP dans le chemin :
# nginx : return 503 avec une racine de maintenance ; le runtime sort totalement du chemin de requête.
```

Arrêter `php-fpm` retire le runtime du chemin de requête — pas de PHP exécuté, pas de vulnérabilité PHP exécutée. C'est le contrôle le plus brut de ce post et le seul que le CERT-EU ait explicitement validé pour l'impatchable.

## Ce que vous en tirez

- **Une date limite** : 14h00 GMT aujourd'hui. Les détails arrivent avec le patch ; l'audit ci-dessus est tout ce que vous pouvez faire *avant* de les lire.
- **Un arbre de décision** : patchable dans la fenêtre → patcher et vérifier la version. Pas patchable → l'interrupteur offline, ou sortir l'actif du bord Internet. Vous ne savez pas si vous êtes exposé → les commandes d'inventaire existent exactement pour ça.
- **Les limites honnêtes** : rien dans ce post ne dit si vous êtes vulnérable à *ces* failles précises — PHP publie ça quand le patch sort. Ce que l'audit vous dit, c'est où chaque PHP vit, ce qui est le prérequis pour patcher en minutes au lieu de jours.

Et la note de prémisse, parce que c'est la même semaine : la memory safety du runtime n'est pas une propriété académique. Onze ans de preuve d'un côté, un avis offline d'une agence UE de l'autre. Le langage que votre serveur exécute *est* le fondement de votre surface d'attaque — tout ce qui est au-dessus, c'est de l'échafaudage.

Le patch sort à 14h00 GMT. L'audit prend dix minutes. Faites l'audit d'abord.

---

*Sources : [Reuters — EU agency warns websites may need to be taken offline as PHP prepares patches](https://www.reuters.com/world/asia-pacific/eu-agency-warns-websites-may-need-be-taken-offline-php-prepares-patches-2026-10-21/) (21 oct. 2026 — citant CERT-EU, ACSC, GoDaddy, Huntress, l'équipe sécurité PHP). Le cadrage runtime-as-premise suit [mon post Rust memory-safety](https://dev.to/slabb/the-11-year-old-premise-inside-rusts-memory-safety-proof-4804). Les commentaires dev.to de ce post seront mis à jour avec les détails CVE et les versions corrigées après la release de 14h00 GMT.*
