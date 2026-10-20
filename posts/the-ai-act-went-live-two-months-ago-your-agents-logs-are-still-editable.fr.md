---
titre: "L'AI Act est entré en vigueur il y a deux mois. Les logs de vos agents restent modifiables."
date: 2026-09-30
themes: preuve
resume: "L'exigence réglementaire existe, la technique manque : journaux chaînés et horodatage comme réponse."
source: https://dev.to/slabb/the-ai-act-went-live-two-months-ago-your-agents-logs-are-still-editable-46dn
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2F19f5h9m81usx77lwoxl7.jpeg
image_alt: "L'AI Act est entré en vigueur il y a deux mois. Les logs de vos agents restent modifiables."
---


> 🇬🇧 **Cet article n'est pas encore traduit** — la version originale en anglais suit. La traduction arrive.

In April, an AI coding agent took out a company's production database. One GraphQL mutation against the Railway API, [nine seconds](https://zenity.io/blog/ai-agent-database-deletion-pocketos), and the production volume was gone. The backups attached to it went too. The founder told the story [himself](https://x.com/lifeofjer/article/2048103471019434248); the agent, reports said, then wrote a confession.

The confession made the rounds as a punchline. The detail that should have kept you up at night was quieter: the most complete witness to what happened was the agent itself, narrating its own actions in a transcript nobody outside the company could verify. And nobody doubts the story. But nobody doubting it isn't a property of the evidence. It's a property of the narrator's mood that day.

Two dev.to posts framed this summer's version of the debate. [Prompt Injection Is the New SQL Injection](https://dev.to/james_anderson_h/prompt-injection-is-the-new-sql-injection-and-were-not-ready-4ea4) is the one everybody quoted, and it ends where these conversations always end: defenses that shrink the blast radius from "catastrophic" to "survivable", plus a call to audit what your agent *reads* against what it's *allowed to do*. Its companion, [Who's Accountable When the AI Was Just Following Instructions?](https://dev.to/james_anderson_h/whos-accountable-when-the-ai-was-just-following-instructions-1efl), doesn't name a culprit. It asks for one thing instead: *"a record of who authorized what — an unforgeable one, not logs the acting system can quietly rewrite."*

That sentence is the whole problem. Neither thread shows how to build the thing it asks for. And both conversations live in the first gap. The unforgeable record is second-gap territory, and the law landed there two months ago.

Quick map, because I'll lean on it. Any AI system has two gaps. What it reads versus what it's allowed to do: the exploit gap. What it did versus what its logs say: the cover-up gap. This post lives in the second one.

![The two gaps — Article 12 lives in the second one](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/k53q4a66sb42naubw687.png)

## Two months ago, the clock started

And while everyone argued about blame, the law moved. On August 2 the EU AI Act passed its general application date: it now applies everywhere its text doesn't schedule otherwise. The big "otherwise" is the high-risk block of Annex III, which lands on [**December 2, 2027**](https://artificialintelligenceact.eu/high-level-summary/). Article 12 sits in that block, and it says high-risk systems must *technically allow for the automatic recording of events (logs) over their lifetime*.

Fourteen months is nothing when the thing being retrofitted is logging that has to survive an auditor. Most agent stacks will check that box with a database table the operator owns. A log you control is a log you can edit, and on the day an authority asks to see it, "we have logs" and "we can prove these logs were never touched" are two very different sentences.

## What the text actually asks for

Article 12 stops being abstract once you read it against an agent stack. The system must record events automatically over its lifetime, with enough detail to trace how it functioned, including the situations that pose risk, and to flag substantial modifications. The deployer keeps those logs for at least six months. On request, they go to the competent authority.

In agent terms:

- every tool call, with arguments, results, and which model decision produced it
- every LLM call. Including the transcript the model was fed — yes, that transcript
- config changes and substantial modifications, versioned
- timestamps that don't depend on the honesty of the machine writing them
- and retention you can prove, not retention you describe in a policy nobody reads

Nothing in that list scares anyone. Every product in this space logs it today. The verb that hurts is the last one in the paragraph: *provide*. Whatever you hand over has to survive someone whose job is to distrust you.

## "Automatic" is doing the heavy lifting

Automatic recording is satisfied by the agent writing its own log. Nobody types it, so it's automatic. But a log written by the system it describes, on infrastructure owned by the operator, is a confession written by the suspect.

Append-only flags stop the sloppy mistakes and nobody else. Hash chains stop outsiders. Neither stops the key holder: they can regenerate the entire history, fabricated events, recomputed hashes, re-signed seals, and end up with an internally consistent journal that verifies against its own key with flying colors. Which proves exactly one thing — that somebody with the key built it. Not *when*. And when is the whole game. A seal created after the fact tells you nothing about what existed before it.

<!-- internal link slot: previous post "Anyone with database access can rewrite your AI agent's logs" — paste URL here if live on dev.to -->

## A witness you can build from parts you already have

The fix is a timestamp from someone outside your trust boundary. The pieces are standard, and the core fits on one screen. The chain first:

```python
import hashlib, json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

key = Ed25519PrivateKey.generate()

def seal(prev_head: bytes, event: dict) -> dict:
    payload = json.dumps(event, sort_keys=True).encode()
    head = hashlib.sha256(prev_head + payload).digest()
    return {
        "event": event,
        "head": head.hex(),
        "prev": prev_head.hex(),
        "sig": key.sign(head).hex(),
    }

GENESIS = bytes(32)  # head of an empty journal
journal = [seal(GENESIS, {"kind": "tool_call", "tool": "db.delete", "ok": True})]
```

Change one event and every head after it changes. Forge the whole history and every head changes. At this point the chain only verifies against its own key, which proves nothing about *when*. So you take the head, all 32 bytes of it, and hand it to witnesses that don't work for you:

```bash
pip install opentimestamps-client        # the only install this post asks for
echo "<last head, hex>" | xxd -r -p > head.bin

ots stamp head.bin                       # lands in a bitcoin block header
ots upgrade head.bin.ots && ots verify head.bin.ots

openssl ts -query -data head.bin -sha256 -cert -out head.tsq
curl -s -H "Content-Type: application/timestamp-query" \
     --data-binary @head.tsq https://freetsa.org/tsr > head.tsr
openssl ts -verify -data head.bin -in head.tsr -CAfile tsa.crt
```

Two different failure modes for a forger. OpenTimestamps buries your 32-byte head in a bitcoin Merkle tree, and redoing a network's proof of work is not a plan. The RFC 3161 receipt is the legal tier: a qualified timestamp authority carries a presumption of correctness under eIDAS, which is the difference between a technical measure and a measure a lawyer accepts. Notice what neither witness ever sees: an event. Only an opaque digest. The GDPR conversation stays short.

What the auditor gets is almost boring. Three files: the journal export, the anchoring receipts, and a verifier of about sixty lines that recomputes the chain from genesis, checks every signature against the public key you published, and checks each receipt against its external root. Exit 0 or the history is rejected, no matter when the tampering happened — any rewrite produces a different head than the one the witnesses recorded. Next to those files goes the logging description Annexe IV §2(f) asks for, written once, against a journal that can't quietly drift.

![What the auditor actually receives: export.json, the receipts, exit 0](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/fnm0dptljdq0t4hkd1tt.png)

## Two honest limits

Because a log is the easiest place to oversell compliance.

First: tamper-evidence is not truth-at-write. Anchoring proves the journal wasn't altered after the fact. If the agent records a false event and it gets sealed, you have now proven, with bitcoin's help, that a falsehood existed. Garbage in, sealed forever.

Second, this documents. It doesn't prevent. Article 12 lives in the cover-up gap and leaves the exploit gap exactly where it found it. An agent that shouldn't touch production will still touch production. It'll just do it on the record. That's worth something, but it's not the same thing, and I'd rather not blur them.

If you've been through an AI Act readiness review this summer, yours or a client's, I'm curious what they actually asked about your logs. Comments are open.
