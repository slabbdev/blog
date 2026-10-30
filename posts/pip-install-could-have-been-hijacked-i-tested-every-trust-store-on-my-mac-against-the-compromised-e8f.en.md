---
titre: "pip install could have been hijacked: I tested every trust store on my Mac against the compromised eMudhra chain"
date: 2026-10-30
themes: securite, python
resume: "The eMudhra keys that were 4, 56 and 115 could have signed a fake pypi.org and turned pip install into arbitrary code delivery. The Python ecosystem fixed itself in five days. The four-way live test: Apple's tools still accept the chain, Python refuses it."
source: https://dev.to/slabb/pip-install-could-have-been-hijacked-i-tested-every-trust-store-on-my-mac-against-the-compromised-e8f
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Ffmel0dbnbm52q7adut1c.png
image_alt: "pip install could have been hijacked: every trust store tested against the compromised eMudhra chain"
---

> The writeup that landed tonight ([OpenTeams: "Pip Install Could Have Been Hijacked"](https://openteams.com/engineering-blog/emudhra-pip-install-hijacked/)) closes a loop this blog opened ten days ago. The eMudhra intermediate keys, the ones where ["the key was the number 4"](https://dev.to/slabb/a-ca-private-key-was-the-number-4-your-curl-still-trusts-it-cve-2026-111943-45o4), were recoverable by anyone: Scott Helme pulled all eight "on a laptop in under a second". Values included **4, 56 and 115**. Tonight's post spells out what that meant for Python: anyone on your network path could have forged a certificate for `pypi.org`, and your next `pip install` would have happily delivered their package. Browsers would have caught it. **Python tools never look at the logs that would have caught it.** So I ran the full test on my own machine, every trust store, one host: same Mac, same hour, split verdict.

## The chain, one paragraph

Recover a weak CA key (act one of this series). Forge a certificate claiming to be `pypi.org`. Sit on the network path: cafe Wi-Fi, a compromised router, an ISP. When a developer runs `pip install requests`, serve the forged certificate and a malicious package or wheel. Only installs pinned to exact file hashes would have noticed the swap. And because Chrome and Safari require certificates to appear in public Certificate Transparency logs while `pip`, `requests` and friends do not consult them at all, **this attack would have left zero traces anywhere**. No exploitation has been documented. The feasibility proof is the key recovery itself, which takes under a second.

## The five-day counterattack

The part of tonight's post that deserves to be remembered is the response timeline, because the Python packaging ecosystem fixed itself in five days flat:

- **Oct 17**: report reaches Google and Mozilla.
- **Oct 20**: Chrome blocks the certificates in under two hours, Firefox by 22:59 UTC. The Python Software Foundation advisory goes out; fixed `certifi` (2026.10.19), `pip` and `uv` releases ship.
- **Oct 21**: conda, mamba and pixi fixes, plus a conda-forge index edit so that even old installs pull fixed certificates.
- **Oct 26**: new CPython releases, 3.15.2, 3.14.10, 3.13.18, 3.12.16, 3.11.18, **block the keys inside the `ssl` module itself**, which protects even old pips running on new Pythons.

One vendor is conspicuously absent from that list, and the omission is the subject of a [separate finding](https://emudhra.we-have-a-problem.com/apple.html) this blog also covered: Apple's own git, on the same machine, was still accepting the chain days later. The volunteers beat the trillion-dollar company by a week, and the gap is measurable on my desk.

## The four-way test, run live

The method: ask each trust store what it thinks of `https://dv-g3b-emudhra.we-have-a-problem.com/`, the official check host whose certificate chains through one of the compromised intermediates. A certificate error means protected. A response means the store still trusts the poisoned chain.

**1. Apple's git, the system toolchain** (from my earlier test this week, same machine, never fixed since):

```text
$ git -c http.curloptResolve=github.com:443:15.235.19.186 clone \
      https://fake-user@github.com/galadran/emudhra-git-test
# README fetched: "INTERCEPTED: your git accepted a certificate from a compromised eMudhra CA"
```

**Vulnerable.** A fake github.com was cloned without one warning.

**2. Python's stdlib, `urllib` + `ssl`:**

```python
import urllib.request
urllib.request.urlopen("https://dv-g3b-emudhra.we-have-a-problem.com/", timeout=15)
# ssl.SSLCertVerificationError: CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate
```

**Protected.** The Homebrew OpenSSL bundle under this Python already dropped the roots.

**3. pip itself, against a compromised-signed package index:**

```text
$ python3 -m pip download --no-deps \
    --index-url https://dv-g3b-emudhra.we-have-a-problem.com/simple/ definitely-not-a-real-package
WARNING: ... SSLError(SSLCertVerificationError('Le certificat «dv-g3b-emudhra...» est bloqué.'))
```

**Protected.** The error message literally says *blocked*. Note this pip is 26.2.1, one patch below the recommended 26.2.2, and its vendored `certifi` bundle already lacks both affected roots (checked by grepping `pip/_vendor/certifi/cacert.pem`: `emSign ECC Root CA - G3` absent, `AAA Certificate Services` absent). **The update advice still stands**, because the explicit block in pip 26.2.2 and in CPython's `ssl` (3.15.2+) defends even when a bundle slips, and my machine's *system* `certifi` is 2026.07.22, two releases behind the fixed 2026.10.19.

**4. Your applications, via `requests`:** whatever `import certifi` resolves to in each virtualenv. On this machine the system `certifi` 2026.07.22 greps clean for both roots, but per-venv copies vary, and this is the one layer nobody updates. That is the check your CI should own.

Four stores, one machine, one hour: **Apple's stack accepted the forged chain, the Python ecosystem refused it.** The difference is not talent, it is that packaging maintainers treated a CA compromise as their incident, and shipped.

## The audit for your machines

```bash
# every interpreter you care about: does it still trust the chain?
python3 -c "import urllib.request
try: urllib.request.urlopen('https://dv-g3b-emudhra.we-have-a-problem.com/', timeout=15); print('VULNERABLE')
except Exception as e: print('protected:', type(e).__name__)"

# pip's vendored bundle (both greps must be empty)
grep -c "emSign ECC Root CA - G3\|AAA Certificate Services" \
  "$(python3 -c 'import pip,os;print(os.path.join(os.path.dirname(pip.__file__),"_vendor","certifi","cacert.pem"))')"

# the versions that matter: pip >= 26.2.2, certifi >= 2026.10.19,
# uv >= 0.13.4, pixi >= 0.82.1, conda >= 26.9.4, CPython latest patch (ssl-level block)
python3 -m pip --version; python3 -c "import certifi; print(certifi.__version__)"
```

And the two operational notes from tonight's post worth pinning on the wall: rebuild container images and CI caches from scratch, because every layer carries its own frozen copy of the roots; and **never disable certificate verification to silence an error**, the single most common self-inflicted downgrade that turns a trust-store incident into an open door.

## Why this story is the good twin of the whole month

October gave us a steady parade of broken pipelines: disclosure lists leaked, embargoes broken, updates that undo manual fixes, extensions that backdoor you at load. This one is the mirror image: a catastrophic CA failure, and a loosely-coordinated ecosystem of volunteers and maintainers that **enumerated its own blast radius correctly** (pip, requests, uv, pixi, conda, CPython, Docker images, installers), then closed it in five days, then published the retrospective. The moral of the month is not that everything is broken. It is that the difference between disaster and non-event is whether somebody owns the inventory. Python packaging owned its inventory. Your stack's question is: who owns yours?

**TL;DR**: the eMudhra keys (values 4, 56, 115) could have signed a fake `pypi.org`, and `pip install` would have delivered attacker code with no traces, because Python tools do not check CT logs. The ecosystem fixed itself in five days, down to blocking the keys in CPython's `ssl` module. My four-way live test: Apple's git still accepts the chain, Python's stdlib, pip and bundles refuse it. Audit commands above, version pins in the post, rebuild your caches.

Sources: [OpenTeams: Pip Install Could Have Been Hijacked](https://openteams.com/engineering-blog/emudhra-pip-install-hijacked/) · [eMudhra disclosure + check hosts](https://emudhra.we-have-a-problem.com/) · [Act one: the number-4 key](https://dev.to/slabb/a-ca-private-key-was-the-number-4-your-curl-still-trusts-it-cve-2026-111943-45o4) · [Act two: the CA exits the business](https://dev.to/slabb/the-ca-whose-private-key-was-the-number-4-just-quit-the-certificate-business-18ba) · [Apple's git still trusts the chain](https://emudhra.we-have-a-problem.com/apple.html)