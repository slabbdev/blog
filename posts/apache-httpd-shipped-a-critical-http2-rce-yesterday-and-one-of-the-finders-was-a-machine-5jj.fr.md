---
titre: "Apache httpd a livré hier une RCE critique en HTTP/2, et un des finders était une machine : CVE-2026-119618 et l'audit trois portes"
date: 2026-11-12
themes: securite, web
resume: "Race mod_http2 dans assign_headers(), corruption de heap, RCE : 2.4.55 à 2.4.70 touchées, corrigé en 2.4.71 sorti hier. Les remerciements d'Apache créditent l'OSS Scanner d'Anthropic comme finder. Mon Mac tourne en 2.4.67, dans la plage, et l'audit trois portes explique pourquoi il est quand même à l'abri."
source: https://dev.to/slabb/apache-httpd-shipped-a-critical-http2-rce-yesterday-and-one-of-the-finders-was-a-machine-5jj
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2F11jiig095nautznwk511.png
image_alt: "Apache httpd RCE critique HTTP/2 : CVE-2026-119618 et l'audit trois portes"
---

> Hier, Apache a publié httpd 2.4.71 avec trois CVEs, dont une critique : **CVE-2026-119618, corruption de heap et RCE dans `mod_http2`**, une race condition dans `assign_headers()` déclenchée par des requêtes HTTP/2 concurrentes sur des ressources partagées. Touchés : **tous les httpd de 2.4.55 à 2.4.70**, et selon la télémétrie de Wiz, **64 % des environnements cloud contiennent une instance vulnérable et 51 % en ont une exposée publiquement**. Et le détail qui ferme une boucle ouverte par ce blog hier : dans les propres remerciements d'Apache, le premier finder listé est **« Anthropic's OSS Scanner, as vulnerability ANT-2026-MAPKT6MZ »**. Il y a vingt-quatre heures, cet espace auditait la courbe de bruit de ce scanner (curl : 45 rapports, 56 % rejetés). Aujourd'hui, son signal : une exécution de code à distance critique dans le serveur web le plus déployé de la planète. Les deux sont vrais, et c'est exactement le propos.

## La vulnérabilité, précisément

Depuis l'[advisorie officielle](https://httpd.apache.org/security/vulnerabilities_24.html) : une faille d'**exécution concurrente utilisant des ressources partagées avec synchronisation impropre** dans le `assign_headers()` de `mod_http2`. Plusieurs flux HTTP/2 frappant concurrent le chemin d'assignation des en-têtes peuvent corrompre la heap, et la corruption de heap dans un serveur preforké, c'est une primitive d'exécution de code. Les prérequis :

- **HTTP/2 activé** (le module chargé et `h2` dans la directive `Protocols`, directement ou via ALPN)
- versions **2.4.55 à 2.4.70** de httpd, ou les builds GitHub standalone de `mod_h2` 2.0.8 à 2.0.42
- corrigé en **2.4.71** (publié le 11 novembre) et mod_h2 au-delà de 2.0.42

Pas d'exploit public, pas d'exploitation observée dans la nature à ce jour. Avec un patch dehors, un serveur h2 exposé sur internet en version affectée vit maintenant un compte à rebours : l'advisorie, le writeup Wiz et le diff du fix sont publics, et l'histoire dit que l'armement des failles httpd se compte en jours-semaines, pas en mois.

La mitigation intérimaire si tu ne peux pas upgrader aujourd'hui tient en une ligne de `httpd.conf` : `Protocols http/1.1` (retirer `h2`/`h2c` des protocoles négociés ferme le chemin vulnérable au coût de la performance HTTP/2). Ce trade est presque toujours correct pour 48 heures.

## L'audit trois portes, lancé en live sur mon Mac

« Mon serveur est-il vulnérable » pour cette CVE, c'est le ET de trois conditions, et chacune tient en une commande. Mon laptop s'est révélé le cas d'école parfait : **son httpd est flaggé sur la version mais pas exploitable**, et voici la sortie complète, non éditée.

```bash
# PORTE 1 : la version (2.4.55 <= v <= 2.4.70 = flag)
$ httpd -v
Server version: Apache/2.4.67 (Unix)          # <- DANS LA PLAGE AFFECTÉE
Server built:   Oct  6 2026 20:57:44           # <- build embarquée par Apple

# PORTE 2 : le module vulnérable est-il seulement chargé ?
$ httpd -M | grep -i h2
(pas de sortie)                                # <- mod_http2 NON chargé

# PORTE 3 : h2 est-il négocié, et quelque chose écoute-t-il ?
$ grep -rn "^Protocols" /etc/apache2/httpd.conf # <- aucun h2 configuré
$ lsof -iTCP -sTCP:LISTEN -P | grep httpd       # <- n'écoute pas du tout
```

Verdict : flaggé sur la version, module absent, daemon idle : **non exploitable tel que configuré, patcher quand même à la prochaine maintenance**, parce que les configurations changent et que l'exposition d'hier n'est pas celle d'aujourd'hui. Note la fine print de la porte 1 pour les utilisateurs Mac : Apple embarque httpd et le build tard (ce 2.4.67 est sorti le **6 octobre**, cinq versions de retard en un mois), donc les serveurs macOS et les images CI qui héritent de `/usr/sbin/httpd` vont traîner derrière la 2.4.71 un moment. Brew ou une image container que tu contrôles battent le bundle.

Pour chaque hôte exposé que tu possèdes, ajoute la variante remote :

```bash
# ton site parle-t-il HTTP/2 ? (si oui ET serveur Apache en plage : agir)
curl -sI --http2 https://ton-site.example | head -1
# HTTP/2 200  -> h2 actif ; combiner avec la version pour conclure

# si tu exposes les server tokens, la version revient gratuitement :
curl -sI https://ton-site.example | grep -i server
```

## L'audit d'hier, le reçu d'aujourd'hui

Le post Glasswing d'hier se terminait sur l'économie : 37 966 findings, 217 corrigés, des mainteneurs enterrés sous des rapports générés par modèle dont la validation avait été externalisée par le labo. Cette CVE est l'autre colonne de ce ledger, sous sa forme la plus forte :

- Le finding était réel, critique, et dans LE serveur web : RCE par corruption de heap, pas une broutille basse sévérité (les six confirmations du cas curl étaient toutes low).
- Il a été **co-trouvé** : Apache crédite à la fois l'OSS Scanner d'Anthropic *et* des chercheurs indépendants (Anthony Weems, Simon Scannell). La machine était première sur la liste, les humains validaient le même terrain.
- Le pipeline de divulgation a fonctionné : coordonné, patché, advisorie avec crédits, fix dans une release normale.

Le ledger honnête après deux jours se lit donc : le flux du scanner est majoritairement du bruit au niveau du rapport individuel, et occasionnellement critique pour l'infrastructure. Les deux faits plaident pour la même conclusion tirée hier : **validé avant expédition, et l'organisation du finder porte le coût du triage**. Une machine qui trouve des RCE Apache httpd a gagné sa facture de compute. Un flux de 5 000 rapports non validés non, et la façon de les départager, ce n'est pas le marketing, c'est exactement ce genre de reçu : une CVE, un patch, une ligne de crédit.

## Quoi faire ce soir

1. **Inventaire** : chaque httpd que tu fais tourner, les trois portes (version, module, protocoles à l'écoute). Les commandes ci-dessus tournent en secondes par hôte.
2. **Patcher vers 2.4.71+** là où les portes 2 et 3 sont ouvertes ; `Protocols http/1.1` comme pont de 48 heures.
3. **Containers et images de base** : les `FROM httpd:*` et les packages distro exigent un rebuild ; 2.4.55-70 a été le défaut dans plein d'images pendant deux ans.
4. Surveiller la fenêtre d'armement : si tu ne peux pas patcher, la porte 3 est ton firewall (pas de h2 pour les étrangers), et tes logs de lignes `PRI * HTTP/2.0` te diront qui sonde.

**TL;DR** : CVE-2026-119618 est une race critique de mod_http2 (`assign_headers()`, corruption de heap, RCE) dans httpd 2.4.55-2.4.70, corrigée hier en 2.4.71, trouvée par l'OSS Scanner d'Anthropic plus des chercheurs indépendants, avec 64 %/51 % d'exposition cloud selon Wiz. Risque = version ET module ET protocole, trois commandes par hôte (mon Mac : flaggé version, safe sur les deux autres). Patche, ponte avec `Protocols http/1.1`, rebuild les images, et mets à jour tes priors Glasswing : le bruit est réel, et ça aussi.

Sources : [advisorie officielle Apache (2.4.71, crédits)](https://httpd.apache.org/security/vulnerabilities_24.html) · [Wiz : analyse CVE-2026-119618 et données d'exposition](https://www.wiz.io/blog/cve-2026-119618-rce-apache-http-server-vulnerability) · [l'audit Glasswing d'hier sur ce blog](https://dev.to/slabb/38000-ai-found-vulnerabilities-217-fixed-auditing-glasswing-anthropics-bug-discovery-machine-k65)
