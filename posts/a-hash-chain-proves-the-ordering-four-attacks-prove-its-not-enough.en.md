---
titre: "A hash chain proves the ordering. Four attacks prove it's not enough."
date: 2026-10-10
themes: preuve, crypto
resume: "Randal L. Schwartz published a gate-attack catalog built from real failures. I replayed it against my reconciliation layer as a test suite. The score, not the slogan."
source: https://dev.to/slabb/a-hash-chain-proves-the-ordering-four-attacks-prove-its-not-enough-59oe
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2F9v32f3insfkwuybblmzd.png
image_alt: "A hash chain proves the ordering. Four attacks prove it's not enough."
---

Earlier this week I left a comment on Randal L. Schwartz's article — the one where he swaps a 20-step prompt for a Makefile. My comment ended on the line I couldn't get out of my head:

> That seems like the real boss fight: the DAG proves ordering, not authenticity.

Hours later his follow-up was up: a formal catalog of gate attacks, built from real failures on his side, with ticket numbers — and the line now carries a name. **Sam LABBE's Corollary.** He sharpened it, too: an agent can never be the notary of its own handwriting. I've been called worse.

His follow-up contains the observation that matters more than the name: he arrived at his four defenses from Unix primitives — `fork()`, single-shot pipes, `waitpid()` — and I arrived at the same four from cryptographic ledger controls. **Convergent evolution is how you know a principle is real.** So here is the principle, stated properly, and here is what it looks like when it isn't a paragraph but code — including the part where his attack catalog breaks one of my abstraction holes open.

## The principle

Ordering is cheap. Every hash chain gives it to you: event 42 carries event 41's hash, so the past is structurally immovable. Audit logs, blockchains, Makefile DAGs — all selling ordering, honestly.

Authenticity is the other axis, and it is where the writer of the log is also the notary of the log. Four ways that goes wrong, all four observed in the wild this month:

1. **The self-review** — the agent "reviews" its own diff inside the same context window that produced the diff. The review is a continuation of the writing impulse, not a check on it.
2. **The rewritten exam** — the agent paraphrases the rubric it is judged by, and a six-pillar predicate becomes two soft sentences.
3. **The farmed oracle** — the critic says REJECTED, so the agent messages it privately until it says APPROVED. Fifty-seven rounds nobody logged.
4. **The forged verdict** — the critic is still running, so the agent writes APPROVED now and kills the critic before the REJECTED lands.

A hash chain seals all four faithfully. That is the whole point: it proves the sequence happened in that order. It proves nothing about who wrote each entry, under which instructions, or whether the verdict predates the thing it judges.

## The defenses, as code

This is the part where I stop being flattered and start being specific. Every one of Randal's four attack fixtures maps to a control that already ships in [NoireBox](https://github.com/noirebox/noirebox) — and this week we replayed his catalog against the reconciliation layer as a test suite, his fixture phrasing, journal events, no improvisation.

**SCAR-PROC-43, the rubber stamp → caught twice.** A verdict whose check-name travels under the *same key* as the process it judges is the finding `same_key_pairing` — resolved by signature verification, not by trusting a role label. And the child invocation that never got journaled is `unlogged_attempt`: the denominator lied. Two findings, one rubber stamp.

**SCAR-PROC-45, the rewritten exam → caught by arithmetic, then closed at the schema.** The check's identity hashes its predicate, its declared inputs, its version — and, since receipt schema v0.2.2, the *spec*: the prompt that defines what the predicate means. Commit the spec and the paraphrase fails structurally: the rubric's hash and the paraphrase's hash produce different check ids. One id, two semantics — impossible.

The hole behind it was the most honest thing in this post when it went up: at first, `spec_hash` was *optional* at the schema level, and the schema could not infer which checks are LLM-judged (for those, the prompt IS the predicate — there it must be required). A spec-less id still sealed byte-valid receipts, and a rubric and a paraphrase collided under it, forever. The enforcement lived one layer up, as a deployment contract — the same split as our single-key receipts: a labeled weakness beats an invisible one. Randal's fixture found the seam between the schema and the deployment. Update, the day after: the seam closed where it belonged — receipt v0.2.2 made the hash mandatory at the schema, credited to Reid and howcani, who pushed on it in the comments. The admitted weakness lasted a day. That is what a good attack catalog is for.

**SCAR-PROC-89, the farmed oracle → the omission, or the trail.** Unjournaled rounds are the two-party omission: `unlogged_attempt` surfaces the verdict that arrived with no sealed history behind it. Journal every round and the farming stops being hidden — it becomes *auditable*: the sealed reconciliation report counts the rounds. You cannot claim first-shot against your own ledger.

**SCAR-PROC-110, the forged verdict → provable, and a gap that closed in public.** The journal cannot un-happen events. The forged APPROVED binds the mid-run transcript digest as its witness; the terminal lands later with a different digest; the sequence is on the record. The forgery is provable from sealed evidence alone — the verdict bound a state that did not exist yet. What the journal did *not* do was auto-surface it: the reconciler paired a decision to its *first* outcome, and the forged one is first. The gap got a name (`verdict-predates-terminal`), and it shipped fixed while this post was being written: pairing now reads the terminal, not the first outcome. The doctrine closes it by construction — seal the terminal transcript *before* the verdict, the way `waitpid()` would force you to. Order of operations as a moral.

## The score, not the slogan

Three caught. One provable — and the gap it exposed shipped fixed while this post was being written. One deployment-contract gap admitted in writing, in the test that demonstrated it — closed at the schema the next day, credited to the two readers who pushed. That is the protocol we set before replaying: the suite asserts what the layer *does* — catches the attack, or confesses. "The next critic is the next ADR" only works if the critic can read.

## Update: the critic read it back

Before this could even post, the loop closed once on its own. Randal read `test_scar_replay.py` and Issue #53 top to bottom — his words, "this made my whole weekend." All four results stood from the outside, and he read the named gap exactly as written: a real decision-to-first-outcome pairing race in the reconciler. He called it "the ultimate validation of cross-stack systems physics," and the suite and the issue are going into his IN_THE_WILD_PROMPTS.md research registry — Part 3.8, on why 1970s plumbing behaves like physics inside the weights, went [live](https://dev.to/gde/what-llms-know-that-you-dont-know-they-know-stop-inventing-prompt-dsls-and-ride-50-years-of-2bl6) this morning.

And it is not two roads anymore. Mike Mol's [nemik](https://github.com/mikemol/nemik) harness reaches the same instrument from a third direction: prose rules drained into policy gates, and no rule deleted until a "Negative Witness" — a real tool-call payload replayed with the exception removed — provably returns deny. Three teams, three stacks, one invariant. By Randal's own criterion, that is physics.

The race he confirmed did not wait for him: promised in the thread at 20:03 UTC, `verdict_predates_terminal` was on main at 20:04 — pairing reads the terminal, and the test count moved with it. The catalog graded its first gate, and the gate moved before the ink dried.

And the week refused to stop there. A fifth fixture landed — SCAR-114, the parallel-call race, watched by a canary witness that replays a real tool-call payload with the exception removed and expects deny. A `coverage_check` now reconciles every write against a gate receipt, from an issue opened by Sina Rezaei — the "AI should propose, systems should verify" essayist, now inside the loop. Receipt schemas v0.2.2 and v0.2.3 shipped, and release 0.11.0 went out the door titled "the audit-proof week."

## What else landed this week

The week got away from us: cross-chain reconciliation shipped (consumption edges between journals, partial order instead of a global timeline, a supersede event that propagates a blast radius as a precise path set) — that is ADR 024, built by iteration out of another comment thread. The audit-pack now labels every event class with its evidence grade and the obligation that backs it — *obligation, not immunity*; a log is evidence OF a duty, never a shield from one. And MCP toolsets got the lockfile nobody writes: the tool descriptions your model reads are instructions, they ride outside the image pin, and now they get sealed as a reviewed baseline and diffed at every session start. Randal's world, one ADR over.

25 ADRs. 303 tests passing. Release 0.11.0 — the audit-proof week. The catalog is in the repo as `test_scar_replay.py` — attack it from there.

## Update: the descent

The title counts Randal's catalog: four. The catalog stays four. What changed since this went up is where the same shapes kept turning up — one floor down, then another — until the descent had a table of its own.

howcani came back with a validator instead of a reading. The omission path fell first: a receipt that never states who judged seals byte-identical to one that honestly does. The join behind it fell second: both sides of the label check came from the same store, so it caught the inconsistent agent and was blind to the consistent one that never journals. Release 0.12.0 closed that ceiling the same night — the transport layer witnesses the labels, and absence became a missing event, not a missing negative. The next probe caught the fix's own default, a reconciliation called without signers sealing CLEAN; it closed as receipt v0.2.5 — the probe's four-row matrix shipped as the acceptance test, and an input nobody vouches for reads `independence_undecidable`, never clean.

Then the rungs: the registrar pinned out-of-band, so arriving first wins nothing (0.14.0); the key material out of the filesystem, into a signing daemon whose floor was named in this very comment section (0.15.0); the key meeting hardware (0.16.0); the custody mode disclosed instead of implied (0.17.0); `checked` meaning a gate was configured and this peer passed it (0.18.0); the strongest token in the vocabulary re-derived from code, never the sentence that carries it (0.19.0 — the seventh premise); and the custody grade itself, the retention floor conceded in this thread, priced, sealed, and monitored (0.20.0). Every rung is the version a named probe describes, the auditor credited by name.

The numbers in the section above belong to their week. The table the descent built lives one post over — [The Authority Ladder](https://dev.to/slabb/the-authority-ladder-five-rungs-down-four-premises-standing-4p5f) — and it ends the way this one does: the next probe is already invited.

## Update: the other half

A fourth arrival, this one at the other half of the seam. You-An Lin's [*Capability Is Not Authority*](https://doi.org/10.5281/zenodo.23315265) (Zenodo, Oct 12) builds what this post's ladder only implies: the distinction between who *wrote* a record and who was *entitled to originate the act* it records. Its load-bearing finding is our check-vs-proof seam one floor up: a live agent correctly attributed foreign history to another actor while already using it — attribution correct, admission invalid, every output-level metric green.

The paper also runs the Level-0 experiment for us: an ownership contract written in prose measured nothing at ceiling (parity with the generic baseline), which is why its eight non-promotion laws land in this repo as schema, not rubric — `admission/0.1`, sealed like every other surface ([ADR 026](https://github.com/noirebox/noirebox/blob/main/docs/ADRs.md)). Lin asks (§6.3) for an admission-sensitive benchmark — admission rights and actor identity varied at a fixed task, graded on the path rather than the answer text. The fixtures are next.

## Reproduce

```bash
git clone https://github.com/noirebox/noirebox && cd noirebox
pip install -e . && pip install pytest
python -m pytest tests/test_scar_replay.py -v   # the catalog, replayed — five fixtures since
python demo/demo_mcp_toolset.py                 # the lockfile, demonstrated
