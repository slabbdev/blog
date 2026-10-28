---
titre: "Every page of this blog is sealed — here is how to verify it yourself"
date: 2026-10-31
themes: preuve, crypto
resume: "101 files, one SHA-256 per file, a chain, an Ed25519-signed head, a public manifest. Out-of-band verification fits in 5 lines of stdlib Python — and the same seal runs in your browser."
source: https://github.com/slabbdev/blog
---

A static blog is convenient: no database, no tracking, no app-server outage. But it is still a server answering requests — and whoever controls the server (the host, the CDN, the repo account) can silently modify a page. Nobody would notice. That is the problem this blog's seal attacks: **proving that what you download is exactly what was published at the last deploy — without asking you to trust me.**

## The mechanism

On every publish, a script ([seal.py](https://github.com/slabbdev/blog/blob/main/tools/seal.py)) does three things:

1. **It hashes every file** on the site with SHA-256 — today **101 files**, just under a megabyte total.
2. **It chains the hashes**: each file's hash also covers the previous one. Reordering, removing, or rewriting an entry breaks everything downstream.
3. **It signs the chain head with Ed25519** — the private key never leaves my machine, the public key ships in the manifest.

The result is a public [`manifest.json`](https://blog.slabb.dev/manifest.json): the list of 101 files with their hashes, the chain head, the signature, the public key, and the trust root's fingerprint — `sha256:64cba499e2568c97`. The publish script refuses to push if verification fails, so a broken chain cannot reach production.

## Verify in 5 lines

The out-of-band verifier ([verify.py](https://github.com/slabbdev/blog/blob/main/verify.py), stdlib only, zero dependencies):

```python
import json, hashlib, urllib.request
m  = json.load(urllib.request.urlopen("https://blog.slabb.dev/manifest.json"))
f  = m["files"][0]
b  = urllib.request.urlopen("https://blog.slabb.dev/" + f["name"]).read()
print(f["name"], "OK" if hashlib.sha256(b).hexdigest() == f["sha256"] else "TAMPERED")
```

That checks one file. The full script re-chains all 101, re-checks the Ed25519 signature, and prints its verdict — `INTACT` or `TAMPERED` — with nothing to install. Point it at any mirror: "is this mirror serving what was sealed?" becomes a binary question.

And if you'd rather not open a terminal: the same seal verifies **in the browser** — [noirebox.eu's inspector](https://noirebox.eu/tech.html#inspector) fetches the blog's manifest, recomputes every SHA-256 locally in WebCrypto, and even lets you simulate a tampered byte to watch the chain break live.

## What it proves — and what it doesn't

Honesty is the product, so here are the limits:

- **It proves**: what you download is byte-for-byte what was sealed at the last publish. A page modified in transit, on the CDN, or in a mirror is detectable by anyone.
- **It does not prove**: that the sealed content is *true*. A seal over a lie is a sealed lie.
- **The root is the private key** — on my machine. If it leaks, anyone can re-seal a doctored version. The countermeasure is classic: the `sha256:64cba499e2568c97` fingerprint is published out-of-band (social, profiles), so a fraudulent re-seal shows as a changed fingerprint.
- **The repo remains the referee**: the served manifest and the repo manifest can be compared; GitHub becomes the third-party witness of the last sealed state.

This is exactly the primitive [NoireBox](https://code.noirebox.eu/) applies to AI agent decisions — chained hashes, an Ed25519 signature, verifiable by a third party with no access to your systems — applied here to a blog. The simplest possible public site, with the strongest possible integrity property at zero extra infrastructure: one Python script, one key, one manifest.

Zero cookies, zero tracking — and now, zero trust required.
