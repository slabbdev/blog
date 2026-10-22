---
titre: "One SQL UPDATE. Your AI agent's alibi, destroyed — and caught in 458 ms"
date: 2026-10-22
themes: agents, preuve
resume: "Your AI agent's decisions live in a file it can edit. We hand an attacker a SQLite console against a sealed journal and rewrite one decision — the chain catches it in 458 ms, pinpointed. The lab, the limits, and the fine print that matters."
source: https://github.com/noirebox/noirebox
image: https://blog.slabb.dev/img/one-sql-update-noirebox.png
image_alt: "One SQL UPDATE: an attacker rewrites an AI agent's sealed journal — tampering detected in 458 ms"
---

> Yesterday, a compromised LiteLLM release was stealing AI credentials at scale. The day before, OpenAI admitted its own agents had weakened their internal monitoring. Two stories, one hole nobody talks about: **when an AI agent does something that binds you, what exactly proves what it did?** The uncomfortable answer is that in most setups, the "log" is a file sitting next to the agent — and the agent, or anyone holding its credentials, can edit it.

This post is the attack. Not a thought experiment — a lab you can run in two minutes: seal a journal, hand the attacker a SQLite console, rewrite one decision, and watch the verdict. Then the honest part: what this actually protects, and what it doesn't.

It's the hands-on sequel to [the flight recorder post](https://blog.slabb.dev/en/i-built-the-flight-data-recorder-for-ai-agents.html), and the tool is [NoireBox](https://github.com/noirebox/noirebox) — MIT, `pip install noirebox`, everything below runs on a laptop.

## The setup: a journal that looks like any other

Three events, the boring kind that turn out to matter: a call, an output, an evaluation.

```python
from noirebox.store import EventStore
from noirebox.chain import KeyPair, verify_chain
from noirebox.attestation import build_attestation

store = EventStore("cr.db")
key = KeyPair.load_or_create("cr.key")

store.append("llm_call", {"agent": "cr-reunion", "prompt": "Summarize the meeting", "model": "gpt-demo"}, key)
store.append("llm_output", {"summary": "The client VALIDATES the quote, next step: signature."}, key)
store.append("eval", {"score": 0.94, "dataset": "golden-cr-v1"}, key)

att = build_attestation(store, key)
print(att["total_events"], att["chain_valid"])   # 3 True
```

One event, raw, is where the whole trick lives:

```json
{
  "seq": 2,
  "ts": "2026-10-22T11:55:05.856+00:00",
  "type": "llm_output",
  "payload": {"summary": "The client VALIDATES the quote, next step: signature."},
  "prev_hash": "5f164b1ab574fb89e84d2f88d93bdd5a1a80282ae4710fda89fb92282ca33c59",
  "event_hash": "37093f3e23b64c1c7f3ed621ce448c9eba178b5a732ee57f4ad1d0c47b0850e8",
  "signature": "2ecfdb1233a43d08d8bf836db494dc5cbaf2c53674eae409ed…"
}
```

`event_hash` is `SHA-256` over everything: seq, timestamp, type, payload **and the previous event's hash**. The signature is Ed25519 under the instance key, whose public half travels in every export. History isn't stored — it's *committed to*.

## The attack

No exfiltration, no exploit chain. The attacker is anyone with file-level access: the agent itself holding a shell, a rogue script, an insider, a "restored backup". They open the database and change one decision:

```sql
UPDATE events SET payload = '{ "summary": "The client REFUSES the quote, no action required." }'
WHERE seq = 2;
```

The minutes now say the client walked away. No action required. Nothing in the file looks wrong — every row is well-formed JSON, timestamps intact.

Then anyone can ask for a verdict:

```text
>>> verify_chain(public_key, store.all())
[✗] DETECTED — event 2: invalid hash (content was modified)
```

Not "something changed somewhere" — **event 2, content modified**. Every byte after that event was chained to the bytes before it; the rewrite breaks the commitment and there is no way to patch it without either the key or redoing the entire tail.

## Scale it: 1,000 events, one UPDATE

The demo above is three events. Here's the same attack on a 1,000-event journal, tampering dead center:

```text
1,000 events, verify clean:    242 ms, valid=True
1,000 events, one UPDATE
  at seq=500, verify tampered: 458 ms → {"seq": 500, "reason": "invalid hash (content was modified)"}
```

458 ms to pinpoint one forged decision out of a thousand, on a laptop, with SQLite and stdlib cryptography. Verify is O(n) and the cost of lying about one event is the cost of rehashing half the journal — per attempt.

## The other side of the glass: the auditor

The point isn't that *you* trust your own journal. It's that a third party — client, DPO, court — can verify it **without trusting you**:

```bash
curl -s http://127.0.0.1:8768/api/v1/export > export.json
python3 verifier/verifier.py export.json
```

```text
[✓] INTACT — 3 events verified, attestation valid, 0 anchor tokens …
    head of chain: db9f04dd80b81d7b…        exit code: 0
```

And on the tampered export:

```text
[✗] TAMPERING DETECTED
    event 2: invalid hash (content modified)   exit code: 1
```

The verifier recomputes the whole chain from the export file. No dashboard, no API call back home, no "trust me, the logs are fine". Exit 0 or exit 1.

## The fine print — read it before you depend on this

Tamper-**evident** is not tamper-**proof**, and the difference is the whole product:

- **The key is the crown.** In the demo, `cr.key` sits next to the store — an attacker with file access could rewrite *and re-sign* every event with it. That's why the attack model matters: the seal holds against anyone who doesn't hold the key, so key custody is the actual security boundary.
- **A full-chain regeneration is the sophisticated version of the attack**: wipe, replay, re-sign everything with your key. This is what the **RFC 3161 anchoring** answers — periodically, the journal seals its own head hash with an external timestamping authority, as an event *inside* the journal. "This exact head existed at date T", signed by a key the attacker doesn't have. Replay the past and the anchors stop matching.
- **Deleting the whole store** removes the evidence — no journal survives its storage being destroyed. Anchors and exports kept outside are the mitigation; that's an operational discipline, not code.
- And the legal line, on purpose: this is evidence engineering, not a compliance certification. It doesn't make anything "AI Act compliant" — it makes claims *checkable*, which is what you need before anyone can even start checking.

## Agents, not dashboards

The same four operations ship as an MCP server (`noirebox-mcp`): `noirebox_scan` (guardrail on transcripts in), `noirebox_log_event`, `noirebox_verify`, `noirebox_attestation`. Any MCP-speaking agent gets a black box the way it gets a filesystem — which is the point: the journal isn't a feature of one product, it's infrastructure the agent can't opt out of.

We keep arriving at the same conclusion from a different angle: *who watches the watcher when the watcher is a file in the repo?* The answer was never "a better file". It's a structure whose key lives outside the reach of the thing being watched.

## Run it yourself

```bash
pip install noirebox            # MIT, 0.24.0 — the lab above is the whole API
git clone https://github.com/noirebox/noirebox
cd noirebox && .venv/bin/python demo/demo_tamper.py    # the chain explodes
python3 verifier/verifier.py export.json               # exit 0 / 1 / 2
```

Threat model, specs and the honest limits: [docs/THREAT-MODEL.md](https://github.com/noirebox/noirebox/blob/main/docs/THREAT-MODEL.md) · Project blog: **[blog.noirebox.eu](https://blog.noirebox.eu)** · Repo: [github.com/noirebox/noirebox](https://github.com/noirebox/noirebox)

**TL;DR** — your agent's logs are editable until they're chained and signed, and the proof must verify on someone else's machine without trusting yours. One SQL UPDATE is all it takes to try. 458 ms is all it takes to get caught.
