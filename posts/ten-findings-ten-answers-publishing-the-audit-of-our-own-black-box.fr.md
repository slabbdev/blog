---
titre: "Dix constats, dix réponses — publier l'audit de notre propre boîte noire"
date: 2026-10-15
themes: agents, preuve
resume: "Dix failles trouvées par l'audit de NoireBox, dix réponses publiques. Publier ses vulnérabilités, receipts à l'appui."
source: https://dev.to/slabb/ten-findings-ten-answers-publishing-the-audit-of-our-own-black-box-1d29
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fn9aub8arzgn5jbpnmy5i.png
image_alt: "Dix constats, dix réponses — publier l'audit de notre propre boîte noire"
---


> 🇬🇧 **Cet article n'est pas encore traduit** — la version originale en anglais suit. La traduction arrive.

Ten findings, ten answers. That is the entire release note of [NoireBox 0.21.0](https://github.com/noirebox/noirebox/releases/tag/v0.21.0) — and it is the part of this month I am simultaneously proudest of and least comfortable with.

The context: NoireBox is a flight recorder for AI agents — every decision an agent takes is sealed into a hash-chained, externally anchored, tamper-evident journal. A product whose entire pitch is "you can trust what this records" has an obligation the pitch implies and can easily forget: **it must survive its own audit.** A recorder that audits everyone's agents but hides its own vulnerabilities is [the witness-was-the-suspect problem](https://dev.to/james_anderson_h/the-witness-was-the-suspect-why-ai-audit-logs-cant-be-trusted-2190) applied to ourselves.

So we commissioned an external audit: line-by-line inspection of the v0.20.0 archive. It came back with **ten findings** — three high, five medium, two low — each with its file, its line numbers, and its attack path. Every finding is now public, in the audit commit, in the release notes, and in this post. Including the ones that sting.

## The measured audit

The severity distribution, exactly as reported — no crypto was broken (the Ed25519 core held), but the logic around it bled:

| Finding | Severity | One line |
|---|---|---|
| NB-01 | high | JWT secret desync: a malformed env var silently fell back to the public demo credentials `demo:demo-secret` |
| NB-02 | high | the third-party verifier fail-opens: missing openssl or ots on the machine → `return True` |
| NB-03 | high | custody-drift bypass via a forged anchor event, and a terminal-records overwrite that could swallow a proven race |
| NB-04 | medium | SSRF: an IPv4-mapped IPv6 address walked past the link-local check |
| NB-05 | medium | Merkle tree collisions: odd-leaf duplication and no RFC 6962 domain separation |
| NB-06 | medium | DoS: unbounded `EventIn` payloads plus `store.all()` re-verifying the whole journal per public GET |
| NB-07 | medium | no rate limiting on the token endpoint, and an unbounded rate-limiter memory |
| NB-08 | medium | `joblib.load()` deserialization without a prior SHA-256 check |
| NB-09 | low | the container ran as root, listening on 0.0.0.0 |
| NB-10 | low | tool inputs sealed into the immutable journal unredacted — secrets included |

Ten findings across auth, verification, networking, cryptography-adjacent logic, resource handling, and secrets handling. None broke the cryptography. All of them were real. **[The report](https://github.com/noirebox/noirebox/releases/tag/v0.21.0) cites file and line for each** — the auditor's receipts, not adjectives.


## Three findings, three answers

**NB-02 is the one that should frighten every builder of verification tooling.** The third-party verifier fail-opens: if `openssl` or the `ots` tool is missing on the machine, the check returns `True` with the string "reported, not hidden." Any CI/CD pipeline validating a journal inside a distroless container — no openssl, no ots — would validate a journal whose timestamp tokens were completely forged, `"tsr": "AAAA"`. The verifier that reports "not verified" as a *pass* is the most dangerous line in the file: it converts an absence of tooling into a presence of trust.

The answer in 0.21.0: unverifiable witness tokens exit **2**, never the clean 0. The project's doctrine — *undecidable is never clean* — now applies **to the tool that enforces it too**. Legacy pipelines that need the old behavior pay for it explicitly: `--allow-unverified-witnesses` or `NOIREBOX_ALLOW_UNVERIFIED_WITNESSES=1`. The escape hatch survives; it is priced.

**NB-03 is the one that proves the premises table works.** The audit found that a forged anchor event — `{"head_seq": 999999, "head_hash": "faux"}`, no timestamp authority — would pass the custody grader unnoticed, and that a non-terminal record could overwrite a proven `verdict_predates_terminal` race, making the finding vanish. Both closed in 0.21.0: the anchor input now validates the cited head hash and token presence, and the non-terminal overwrite surfaces as `post_terminal_activity`. Each fix carries its own named test.

**NB-01 is the one every demo-mode product should read.** The JWT secret desynced from the loaded key, and a malformed `NOIREBOX_CLIENTS` env var silently fell back to the public demo credentials — the operator believed authentication was on; the app had switched to `demo:demo-secret`. The answer: the app now refuses to start rather than guess, and the secret derives from the key actually loaded. Fail loudly at startup beats fail quietly at request time.

The full mapping — all ten findings, all ten answers, version by version — is in [the release notes](https://github.com/noirebox/noirebox/releases/tag/v0.21.0). Every fix carries its own named test: **392 collected** at release time.

## The species-blind argument, again — with better data

Last week's audit arc (an external reader descending our reconciliation layer) proved the method on a sample of one probe. This audit is the second data point, from a different species of reviewer: a line-by-line inspection agent rather than a human prober. Two external entities, two methods, same conclusion: **external entities find what internal reviews confess and defer.** The internal review had labeled NB-02's weakness in writing; it took the external pass to make its closure a release blocker. [McGraw's advice](https://www.csoonline.com/article/4234854/containment-and-monitoring-failures-are-to-blame-for-ai-hacking-reports-experts.html) — "get an external entity to help" — is not consulting wisdom. It is the mechanism by which the ladder grew its floor.

## The code, verbatim

Four excerpts from v0.20.0, unchanged. First, the verifier that reports "not verified" as a pass — two functions, same shape:

```python
# verifier/verifier.py
def verify_anchor_token(...):
    if not shutil.which("openssl"):
        return True, "openssl missing — token not verified (reported, not hidden)", False

def verify_ots_token(...):
    ...
    except subprocess.TimeoutExpired:
        return True, "ots verify timed out (reported, not hidden)", False
```

Second, the register a race can zero — the custody grader trusted whatever anchor arrived last, without checking that its hash matched the real event:

```python
# noirebox/reconcile.py
def _newest_anchor(events: list[dict]) -> dict | None:
    newest = None
    for e in events:
        if e.get("type") == "anchor":
            seq = e.get("payload", {}).get("head_seq")
            if seq is not None and (newest is None or seq > newest["head_seq"]):
                newest = {"head_seq": int(seq), ...}
```

Third, the premise under the JWT: the secret reloaded from a hardcoded path on every request, ignoring the key the app had already loaded — plus the fallback clients dict:

```python
# noirebox/auth.py
DEFAULT_CLIENTS = {"demo": "demo-secret"}

def _jwt_secret():
    ...
    key = KeyPair.load_or_create(
        os.environ.get("NOIREBOX_DB", "data/noirebox.db") + ".key")
```

And the deserialization with no integrity gate:

```python
# noirebox/ml_guardrail.py
_pipelines[lang] = joblib.load(path)
```

Read them in that order and the severity calls grade themselves: two fail-opens that answer "trust me", one race with no validation, one hardcoded path, one pickle. None subtle. All shipped for months — which is the part the next audit is for.

## What to steal — the pattern, generalized

- **Commission an external line-by-line audit of your own tool, on the current version, before someone else does it for you.**
- **Publish the findings with file, line, and severity** — the auditor's receipts, not your summary of them.
- **Answer every finding in one release**, each answer carrying its own named test — "ten findings, ten answers" is a sentence a user can verify in an evening.
- **Keep the premises table public.** The findings your answers did *not* close, the assumptions your controls rest on, the hardening deliberately deferred — labeled, public, falsifiable.

## Two honest limits

**The auditor was an agent we commissioned, on a version we chose.** An n=1 external probe with a scope we set is not the same as a red team with its own budget and its own grudge. And every finding was logic-level — the Ed25519 core held, no cryptographic break — which is both genuinely good and partially luck of scope.

**And "ten answers" is young.** Release 0.21.0 is days old; 392 tests collected is a snapshot, not a track record. The real test of "ten findings, ten answers" is the *next* audit — whether the new premises table holds, and whether the answers aged into defenses or into new residues. That audit is already scheduled. Its findings will be published too — that sentence is the commitment, and now it is on the record.

## Your turn

[The audit findings](https://github.com/noirebox/noirebox/releases/tag/v0.21.0) are public, [the answers](https://github.com/noirebox/noirebox/commit/45ebbe61) are in the repo, and [the premises table](https://github.com/noirebox/noirebox/blob/main/docs/AUTHORITY-LADDER.md) names what still stands. If you ship anything agents touch — audit it externally, publish the findings with your answers, and link both. The registry of published self-audits in this lane is empty. Being first costs one uncomfortable week. Being second costs the excuse.
