---
titre: "Le matelas dépendant d'internet a un mode recovery : rooter l'Eight Sleep Pod 3 avec un quirk de GNU tar"
date: 2026-11-16
themes: securite, iot
resume: "Tiens un bouton, branche l'alim, et le Pod 3 boote depuis la SD et se reflashé lui-même avec GNU tar. Comme tar garde la copie d'après quand une archive contient deux fois le même chemin, ajouter trois fichiers au rootfs d'usine donne le root permanent, tue les services de mise à jour, et libère le matelas de son cloud. Le writeup, la démo tar de 30 secondes, et pourquoi les partitions de recovery sont la nouvelle porte d'entrée."
source: https://dev.to/slabb/the-internet-dependent-mattress-has-a-recovery-mode-rooting-the-eight-sleep-pod-3-with-a-gnu-tar-3hi4
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fsitx8drlp4009gej4m6u.png
image_alt: "Le matelas dépendant d'internet a un mode recovery : rooter l'Eight Sleep Pod 3 avec un quirk de GNU tar"
---

> L'Eight Sleep Pod 3 est un surmatelas avec pompes à eau, une carte Yocto Linux (NXP i.MX8M Mini sur un module Variscite DART), et un business model : il veut un abonnement, et la panne AWS de l'an dernier avait laissé des propriétaires incapables de régler leurs propres lits. Le [writeup de rooting de Ryan Bagley](https://rb.ax/blog/rooting-the-eight-sleep-pod-3/) de cette semaine referme cette histoire avec ma primitive d'exploitation préférée du mois : **la règle des doublons de GNU tar**. Le flux de recovery d'usine déverse `rootfs.tar.gz` sur l'eMMC de l'appareil avec du `tar` simple, et « quand une archive contient deux fois le même chemin, GNU tar garde la copie d'après ». Ajoute trois petits fichiers à l'archive, et ce qu'ils contiennent devient le système. Pas d'UART, pas de glitching, pas de chaîne d'exploits : le propre mode de réparation de l'appareil respecte la sémantique de tar plus qu'il ne respecte son propriétaire.

## La chaîne, en quatre mouvements

1. **Ouvre le boîtier** (plusieurs clips en plastique meurent), retire la carte SD. Sous une carte fille se cache le connecteur que le manuel ne mentionne jamais.
2. **Sauvegarde la carte, patche l'archive.** Sur macOS, `dd` la carte, puis travaille dans l'image avec `debugfs` d'e2fsprogs (sans montage). Le payload, c'est trois changements ajoutés à `rootfs.tar.gz` : une nouvelle clé SSH dans `etc/ssh/authorized_keys`, un fichier sudoers (`rewt ALL=(ALL) NOPASSWD: ALL`), et quatre symlinks vers `/dev/null` pour les unités systemd liées aux mises à jour, dont `swupdate` et une unité nommée sincèrement **`defibrillator.service`**.
3. **Le tour de tar.** Comme le flux de recovery extrait avec GNU tar, les doublons ajoutés écrasent les originaux sans toucher au reste de l'archive d'usine. Pas de repack de gigaoctets, pas de chirurgie de checksum : trois fichiers, ajoutés.
4. **Factory-reset via le bouton de boot**, et le flux de recovery fait le reste : il écrit ton rootfs patché sur l'eMMC et reboote dessus. `ssh -p 8822 rewt@POD_IP`, `sudo -i`, terminé. L'auteur a ensuite installé le stack open source **free-sleep** : une UI web locale sur le port 3000, des commandes de pompes en **moins d'une seconde** (contre les lenteurs du round-trip cloud), et un lit qui continue de marcher quand internet tombe.

Les commandes complètes sont dans le post ; la méthode s'appuie sur le projet free-sleep et l'article ZeroSleep de Bo Lopker. Le cadrage du risque de l'auteur est honnête : avec les services de mise à jour neutralisés, « si quelque chose va mal, tu es seul », un trade qu'il préfère à un matelas dépendant du cloud de quelqu'un d'autre.

## Le lab de 30 secondes : tar comme primitive de rooting

C'est la partie que n'importe qui peut lancer ce soir, sans hardware, et je l'ai tournée pour ce post. Chemins dupliqués, même archive, la copie d'après gagne :

```bash
mkdir -p a/etc c/etc out
echo "original: cloud-locked" > a/etc/config
echo "patched: ssh key + sudoers + /dev/null units" > c/etc/config

tar cf rootfs.tar -C a etc      # l'archive d'usine
tar rf rootfs.tar -C c etc      # AJOUT du MÊME chemin

tar tvf rootfs.tar              # le chemin est littéralement présent deux fois :
# -rw-r--r-- 23 ... etc/config
# -rw-r--r-- 45 ... etc/config

tar xf rootfs.tar -C out && cat out/etc/config
# patched: ssh key + sudoers + /dev/null units
```

Ma sortie, non éditée : le listing montre les deux entrées (23 octets, puis 45), et l'extraction écrit la copie de 45 octets. C'est toute la primitive : **tout pipeline qui extrait un tarball en opération privilégiée, sans vérifier que l'archive est sans doublons, a une primitive d'écriture root dans son chemin de recovery**. Le fix est à un flag : `--occurrence=1`, ou un check explicite de doublons, ou signer l'archive et la vérifier avant extraction, et le fait que ça marche encore sur du hardware grand public en 2026 te dit à quel point ce check est rare.

## Pourquoi ça reste notre sujet

Les habitués reconnaissent le pattern ; ce trimestre en a fait une tournée :

- Les **frigos de supermarchés** sont tombés par des interfaces web publiques avec des mots de passe à la date du jour : le plan de gestion à distance que personne n'a sécurisé.
- La **clé USB « chiffrée » Lenovo** était du théâtre : pas de crypto, juste un verrou en forme d'empreinte.
- L'histoire de la **machine à broder** était le même combat d'ownership avec un abonnement boulonné, et la communauté a répondu avec une app ouverte.
- L'Eight Sleep tresse les deux fils : **un mécanisme de recovery qui est une interface de flash non authentifiée**, et **une dépendance cloud qui transforme l'ownership en bail**. Le boot de recovery qui trust toute carte SD insérée est le jumeau physique de « le listener qui accepte les messages des étrangers » ou « le parseur qui tourne avant la validation » : surface d'entrée de confiance, non authentifiée, livrée par défaut.

Et l'angle tar se généralise plus loin que les matelas : partitions de recovery, images de mise à jour vendor, layers de containers, restores de backup. Partout où un processus privilégié extrait une archive qu'il n'a pas construite, la règle des entrées dupliquées est une primitive d'écriture-n'importe-où, silencieuse, checksum-préservant par fichier, et invisible pour tout outil qui liste l'archive sans flagger les répétitions. Si tu shippes un tel pipeline, l'audit tient en une commande : `tar tvf image.tar | awk '{print $NF}' | sort | uniq -d` ne doit rien imprimer.

## Quoi faire avec celle-là

- **Propriétaires de Pod** : le writeup est complet et conservateur (backups, checksums, `debugfs` plutôt que des mounts), mais tu neutralises ton chemin de mise à jour ; lis les caveats de l'auteur et sache qu'un firmware futur peut changer le flux de recovery. La route free-sleep achète la vitesse, la localité et l'immunité aux pannes au prix d'être ton propre vendor.
- **Builders d'appareils** : signe tes images de recovery, vérifie avant extraction, rejette les entrées dupliquées, et fais exiger du boot de recovery une preuve de présence physique plus forte que « un bouton qui est aussi le bouton factory-reset ». Le flux du Pod a fait l'inverse de chacun de ces points.
- **Tout le monde** : lance le check de doublons ci-dessus sur chaque tarball que ton infrastructure extrait avec des privilèges. C'est l'audit supply-chain le moins cher que tu feras cette semaine, et le matelas de ce trimestre, c'est le routeur, le NAS ou le chargeur EV du prochain trimestre.

**TL;DR** : le mode de recovery de l'Eight Sleep Pod 3 boote depuis SD et reflashe l'eMMC avec GNU tar ; ajouter des chemins dupliqués au rootfs d'usine (la copie d'après gagne) plante des clés SSH, un sudo sans mot de passe et des services de mise à jour morts, de façon permanente, sans aucune attaque hardware. L'auteur tourne maintenant le stack open source free-sleep en local avec un contrôle des pompes en moins d'une seconde et zéro cloud. La démo tar de 30 secondes ci-dessus prouve la primitive sur n'importe quel laptop, et le check `uniq -d` d'une ligne appartient à chaque pipeline qui extrait des archives avec des privilèges. L'ownership d'un appareil que tu as payé ne devrait pas être un exercice de rooting, mais jusqu'à ce que les vendors se mettent d'accord, la partition de recovery est la porte d'entrée.

Sources : [Ryan Bagley : Rooting the Eight Sleep Pod 3](https://rb.ax/blog/rooting-the-eight-sleep-pod-3/) (méthode complète, commandes inline) · [throwaway31265/free-sleep](https://github.com/throwaway31265/free-sleep) (le stack de contrôle local) · manuel GNU tar, comportement des entrées dupliquées · démo tar et check de doublons reproduits en live pour ce post
