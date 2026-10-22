---
titre: "Six failles kernel non patchées viennent de fuir sur une liste de diffusion publique"
date: 2026-10-22
themes: securite, linux
resume: "Cette nuit, six rapports ZDI — dont deux RCE réseau CVSS 9.0 dans le serveur SMB du kernel, non patchées en mainline — sont arrivés sur la LKML publique au lieu de la liste privée. Réponse de Greg Kroah-Hartman : « For some reason you sent this to public lists, and did not include a patch. » Le lab : ta flotte est-elle exposée ?"
source: https://lore.kernel.org/lkml/BYAPR01MB3830472B5702C089B0BBB77D80662@BYAPR01MB3830.prod.exchangelabs.com/
image: https://blog.slabb.dev/img/six-unpatched-linux-kernel-leak.png
image_alt: "Six rapports ZDI — dont deux RCE KSMBD CVSS 9.0 — fuient sur la LKML publique : la boîte d'envoi, Tux, et le triage du port 445"
---

> Cette nuit, la machine de divulgation coordonnée du kernel Linux s'est cassée de la manière la plus banale qui soit : **ZDI (Trend Micro) a envoyé six rapports de vulnérabilités sur la LKML publique** — la liste archivée, lisible par le monde entier — au lieu du canal privé prévu. Deux d'entre elles sont des **RCE réseau CVSS 9.0** dans le serveur SMB du kernel, **non patchées en mainline**. Greg Kroah-Hartman, le numéro deux du kernel, a répondu à chacune : *« For some reason you sent this to public lists, and **did not include a patch**, so there's not much we can do with this. »*

Ce n'est pas une histoire de vulnérabilité kernel. C'est une histoire de **pipeline de divulgation** — et c'est la deuxième de la semaine. Voici ce qui a fuité, pourquoi la fenêtre est ouverte là maintenant, et un triage de deux minutes pour ta propre flotte.

## Ce qui est public maintenant

Six rapports de `zdi-disclosures@trendmicro.com`, postés cette nuit (21 oct, 21h16 UTC et après), posés dans l'archive lore.kernel.org pour tout le monde :

| Réf ZDI | Bug | Classe | Sévérité |
|---|---|---|---|
| ZDI-CAN-33549 | KSMBD SMB Direct | **Exécution de code à distance** (réseau) | **9.0** |
| ZDI-CAN-33774 | KSMBD race condition | **Exécution de code à distance** | **9.0** |
| ZDI-CAN-33367 | skbuff `skb_zerocopy` | élévation de privilèges locale | high |
| ZDI-CAN-34068 | vmwgfx dirty tracking | écriture out-of-bounds → LPE | high |
| ZDI-CAN-34076 | NVMET | ressource non initialisée → fuite d'info | medium |
| ZDI-CAN-32005 | requête TCP search-domain | stack buffer overflow → LPE | high (postée la veille) |

La pièce maîtresse, [ZDI-CAN-33549](https://lore.kernel.org/lkml/BYAPR01MB3830472B5702C089B0BBB77D80662@BYAPR01MB3830.prod.exchangelabs.com/), est une beauté — et ça se lit comme une visite guidée. La cible : le serveur SMB du kernel (KSMBD) sur SMB Direct ; le bug : un underflow entier de deux lignes :

```c
desc_buf += desc_buf_len;
buf_len -= desc_buf_len;   // (2) integer underflow, leads to heap overflow
                           //     within rxe_mr_copy()
```

En dessous : la sortie KASAN exacte (`slab-out-of-bounds in rxe_mr_copy_dma`, écriture de 1024 octets), la version testée (7.3-rc3), la plateforme (Debian trixie), et les clés de config pour rendre la faille atteignable (`CONFIG_SMB_SERVER_SMBDIRECT=y` + `CONFIG_RDMA_RXE=y` — note que `rdma_rxe` est du RDMA *logiciel* : pas besoin de matériel exotique). Prérequis selon le rapport : un device RDMA, un partage en écriture, SMB Direct activé.

Tout ce qu'il faut à un tiers pour partir de l'analyse au lieu de la classe de bug. Le patch, d'après Phoronix, dormait dans une branche prévue pour **v7.5** — désormais probablement accéléré.

## Pourquoi la fenêtre est ouverte *là maintenant*

La mathématique d'un rapport non patché qui fuite :

1. **Aujourd'hui**, n'importe qui lit l'analyse complète — fonction vulnérable, trace de crash, config cible. Le fix n'est dans aucune release stable.
2. **Quand le patch arrive** dans linux-next (il est accéléré), le diff du commit devient le guide terrain de l'exploit : un `git log` et toute la surface de fuzzing se réduit aux lignes exactes qui ont changé.
3. **Jusqu'à ce qu'une stable sorte**, des flottes tournent sur un kernel dont les plans des trous connus sont publics.

KSMBD rend ça pire qu'un driver quelconque : c'est le **serveur SMB dans le kernel**, à l'écoute sur le 445, un sous-système qui a déjà passé 2022-2023 sur la liste des criminels de la sécurité avec sa propre série de RCE et des débats publics sur sa place en mainline. Un 445 exposé sur internet + un plan de RCE 9.0 public, c'est le genre de combinaison que les équipes ops n'ont pas le droit d'ignorer.

Et la réponse de Greg KH nomme la deuxième défaillance : **les rapports n'avaient pas de patch**. Les mainteneurs n'ont rien d'actionnable ; les attaquants ont tout. C'est le pire des deux côtés d'une divulgation.

## Triage ta flotte en deux minutes

Les rapports donnent leurs propres configs. Vérifie les tiennes :

```bash
# Le serveur SMB in-kernel est-il chargé ?
lsmod | grep ksmbd

# Quelque chose écoute sur le SMB (445) ?
ss -tlnp | grep ':445 '

# SMB Direct était-il compilé — et le RDMA logiciel (le rxe du bug) est-il actif ?
grep -E 'SMBDIRECT|INFINIBAND_USER' /boot/config-$(uname -r) 2>/dev/null
lsmod | grep rxe

# VM VMware ? Le rapport vmwgfx parle de ton driver graphique.
systemd-detect-virt
```

Si `ksmbd` n'est pas chargé et que rien n'écoute sur 445, les RCE sont le feu de quelqu'un d'autre aujourd'hui — mais la LPE skbuff (locale, via le cœur réseau) concerne à peu près tout le monde, donc la vraie tâche est celle que le kernel demande toujours : **sois à jour sur tes point releases stables cette semaine**, parce que les patchs accélérés prendront le prochain train. Surveiller [le thread lore](https://lore.kernel.org/lkml/BYAPR01MB3830472B5702C089B0BBB77D80662@BYAPR01MB3830.prod.exchangelabs.com/) est le meilleur système d'alerte précoce gratuit.

(Petit joke d'internet au passage : lore.kernel.org est derrière **Anubis**, le portail proof-of-work conçu pour tenir les scrapers IA à distance. Le mur anti-bot du kernel fait maintenant écran devant des rapports de zéro-days — il te faut un vrai navigateur pour lire les fuites.)

## La partie qui compte dès vendredi

Cette semaine nous a livré le test A/B de la discipline de divulgation, dans les mêmes sept jours :

- **eMudhra** (lundi) : une clé de CA compromise signalée par le *bon canal privé*, avec preuves cryptographiques, corrigée et bloquée par tous les root programs en trois jours. Le manuel.
- **ZDI** (cette nuit) : six rapports non patchés dans l'archive *publique*, sans patch attaché, une campagne de mails mal adressée depuis un expéditeur Exchange Online — `exchangelabs.com` — et le numéro deux du kernel qui dit, en public, *« there's not much we can do with this »*.

Même industrie, même semaine, même classe d'actif. La variable n'a jamais été la qualité des vulnérabilités ; c'est le **pipeline** — l'adressage, le patch attaché, le process qui fait passer un rapport du privé au public *après* l'existence du fix. Un canal de divulgation est de l'infrastructure de sécurité, et cette nuit il a échoué comme l'infrastructure échoue : une table de routage que personne n'a relue, une pièce jointe que personne n'a attachée.

On arrive toujours à la même conclusion sous un autre angle — la plomberie du gardien est la surface d'attaque. Cette fois ce n'était pas un agent qui réécrivait ses logs ; c'était un client mail avec la mauvaise ligne To:.

## TL;DR

Six rapports ZDI, dont deux RCE KSMBD CVSS 9.0, ont fuité sur la LKML publique cette nuit — non patchés, analyse complète, archivés pour toujours. La réponse de Greg KH résume tout : pas de patch attaché, rien à faire. Triage ton exposition 445 aujourd'hui, sois à jour sur les kernels stables cette semaine, et surveille l'arrivée des commits de fix — parce qu'au moment où ils tombent, le diff dit à tout le monde exactement où étaient les trous.

Sources : [ZDI-CAN-33549 sur lore.kernel.org](https://lore.kernel.org/lkml/BYAPR01MB3830472B5702C089B0BBB77D80662@BYAPR01MB3830.prod.exchangelabs.com/) · [Réponse de Greg KH](https://lore.kernel.org/dri-devel/2026102254-protector-seventy-6454@gregkh/) · [Phoronix : LKML New Trend Vulnerabilities](https://www.phoronix.com/news/LKML-New-Trend-Vulnerabilities)
