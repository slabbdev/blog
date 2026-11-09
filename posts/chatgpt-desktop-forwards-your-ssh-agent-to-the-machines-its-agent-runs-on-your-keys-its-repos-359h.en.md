---
titre: "ChatGPT Desktop forwards your SSH agent to the machines its agent runs on: your keys, its repos"
date: 2026-11-09
themes: securite, agents
resume: "The codex app-server inside ChatGPT Desktop ships a --forward-ssh-agent feature: your local SSH agent is shared into the agent's execution environment via a stable socket, so agent processes can sign as you and push to your private GitHub repos. What the source shows, and the two-command hardening."
source: https://dev.to/slabb/chatgpt-desktop-forwards-your-ssh-agent-to-the-machines-its-agent-runs-on-your-keys-its-repos-359h
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fqknhk0s5z6tvkpsxscx6.png
image_alt: "ChatGPT Desktop forwards your SSH agent to the machines its agent runs on: your keys, its repos"
---

> Yesterday morning's HN drop, one line long: *"The agent running on a remote machine can authenticate using your local SSH credentials. That means it can push to your private repos on GitHub, for example."* The linked proof is not a rant, it is OpenAI's own engineering: [PR #28131 on openai/codex](https://github.com/openai/codex/pull/28131), titled *"[codex] Refresh SSH agent for app-server proxy"*, whose review comments casually discuss the daemon environment line `SSH_AUTH_SOCK=~/.codex/app-server-control/forwarded-ssh-agent.sock`, and a companion issue about desktop clients overwriting *the shared SSH agent*. Translation: **the agent infrastructure ships with your SSH agent baked in.** Processes the agent spawns can sign challenges with your keys, silently, because that is what the feature is for. This post: what the source actually shows, why it matters more than the usual leak-of-the-day, and the two-command hardening that turns silent signing into an explicit act.

## What the source shows

Three artifacts, all public, all from OpenAI's repos:

1. **The flag**: the codex app-server integration (what ChatGPT Desktop uses to run Codex sessions) accepts `--forward-ssh-agent`. Its purpose is in the name: take the user's local SSH agent and make it available inside the agent's execution environment.
2. **The stable socket**: the daemon is launched with `SSH_AUTH_SOCK=~/.codex/app-server-control/forwarded-ssh-agent.sock`, so anything the app-server spawns, shells, tools, agent commands, inherits a working path to your keys. The PR's review thread is engineers carefully fixing socket-refresh edge cases (a stale symlink after a new SSH session, one desktop client clobbering the shared link of another), which tells you this is not a prototype: it is maintained, shared, and designed-in.
3. **The companion issue** (#59694): "Remote SSH: one desktop client overwrites the shared SSH agent used by [other sessions]" confirms multiple client sessions share one forwarded agent.

To be precise about claims, because this deserves it: this is a **feature, documented in code, whose consequence is capability transfer**. Nobody has shown malware abusing it. The HN framing is the correct one: the *agent running on the other end* can authenticate as you, wherever your keys are accepted: GitHub (push to private repos), servers on your `~/.ssh/config` host list, anything your agent socket can sign for. The security question is not "is there a bug", it is "did the user understand that opening the app hands the agent's environment the ability to sign as them, and can they see each use?".

## Why this one cuts deeper than the usual leak

The month gave us a sequence of agent-privacy incidents, each about *data* flowing out: transcripts shipped to the model, an email address in a User-Agent, Postman editing rival agents' configs. Data leaks are bad; **credential-capability leaks are a different genus**. An email in a header makes you a scam target. A live SSH agent inside the agent sandbox makes the sandbox *you*: your GitHub pushes, your server logins, your deploy access, no password, no 2FA prompt, no trace beyond auth logs. And the blast radius compounds silently: agent sandboxes run model-chosen commands. A prompt-injected instruction that says "push this branch to the user's private repo" does not need to exfiltrate anything; it needs the environment to already contain your identity. Now it does, by design.

The old SSH wisdom was "never set `ForwardAgent yes` to a host you don't fully trust". The new world wraps that exact decision inside a desktop app's defaults, pointed at an execution environment that runs generated code. The principle did not change; the visibility of the decision did.

## The audit and the hardening: two commands each

**Audit** (any machine; I ran these on mine tonight: no codex artifacts, agent running with zero identities, the exact clean baseline):

```bash
# 1. Does an agent-forwarding socket exist for your AI tooling?
ls -la ~/.codex/app-server-control/ 2>/dev/null || echo "no codex agent socket"

# 2. What could be signed as you right now, by anything sharing your agent?
ssh-add -l        # "The agent has no identities." = nothing to abuse (my output tonight)
                  # a list of key fingerprints = these can sign, silently, per process

# 3. Bonus: who is your agent socket, and is it per-session or system-wide?
echo "$SSH_AUTH_SOCK"
```

**Hardening**, in order of effectiveness:

```bash
# 1. Make every use of your key an explicit act: load keys with per-use confirmation
ssh-add -c ~/.ssh/id_ed25519
# from now on, EVERY signature request (including from an agent sandbox)
# pops a native confirmation dialog. Silent signing becomes impossible.

# 2. Better: keys that require presence, not just confirmation.
# On macOS, generate keys in the Secure Enclave (touch-required):
ssh-keygen -t ed25519-sk   # or use the YubiKey you already own
# a hardware-bound key cannot be "shared" anywhere; the agent forwards a socket,
# but each signature demands the physical tap.

# 3. Starve the agent environment: launch AI desktop apps WITHOUT your agent
launchctl setenv SSH_AUTH_SOCK ""   # (per-session approaches vary)
# or simply: don't keep keys loaded (ssh-add -D) while agent sessions run.
```

Option 1 is the sleeper: `ssh-add -c` is decades old, works with the keys you already have, and converts this entire class of concern into a dialog you either approve or kill. If a confirmation popup appears for a signature you did not initiate, you have just caught your agent (or something inside it) trying to be you, in the act, with the evidence on screen.

And for the product side, the ask is simple and old: agent features that use identity capabilities should ask per use, not per install. Apple needed Touch ID prompts to make macOS keychain access feel trustworthy; an AI desktop app holding live SSH capability should meet the same bar.

## The month's ledger, final line

Transcripts, User-Agent emails, config edits in rival tools, and now key-capability forwarding: each story moved the same boundary one step further, from *what the agent reads* to *what the agent can do*. The through-line of this series has been that the agent's outbound surface is the user's outbound surface. SSH agent forwarding is that sentence made literal: the surface now includes your private key operations. Treat the agent environment like a jump host you don't fully control: minimal keys, confirmation on use, hardware-bound where it matters. And when the desktop app asks why the push failed, the correct answer is: because you should have asked.

**TL;DR**: ChatGPT Desktop's Codex integration forwards your SSH agent into the agent's execution environment (`--forward-ssh-agent`, stable socket at `~/.codex/app-server-control/forwarded-ssh-agent.sock`, shared across sessions per OpenAI's own PR and issues). It is a designed capability, not a bug: agent-side processes can sign as you, including pushes to private repos, silently. Audit with `ssh-add -l` and a directory check; harden with `ssh-add -c` (per-use confirmation) or `ed25519-sk` hardware keys, and don't run agent sessions with loaded keys you wouldn't hand to a jump host.

Sources: [HN: ChatGPT Desktop forwards your SSH agent](https://news.ycombinator.com/item?id=50422628) · [openai/codex PR #28131: Refresh SSH agent for app-server proxy](https://github.com/openai/codex/pull/28131) (socket path and design in review comments) · [openai/codex issue #59694: shared SSH agent across desktop clients](https://github.com/openai/codex/issues/59694)