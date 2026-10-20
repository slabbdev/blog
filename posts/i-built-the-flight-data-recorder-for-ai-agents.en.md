---
titre: "I built the flight data recorder for AI agents."
date: 2026-09-22
themes: agents, preuve
resume: "Or: why I spent my evenings making AI-agent journals impossible to rewrite.              One Tuesday,..."
source: https://dev.to/slabb/i-built-the-flight-data-recorder-for-ai-agents-38f6
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fk1elz17wfgodj9udh7ur.png
image_alt: "I built the flight data recorder for AI agents."
---

*Or: why I spent my evenings making AI-agent journals impossible to rewrite.*

---

## One Tuesday, at 2:37 PM

A disgruntled employee opens the database behind an AI product and
edits one row. The minutes an agent produced yesterday — the ones a client
is about to receive — now say something else. No alert. No trace. The
dashboard shows a pristine history, because the history **has been
rewritten**.

This isn't a thriller plot. It is the default state of every AI-agent
product shipping today: their logs live in mutable databases, and **nothing
exists to prove, after the fact, what the agent actually decided**.

I looked for the tool that closes this gap. It didn't exist. So I built it.
It's called **NoireBox**, it's open source (MIT), and this post is about
what it does, how it does it, and why I believe it's a missing piece.

→ **https://noirebox.github.io/noirebox**

*(Written three weeks ago; updated October 8 — the numbers below are
regenerated, not remembered.)*

## The founding question

After fifteen years of backend engineering — insurance, renewable energy,
real estate — in systems where every decision must be defensible years
later, I asked the question that started everything:

> **If someone contests a decision made by an AI agent tomorrow, who can
> *prove* it?**

Not "who can tell the story". Not "where is it logged". Who can **prove** it
— to a client, a lawyer, an auditor, a regulator — without trusting the
vendor, the host, or the administrator?

The answer, everywhere, was: nobody. Observability tooling (Langfuse,
LangSmith, Helicone…) is great for **debugging** what happened — but its
logs stay mutable, and nothing is exportable as evidence. Debugging and
proving are different jobs.

## The principle: a proof, not a promise

NoireBox is a **tamper-evident journal for AI agents** — a flight data
recorder, like the ones in aircraft. Every event (model call, output,
decision, incident) goes through four mechanisms:

**1. Hash chaining.** Each event's SHA-256 fingerprint includes the previous
event's. Modify, insert, or delete anything and the chain breaks — and the
verifier tells you **which** event was tampered with. A numbered notebook:
you can't tear out a page without anyone noticing.

**2. Signatures.** Every fingerprint is signed with **Ed25519**, using a key
that never leaves the server (chmod 600) — or one injected by your secret
manager. Regenerating the whole chain without the key? The forgery is
visible on sight.

**3. The outside witness.** The detail that kills tampering *at the source*:
NoireBox has an external **timestamp authority** (RFC 3161 — the same
protocol notaries and audit firms use) sign the chain head's fingerprint at
time T. Rewriting history *afterwards* becomes arithmetically impossible:
the old token no longer covers the new head. A journal that timestamps
itself proves nothing — that's the suspect writing its own police report.

**4. The third-party-verifiable export.** One file, plus a standalone
verifier that **anyone** runs on their own machine, offline, with no
credentials:

```console
$ python verifier/verifier.py export.json
[✓] INTACT — 7375 events verified, attestation valid, 4 anchor tokens (2 against pinned roots, 0 reported-not-verified), head of chain: 6097eca4b7690d90…
```

*Output from the journal running on my machine as I edit these lines —
not an illustration.*

And on that Tuesday at 2:37 PM, the same verifier returns a different
verdict:

```console
[3] An attacker rewrites event 2: the minutes now read "REFUSE".
[✗] DETECTED — event 2: invalid hash (content was modified)
```

*(Real output from the repo's tamper demo — not an illustration.)*

**NoireBox never asks you to trust it. It hands you the dossier, and anyone
recomputes the truth themselves.**

## What about a whole fleet? One seal, a thousand boxes

Each box seals its own chain head individually. But what if you run 1,200
agents? Aggregated anchoring: the chain heads of N boxes form a **Merkle
tree** whose root receives **a single** TSA seal. One seal for the whole
fleet — and each box proves it took part with ~log₂(N) hashes (11 for
1,200), verified offline.

That's the **Certificate Transparency** model — the system that made HTTPS
certificates auditable worldwide — applied to AI-agent decisions. To my
knowledge, nobody does this.

```console
$ make demo-fleet
[2] Merkle tree: 3 leaves, root 7f2cf1a1e7b9879d…
    cr-reunion         proof: 2 hashes → ✓ covered
    support-juridique  proof: 2 hashes → ✓ covered
    scoring-credit     proof: 2 hashes → ✓ covered
[5] support-juridique regenerates its journal: content rewritten, re-chained cleanly.
[✗] DETECTED — the new head is not covered by the fleet seal.
    old head covered: yes; new one: NO
```

*(The root is different on every run — it commits to the exact state of
every chain at sealing time. That's the point.)*

The most important part: the hub doing the aggregation cannot cheat. It can
*omit* a box (a detectable silence), but it can neither rewrite a sealed
batch nor include a fake head — and it journals the full tree into **its
own** NoireBox journal. Every member verifies **locally**, without
contacting anyone. The arithmetic decides.

## The guardrail is a plugin (keep yours)

Already running Lakera, Llama Guard, your own LLM-judge, or your own
regexes? **Keep them.** Prevention is a fungible layer — everyone has their
own, and it will keep changing. Proof is the universal layer.

Journal your solution's verdicts with a single `POST /api/v1/events`
(`type: "incident"`) and its catches become tamper-evident and
third-party-verifiable, instead of ending up in rewritable app logs. The
bundled detector (regex + micro-model, French, English and Spanish, ~250–290
KB per language) is a **working example of the plugin contract**, not an
obligation.

## The numbers — all reproducible with one command

| Metric | Value | Reproduce with |
|---|---|---|
| Sealing one event (hash + signature + commit) | 0.17 ms | `make bench` |
| Full verification of 100 events | ~44 ms | `make bench` |
| Bundled detectors, FR + EN + ES | 293 + 243 + 287 KB | `make train` + `make train-en` + `make train-es` |
| Held-out attack sentences, never seen in training | 18/18 across FR, EN, ES | the three `metrics*.json` files |
| Test suite | 244 green | `make test` |

Performance is boring by design, as it should be: sealing an event
(hash + signature + commit) costs a fraction of a millisecond, and
verifying a 100-event export takes about a tenth of a second on a laptop.
The bottleneck is SHA-256 and Ed25519 — not clever code.

I imposed one rule on myself: **no number that can't be reproduced with one
command.** A metric we can't reproduce is *unknown* — not a rounder number.
That's also why this post contains no "78M+ events", no customer logos, no
testimonials.

## What three weeks of public review added

This post got taken apart in public, and the attacks became the roadmap.
The consolidated answers are six new ADRs, credited to the people who
found the gaps: a **receipt schema v0.2.1** where a verdict binds its
check, its evaluator (touch the test suite and the receipts die), the
spec that defines its semantics, the questions asked — anchored outside
the agent's reach — and **the state it was judged against** (the TOCTOU
field: the executor applies the sealed version as a precondition, a 409
on state move, the divergence sealed — never silent reuse); **the
denominator** — a hash chain never catches the entry never written, so
attempts are sealed before outcomes, the invariant is `outcomes ≤
attempts`, and an outbound expectation must be anchored or co-signed
before "pending" means anything; **flow independence as a testable
invariant** — can one compromise reach both the audit flow and the truth
flow?; **custody vs anchoring** — when a counterparty exists, their
record beats your timestamp; **sealing the belief** — the resolved view
captured before the action; and **cross-chain reconciliation (ADR 024)**
— when one agent consumes another's output, the consumption itself is a
sealable event, the contract is a partial order (edge admissibility, not
a global timeline), and the blast radius of a superseded head is a
precise path set. A journal server that anchors itself on a wall-clock
timer, journals that several processes write and anyone verifies, and a
checker whose own reports are sealed — clean passes included, negative
controls that must bite. The attackers are named in the ADRs, because
credit is the cheapest honesty there is.

## What it is not

- **Not a blockchain.** One issuer, one verifier. Blockchains solve a
  problem we don't have — consensus among strangers — at a complexity price
  we refuse to pay.
- **Not a certification.** A building block that feeds your audits; the
  exact perimeter is written down in the
  [threat model](https://github.com/noirebox/noirebox/blob/main/docs/THREAT-MODEL.md).
- **Not an LLM.** A ~250 KB specialist detector that sorts sentences into 5
  classes, deterministic and testable — not a black box predicting the next
  token.

## Why now

The [EU AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) (article 12)
requires **automatic event logging** for high-risk systems. GDPR (art. 5(2),
30) puts the burden of proof on whoever processes the data. ISO 42001
asks for traceability of AI decisions.

European vendors will have to **prove** — not promise — what their agents
did. Today, almost none of them can. NoireBox is a sovereign building block:
self-hosted, zero telemetry, keys stay yours. Built in the Vosges mountains
🇫🇷 — yes, proof infrastructure can be built from the mountains.

## Try it in three commands — or one with Docker 🐳

```console
$ git clone https://github.com/noirebox/noirebox && cd noirebox
$ ./start.sh          # 244 green tests + API on :8768 — /docs is live
$ make demo           # the model → the journal → the auditor → the attacker
```

Or from PyPI — the ML engine ships inside the wheel:

```console
$ pip install noirebox
$ noirebox serve      # API + OpenAPI docs on :8768/docs
```

Or with Docker — no Python needed:

```bash
docker run -p 8768:8768 ghcr.io/noirebox/noirebox:latest
```

API + OpenAPI docs on :8768/docs — data persists in ./data. The image is
public on GHCR: pull it anonymously, run it, verify it.

FastAPI, 11 documented routes plus Prometheus metrics, a Python SDK, an MCP
server (4 tools to plug your agents in), a bilingual DPO-ready PDF export, a
VS Code extension (Marketplace and Open VSX), and a self-hosted TSA
(`make tsa`, OpenSSL, $0, offline) — because a witness you don't control is
a witness less.

## What's next

Shipped since this post: the receipt schema v0.2.1 with state binding
(ADR 019), the denominator and its outbound half (ADR 020), flow
independence as a bench (ADR 021), the custody-vs-anchoring taxonomy
(ADR 022), belief-before-action sealing (ADR 023), cross-chain
reconciliation (ADR 024), the two-key pairing enforced, the auto-anchor
timer, multi-writer journals, Spanish detection, and the editor
extension (VS Marketplace and Open VSX). Zero open issues. Next: the
cross-chain edges wired into the reconciler, the independence bench
against outside review, HSM-backed signing. The core is **MIT, forever —
verification included.**

If this resonates, here's what would help the most:

- ⭐ [A star on the repo](https://github.com/noirebox/noirebox) — it sounds
  silly, but it's what makes a project exist
- 🕵️ **Try to break the proof.** This is a project whose product is
  resistance to tampering: the best compliment is an issue describing an
  attack
- 🔀 Fork it, PR it, question it — the code is deliberately small (one
  journal, one plugin, one verifier) so it can be read end to end

And if you know a DPO, a CISO, or an AI vendor preparing for article 12,
send them this post — that's exactly who this black box is for.

---

*NoireBox — every AI decision, sealed forever.*

*Built solo, in the Vosges mountains, between two missions. Code, threat
model and specs:*
**[github.com/noirebox/noirebox](https://github.com/noirebox/noirebox)**
