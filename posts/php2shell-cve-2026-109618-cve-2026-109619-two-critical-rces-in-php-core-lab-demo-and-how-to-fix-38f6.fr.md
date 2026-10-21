---
titre: "php2shell : deux RCE critiques dans le cœur de PHP — démo en labo et correctif"
date: 2026-10-21
themes: securite, php
resume: "Deux RCE corrigées en urgence dans le cœur de PHP — php2shell, 9,2/10, toutes les versions depuis la 5.4 potentiellement exposées. La fuite, le patch avancé, la démo en labo, et le correctif."
source: (T0: URL dev.to après publication)
image: (T0: og:image dev.to après publication)
image_alt: "php2shell : deux RCE critiques dans le cœur de PHP, démo en labo et correctif"
---

Deux vulnérabilités d'exécution de code à distance viennent d'être corrigées en urgence dans le **cœur de PHP** : CVE-2026-109618 et CVE-2026-109619, CVSS v4.0 **9,2/10** chacune, surnommées **php2shell**. Elles touchent potentiellement toutes les versions de PHP depuis la 5.4 — celle de 2012. Les détails ont fuité avant l'embargo, PHP a avancé sa release de sécurité, et on montre tout en labo : la surface d'attaque, la démonstration, et surtout le correctif.

⚠️ Le labo complet (Docker, harness de course, preuve A/B AddressSanitizer) vit ici : **[T0: lien repo — à passer en public avec l'article]**. Cible locale uniquement, jamais dirigée vers des systèmes tiers — et le PoC est construit à partir du diff officiel au moment de la release, pas à partir de l'outil qui a fuité.

## Chronologie d'une fuite

- **20 oct, matin** : un « Tell HN » (supprimé depuis) révèle deux RCE PHP notées CVSS 10,0. Les screenshots filent sur X et Mastodon, les identifiants CVE réservés sont cités.
- **20 oct** : watchTowr confirme publiquement que les failles sont réelles. PHP publie un préavis : CVSS v4.0 9,2 chacune, release de sécurité le 21 octobre à 14h00 UTC — avancée d'un jour précisément parce que les détails ont fuité.
- **21 oct** : une vidéo d'exploit « php2shell » (créditée Calif.IO) et un PoC circulent brièvement avant d'être retirés. Aucune exploitation sauvage confirmée à l'heure d'écriture (Huntress), mais Sansec table sur une exploitation de masse dans les minutes suivant la publication du patch.

## La surface d'attaque

<!-- [T0: remplacer par l'analyse du diff officiel. Ci-dessous : connaissances publiques au moment de la fuite.] -->

Les détails techniques qui ont filtré dans la couverture de la fuite décrivent **« deux primitives de use-after-free dans le gestionnaire `session.upload_progress` de PHP »**.

Ce qui rend ça sérieux : `session.upload_progress.enabled` est **activé par défaut** sur quasiment toutes les installations PHP depuis la 5.4. Ce qui colle parfaitement avec la claim de l'outil leaké : *« works against every PHP release from 5.4.0 on »*.

On a vérifié cette surface en labo. Un simple POST multipart avec un champ `PHP_SESSION_UPLOAD_PROGRESS=<clé>` fait écrire au serveur une entrée entièrement contrôlée par l'attaquant dans **son propre store de session** :

```text
array (
  'upload_progress_fastkey' =>
  array (
    'start_time' => 1792574947,
    'content_length' => 7284,
    'bytes_processed' => 7284,
    'done' => true,
    'files' => array ( ... ),
  ),
)
```

C'est la fonctionnalité officielle de barre de progression d'upload — personne ne l'active, personne ne la désactive, personne ne la surveille. Et c'est une course permanente entre le streaming de l'upload et le cycle de vie de la session. Exactement là où vivent les use-after-free.

<!-- [T0: démo complète ici — PoC, sortie ASAN sur le build vulnérable, run propre sur le build patché] -->

## La démo en labo

Setup : nginx + php-fpm 8.4 (images Docker digest-pinnées **avant la release**), et un harness Python qui envoie un upload multipart ralenti en raw socket pendant qu'un deuxième flux perturbe le cycle de vie de la session (destruction, régénération, GC, double upload, abort client).

<!-- [T0: résultats A/B — le UAF prouvé par ASAN sur le build vulnérable, le même harness qui reste propre sur le build patché. C'est une démonstration, pas une théorie.] -->

## Qui est exposé

- **Tout serveur web PHP non patché** : php-fpm, mod_php, cgi. Pas besoin de compte, pas besoin d'endpoint applicatif vulnérable — le bug est dans le cœur, et l'exploit se termine avant même que votre code applicatif tourne. Les WAF applicatifs ne voient rien.
- **Les branches end-of-life (≤ 8.2) n'auront pas de correctif officiel** : une grosse partie du web doit migrer ou compter sur les backports des distros.
- [T0: versions patchées exactes par branche 8.3.x / 8.4.x / 8.5.x]

## Le correctif, étape par étape

1. **Inventorier** tout ce qui tourne en PHP, y compris les PHP embarqués (applis qui vendent leur propre `php.exe`, cPanel/Plesk, containers oubliés) :
   ```bash
   php -v
   php -i | grep -i 'upload_progress.enabled'   # On = surface active (défaut depuis 5.4)
   ```
2. **Mettre à jour** vers la release corrigée de votre branche :
   <!-- [T0: commandes distro — apt/dnf/alpine/brew, versions cibles exactes] -->
3. **Branches EOL** : migrer vers une branche supportée est la seule vraie réponse. En attendant : isolation réseau plus détection renforcée (ci-dessous).
4. **Hébergement managé ou mutualisé ?** Ouvrez le ticket *maintenant* — demandez à votre fournisseur exactement quand ils déploient les paquets corrigés et pour quelles branches. « Bientôt » n'est pas une réponse.
5. ⚠️ **`session.upload_progress.enabled=Off` n'est PAS un correctif.** C'est une mitigation partielle que la couverture publique dit insuffisante — les release managers PHP ont été explicites : le patch est obligatoire.

## Détecter une tentative

Surveillez les **enfants anormaux des workers PHP** : un `php-fpm` qui spawn `sh`, `bash`, `nc`, `curl` ou `python`, c'est déjà trop tard — mais c'est le signal. Un tri rapide sur n'importe quelle boîte :

```bash
pstree -p | grep -A2 php-fpm    # tout ce qui pend à un worker et qui n'est pas un socket = regarder de plus près
```

Patterns de reverse-shell dans les lignes de commande : `/dev/tcp/`, `mkfifo`, `fsockopen`. Sur les serveurs Linux non surveillés, un process-watcher gratuit en mode observe vaut mieux que rien en attendant une vraie EDR.

<!-- [T0: règles Sigma/YARA officielles (Huntress huntresslabs/threat-intel) + IOC publiés] -->

## TL;DR

Patchez aujourd'hui, pas demain. L'analyse complète du diff, le PoC et les preuves sont dans le repo du labo : **[T0: lien]**.

Sources : [préavis officiel php.net](https://www.php.net/archive/2026.php#2026-10-20-1) · [watchTowr](https://watchtowr.com/intelligence/php-cve-2026-109618-faq) · [Huntress](https://www.huntress.com/blog/php2shell-leaked-critical-php-vulnerabilities) · [Sansec](https://sansec.io/research/php2shell) · [CERT-EU 2026-018](https://cert.europa.eu/publications/security-advisories/2026-018) · [T0: notes de release officielles & pages d'upgrade pour 8.3 / 8.4 / 8.5]
