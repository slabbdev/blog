---
titre: "L'échelle d'autorité : cinq barreaux plus bas, quatre prémisses toujours debout"
date: 2026-10-13
themes: agents, preuve
resume: "Quand un agent se bloque, qui décide ? Cinq niveaux d'autorité passés au crible, quatre prémisses qui survivent."
source: https://dev.to/slabb/the-authority-ladder-five-rungs-down-four-premises-standing-4p5f
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Foxnzddq2n9t2q3i03al6.png
image_alt: "L'échelle d'autorité : cinq barreaux plus bas, quatre prémisses toujours debout"
---


> 🇬🇧 **Cet article n'est pas encore traduit** — la version originale en anglais suit. La traduction arrive.

> A ladder exists to be climbed. This one is built the other way: every rung down leaves fewer candidate writers, and the only descent that matters is an attacker's. The audit descends first, on purpose — because whoever descends it second is the threat, and the premises table at the end exists to measure exactly how much ladder they would still have left.


My last post ended with an invitation: here is a reconciliation layer, here is a catalog of gate attacks replayed against it as tests — attack it from there. A reader took the invitation literally. In the comments, [howcani](https://dev.to/slabb/a-hash-chain-proves-the-ordering-four-attacks-prove-its-not-enough-59oe#comment-3hj95) probed every rung I claimed, found the one seam I had confessed but not closed, and pushed until it closed at the schema. What came out of that thread is now a page in the repository: [the authority ladder](https://github.com/noirebox/noirebox/blob/main/docs/AUTHORITY-LADDER.md) — [PR #87, merged](https://github.com/noirebox/noirebox/pull/87) — and this post is that page, in post form, because the method behind it deserves as much air as the result.

The method has a property that matters more than any single finding. The frame came from Randal L. Schwartz — Unix primitives, gate attacks, a catalog built from real failures. The probes came from howcani — run the validator, name the seam, demand the ceiling. The closures came from me and from agents, in code. Human frame, LLM probes, agent closures — three species, one descent, the same rungs found. When reviewers that share no priors descend the same structure and hit the same floors, the rungs stop being taste. They become physics.

## The one-sentence setup

The journal proves ORDER and INTEGRITY: a hash chain, externally anchored, tamper-evident. It deliberately does not know WHO the writer is. The ladder answers that question one rung at a time — and each rung below states what it sees, what it closed, the residue it exposed, and the test that bites.

## Rung 0 — the caller's argument

The labels supplied at check time: `signers=[(k1, "agent"), (k2, "hook")]`, the domain strings, the event types. Vocabulary, not evidence — the party under audit wrote it.

What it closed: nothing. Rung 0 is where audits start. The verdict used to read these labels, which meant an attacker row — identical key material, one relabelled — moved the verdict.

Closed by v0.2.5: **the verdict reads keys, not labels**. The attacker row is pre-registered as an immobility test — `test_attacker_row_labels_never_move_the_verdict`. Relabel identical key material and nothing moves. The caller's vocabulary certifies nothing.

## Rung 1 — the signature

The Ed25519 signature on each event: the journal's own key material, resolved by verification, never by name.

What it closed: the transport-writer invariant — a "deterministic" label is only verified by an attempt sealed by a writer the agent does not control; absence of one is `unverified_label`. And the unresolved receipt writer is `independence_undecidable` — undecidable is **never clean**.

The residue it exposed: two distinct keys, one owner — invisible to any amount of key material. And the key itself was a file on disk. Both residues live higher up the ladder.

## Rung 2 — the sealed registry

The known-writers registry: every writer's domain declared at registration, before any run the writer could influence, and sealed into the journal. The caller now supplies nothing — registry mode resolves keys and domains from the sealed registry.

What it closed: the caller's labels demoted to decoration — the registered domain decides, tested as `test_writer_registry_overrides_the_callers_labels`.

The residue, found by howcani at [3hj95](https://dev.to/slabb/a-hash-chain-proves-the-ordering-four-attacks-prove-its-not-enough-59oe#comment-3hj95): the registry assembly was store-derived and `setdefault` made **first-write-wins** the registrar — the agent could seal its own `writer` entry and win the vote by arriving first; the operator's honest attestation, arriving second, sat inert. A correlation rule standing in for an authority rule. Found at the head, in public, by a probe.

## Rung 3 — the pinned registrar, the floor of evidence

`registrar_public_hex` on the reconciliation call (v0.2.7): the operator's key, supplied **out-of-band** — the same pattern as the TSA roots in ADR 008, never read from the artifact under audit. The registry assembles from registrar-sealed entries only. Order no longer decides anything.

The registered prediction, run and held: at the pinned head, the operator's attestation landing second reads `unverified_label` — not clean, with the finding beside it. "The vote moved; the finding did not merely report." The test: `test_v027_write_race_agent_first_operator_second_reads_unverified`.

And this rung is **the floor** — the point where the artifact stops being evidence about the agent and becomes trust in the operator. The honest output is a grade, not a verdict: `registry_disclosure()` states the registrant and the evidence grade — grade 3, "anchored self", voluntary unless a regime imposes it. Sealed into the report; never folded into `clean_pass`, because a disclosure is not a violation — it only stops a clean verdict from pretending to rest on more than the operator's own custody.

The premise it carried, from howcani at [3hif9](https://dev.to/slabb/a-hash-chain-proves-the-ordering-four-attacks-prove-its-not-enough-59oe#comment-3hif9): the pin names who makes authority, but the operator's key was still a file on disk — *"what stands on it is a premise, not a cipher."* An agent that can read the file can use it. That residue is custody, not evidence. One rung down.

## Rung 4 — the keyholder (custody, not evidence)

Release 0.15.0: the key material loads once into a dedicated daemon and never leaves it. A unix socket answers `sign` and `describe` — nothing else, no export operation, an oversized request ends in disconnection. Every writer path signs through the daemon unchanged: Ed25519 is deterministic, the signatures are byte-identical, and every existing verifier reads the journal as before. `--allow-uid` gates the peer by uid and **fails closed** where the peer is not checkable.

What it closed: readability of the key bytes. `cat journal.key` stops being an attack — the bytes are not on any path the agent can read, and after start, the PEM can be removed from the agent-reachable volume entirely.

The premise, re-priced: reachability of one socket path replaces readability of the key bytes. A deployment that wants "the agent cannot sign" mounts everything except the socket. Where agent and operator share a uid and the socket, the gate is the filesystem's — stated, not hidden.

Rung 5 shipped this week, [release 0.16.0](https://github.com/noirebox/noirebox): HSM signing rides the same signer interface — the key never leaving hardware is the same move, one rung further down.

![The authority ladder: six rungs, each closed by a named test](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/4z5ojbq7j6lq92dql1vx.png)

## Where the ladder ends

Below the pinned registrar there is no crypto left to invoke — only deployment assertions and the honesty rules that make them auditable:

- **undecidable is never clean** — an unresolved writer, a contested key, an uncheckable peer: each reads as a named state, never as silence.
- **a skipped check is reported, never folded into clean.**
- **disclosure is not violation** — the verdict states the registrant and the grade; `clean_pass` means "no findings", not "no premises".
- **the premises are on the table** — the next section is the table.

## The standing premises — the table the next probe reads

| # | premise | what it narrows to | named in |
|---|---|---|---|
| 1 | the registrar pin is supplied out-of-band, by the deployment | the deployment's word on one key | ADR 021, §17 |
| 2 | the keyholder socket is reachable only to those the filesystem and uid gate allow | one path, gated where the platform can check | ADR 020 amendment |
| 3 | agent and operator do not share uid and socket | a container/mount assertion — reachability, not readability | ADR 020 amendment |
| 4 | no hardware root under the signing key | HSM/PKCS#11, same signer interface — interface shipped, the silicon still owes the closure | release 0.16.0 |
| 5 | the custody MODE is a disclosure field, not a proof — the journal cannot tell in-process from socket from token | `signer_mode` + `uid_gate` in the disclosure, null when unstated | release 0.17.0 |

The next probe starts here. This table is the diff between what the ladder proves and what it assumes — and it is public on purpose, because the fastest way to find rung 6 is to hand the premises to someone who does not share my priors.

## Two honest limits

**The ladder is my map of my own code.** The probes were external — howcani descended at the head, found the write race, named the floor — but every closure is mine, and a self-audit grades on a curve that only external review corrects. The tests are public and bite at the head; the curve is the part they cannot fix.

**And the descent has a floor by design, not by completion.** Rung 5 narrows premise 4; premises 1–3 stand. A ladder of custody never reaches a rung labeled "trustworthy" — the taxonomy exists to prevent pretending it terminates anywhere stronger than the operator.

## Your turn

The page is [in the repo](https://github.com/noirebox/noirebox/blob/main/docs/AUTHORITY-LADDER.md), the tests are in the tree, and the premises table is the invitation. If you build gates: descend yours, grade your rungs, publish your premises — the format is one table, and the method is species-blind, which means it works on your stack too. The next rung anyone finds is a pull request away.

**Update 3 — the probe took rung 4 seriously, and the ladder grew a row** (hours later)

The method keeps running. howcani took the custody rungs to the tags ([3hkpp](https://dev.to/howcani_howcani_77e786a89/comment/3hkpp)): the drop-in holds byte-identically from another process — and that IS the finding. The journal cannot tell custody modes apart, by design: a writer event sealed through the keyholder reads exactly as one signed in-process. On darwin the uid gate is **unusable rather than unsafe** — it refuses, fail-closed — and the socket's 0600 separates **users, not processes**. Rung 4's residue is rung 3's sentence with one noun changed: the assertion is no longer "the agent cannot read the key material" (that half is genuinely closed — there is no export op) but **"the agent does not run as the operator's uid."**

So the premises table above grew a fifth row, and release 0.17.0 ships it: `registry_disclosure(signer_mode=..., uid_gate=...)` — null when the caller states nothing, derived from the daemon's own `describe()` instead of asserted. The registered prediction held at the tag: over a keyholder-signed journal, the disclosure reports `uid_gate: unavailable(darwin)`. And the token PIN left argv — `NOIREBOX_HSM_PIN` carries it now, because an argument PIN sits in the process table, readable via `ps`.

This post is a snapshot; [the page](https://github.com/noirebox/noirebox/blob/main/docs/AUTHORITY-LADDER.md) is the living map. The fastest way to find rung 6 is still to hand the premises to someone who does not share our priors.
