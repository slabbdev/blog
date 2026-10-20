---
titre: "OpenCode lost the keys that lived in its cloud. The ones on disk were fine."
date: 2026-10-19
themes: securite, agents
source: https://dev.to/slabb/opencode-lost-the-keys-that-lived-in-its-cloud-the-ones-on-disk-were-fine-238g
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fr49qhm9mantoqtdmhhzi.png
image_alt: "OpenCode lost the keys that lived in its cloud. The ones on disk were fine."
resume: "A breach of OpenCode's online console exposed 1.4% of users' stored API keys — five-figure bills at 3am, Anthropic and Google blocking keys, OpenAI refunding credits. The CLI users slept. The incident didn't need the disputed distillation motive to prove the architecture rule: your key's custody grade is the retention policy of wherever you left it."
---

> API keys are credit cards without a ceiling. This week someone broke into the ceiling-holder's office — and the interesting part is not who did it. The interesting part is that the breach sorted users into two groups by architecture, and one group slept through it.

Mid-October, attackers got into the **online console of OpenCode**, an open-source coding agent positioned as an alternative to Claude Code or Cursor. Some developers stored their AI provider keys in that console — a convenience workspace where the platform holds your credentials and proxies your calls. The keys leaked. [Actu.ai's writeup](https://www.actu.ai/opencode-piratage-cles-api-factures-ia-proteger-ses-cles-80037.html) and OpenCode's own statements on X piece the incident together: **1.4% of console users** affected, spend alerts firing at 3am, bills from several hundred to over **$1,000** at OpenAI, Anthropic and Google.

The response machinery worked the way it's supposed to. Anthropic and Google **blocked the exposed keys**; OpenAI restored access and **refunded the consumed credits**; OpenCode is reimbursing unauthorized fees. The company's cofounder Dax Raad reported intrusion attempts running continuously for 48 hours.

## The split that matters more than the breach

Here is the part I'd put on a slide. The incident divided OpenCode's users into two populations, and the dividing line was not luck, patch level, or password strength:

- **Keys stored in the cloud console** — the platform's retention policy became *your* key's custody grade. 1.4% of that population got robbed.
- **Keys that stayed on the machine** — the CLI and the local app never upload keys to OpenCode's servers. Zero of that population was exposed. Not "less exposed." Structurally unreachable by this attack.

OpenCode's own statement is the receipt: the app and CLI are untouched *because the keys used by those tools never transit their servers*. The vendor published the architecture rule while disclosing the breach of the architecture that broke it.

## What about the distillation story?

The claimed motive is a "large-scale distillation attack" — burning stolen keys at industrial volume to train a competing model on a frontier model's outputs, possibly from regions where US models are restricted. It's a compelling story, and [some observers are openly skeptical](https://www.actu.ai/opencode-piratage-cles-api-factures-ia-proteger-ses-cles-80037.html): for them this is a classic intrusion, and distillation as the purpose is unproven. OpenCode has not said how the attackers got in, or how the keys were stored.

I'm going to suggest something that sounds cold: **the motive doesn't matter for the engineering conclusion.** Whether the thieves wanted training data or just free inference, the exploitable condition was identical — keys held in custody of a third-party web console. Your defense shouldn't be conditioned on a narrative the vendor couldn't confirm either. Facts first: server-side key storage leaked, on-device key storage didn't. The story is somebody else's post-mortem.

## Run it yourself: the custody audit

You cannot audit OpenCode. You can audit yourself, in one pipeline — the question is not "are my keys safe" but "**where do they physically live, and who controls that storage**". Count the places your keys actually sit:

```sh
# 1. keys lying around in shell configs and dotfiles (count, don't print)
grep -rlE "sk-ant-[a-zA-Z0-9_-]{20,}|sk-[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z_-]{35}" \
  ~/.zshrc ~/.bashrc ~/.profile ~/.config 2>/dev/null

# 2. keys duplicated across project .env files (each copy is a retention surface)
find ~ -maxdepth 4 -name ".env" -not -path "*/node_modules/*" 2>/dev/null \
  -exec grep -lE "sk-ant-|sk-[a-zA-Z0-9]{20,}|AIza" {} \;

# 3. keys committed to git history, the retention surface that outlives you
git log --all --full-history -p -- . 2>/dev/null | grep -cE "sk-ant-[a-zA-Z0-9_-]{20,}"
```

Rule one: the output of an audit is a *count and a location*, never the key itself. Rule two: every location in the output is a retention surface you either control (your disk, encrypted at rest, your keychain) or don't (someone's web console, someone's CI cache, someone's git history). Rule three, from the incident: **keys that only live on your machine cannot leak in a console breach** — that is not a best practice, it is an architectural property.

Then close the loop the boring way: per-project keys instead of one god key (a leak gets contained), hard spend caps at the provider (the 3am alert becomes a 3am *rejection*), and rotation on any doubt — rotation beats deletion, because a deleted key in someone's exfiltration dump is still valid until revoked.

## The custody grade, applied to key material

My last post on this series was the CA industry discovering that a witness must live somewhere the attacker can't reach — five perspectives, two RIRs, a quorum. The same `min()` runs through this breach. Your API key has an authoring grade (you typed it, you control the bytes) and a custody grade (wherever you *stored* it, and whose retention policy guards that store). Store it in a web console and your custody grade is that console's patch discipline, incident response, and employee vetting — none of which appear in your threat model until 1.4% of the user base gets an email.

We shipped the answer on our own stack the same week, because the rule is not new even when the news is: keys belong in the OS keychain, bound to the origin they call, and the agent that uses them should never read them — [`navette creds set`](https://github.com/slabbdev/navette) fills a password you type once, stores it in the Keychain, and the agent only ever gets a `{logged_in: true}`. And if you want to *know* what your agent emits instead of trusting it, that is what a logging proxy in front of the client is for — [one file, no API key, verbatim capture](https://dev.to/slabb/i-put-a-logging-proxy-in-front-of-an-llm-client-heres-what-it-emitted-5dii).

The OpenCode CLI users were right by architecture. Be right by architecture.

---

*Sources: [Actu.ai — Piratage d'OpenCode](https://www.actu.ai/opencode-piratage-cles-api-factures-ia-proteger-ses-cles-80037.html) (Oct 20, 2026), OpenCode statements on X (Dax Raad). The custody framework follows [this comment thread](https://dev.to/fluffydesk/comment/3hmoi) and [the five-witnesses post](https://dev.to/slabb/five-witnesses-and-two-rirs-the-cas-just-discovered-custody-4aie).*
