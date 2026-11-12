---
titre: "Apache httpd shipped a critical HTTP/2 RCE yesterday, and one of the finders was a machine: CVE-2026-119618 and the three-gate audit"
date: 2026-11-12
themes: securite, web
resume: "mod_http2 race in assign_headers(), heap corruption, RCE: 2.4.55 through 2.4.70 affected, fixed in 2.4.71 released yesterday. Apache's own acknowledgements credit Anthropic's OSS Scanner as finder. My Mac runs 2.4.67, in the vulnerable range, and the three-gate audit explains why it is still safe."
source: https://dev.to/slabb/apache-httpd-shipped-a-critical-http2-rce-yesterday-and-one-of-the-finders-was-a-machine-5jj
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2F11jiig095nautznwk511.png
image_alt: "Apache httpd critical HTTP/2 RCE: CVE-2026-119618 and the three-gate audit"
---

> Yesterday, Apache released httpd 2.4.71 with three CVEs, one of them critical: **CVE-2026-119618, heap corruption and RCE in `mod_http2`**, a race condition in `assign_headers()` triggered by concurrent HTTP/2 requests on shared resources. Affected: **every httpd from 2.4.55 to 2.4.70**, and per Wiz's telemetry, **64% of cloud environments contain a vulnerable instance and 51% have one publicly exposed**. And the detail that closes a loop this blog opened yesterday: in Apache's own acknowledgements, the first finder listed is **"Anthropic's OSS Scanner, as vulnerability ANT-2026-MAPKT6MZ"**. Twenty-four hours ago this space audited that scanner's noise curve (curl: 45 reports, 56% rejected). Today, its signal: a critical remote code execution in the most-deployed web server on earth. Both things are true, and that is exactly the point.

## The vulnerability, precisely

From the [official advisory](https://httpd.apache.org/security/vulnerabilities_24.html): a **concurrent execution using shared resources with improper synchronization** flaw in `mod_http2`'s `assign_headers()`. Multiple HTTP/2 streams hitting the header-assignment path concurrently can corrupt the heap, and heap corruption in a preforked server is a code-execution primitive. The requirements:

- **HTTP/2 enabled** (the module loaded and `h2` in the `Protocols` directive, directly or via ALPN)
- versions **2.4.55 through 2.4.70** of httpd, or the standalone `mod_h2` GitHub builds 2.0.8 through 2.0.42
- fixed in **2.4.71** (released November 11) and mod_h2 beyond 2.0.42

No public exploit, no observed in-the-wild exploitation yet. With a patch out, an internet-facing h2 server on an affected version is now running a countdown: the advisory, the Wiz writeup and the fix diff are all public, and history says weaponization of httpd flaws is measured in days-to-weeks, not months.

The interim mitigation if you cannot upgrade today is one line in `httpd.conf`: `Protocols http/1.1` (removing `h2`/`h2c` from the negotiated protocols closes the vulnerable path at the cost of HTTP/2's performance). That trade is almost always correct for 48 hours.

## The three-gate audit, run live on my Mac

"Is my server vulnerable" for this CVE is the AND of three conditions, and each is one command. My laptop turned out to be the perfect teaching case: **its httpd is version-flagged yet not exploitable**, and here is the full output, unedited.

```bash
# GATE 1: the version (2.4.55 <= v <= 2.4.70 means flag)
$ httpd -v
Server version: Apache/2.4.67 (Unix)          # <- IN THE AFFECTED RANGE
Server built:   Oct  6 2026 20:57:44           # <- Apple's bundled build

# GATE 2: is the vulnerable module even loaded?
$ httpd -M | grep -i h2
(no output)                                     # <- mod_http2 NOT loaded

# GATE 3: is h2 negotiated, and is anything listening?
$ grep -rn "^Protocols" /etc/apache2/httpd.conf # <- no h2 configured
$ lsof -iTCP -sTCP:LISTEN -P | grep httpd       # <- not listening at all
```

Verdict: version-flagged, module absent, daemon idle: **not exploitable as configured, patch anyway at the next maintenance**, because configurations change and yesterday's exposure is not today's. Note gate 1's fine print for Mac users: Apple bundles httpd and builds it late (this 2.4.67 shipped **October 6**, five versions behind within a month), so macOS servers and CI images inheriting `/usr/sbin/httpd` will trail 2.4.71 for a while. Brew or a container image you control beats the bundle.

For every internet-facing host you own, add the remote variant:

```bash
# does your site speak HTTP/2? (if yes AND the server is Apache in range: act)
curl -sI --http2 https://your-site.example | head -1
# HTTP/2 200  -> h2 active; combine with version to conclude

# if you expose server tokens, the version comes back free:
curl -sI https://your-site.example | grep -i server
```

## Yesterday's audit, today's receipt

The Glasswing post yesterday ended on the economics: 37,966 findings, 217 fixed, maintainers buried under model-generated reports whose validation the lab had outsourced. This CVE is the other column of that ledger, in the strongest possible form:

- The finding was real, critical, and in **the** web server: heap-corrupting RCE, not a low-severity nit (the curl case's six confirms were all low).
- It was **co-found**: Apache credits both the Anthropic OSS Scanner *and* independent researchers (Anthony Weems, Simon Scannell). The machine was first on the list, humans validated the same ground.
- The disclosure pipeline worked: coordinated, patched, advisory with credits, fix out in a normal release.

So the honest ledger after two days reads: the scanner stream is majority-noise at the individual report level, and occasionally infrastructure-critical. Both facts argue for the same conclusion drawn yesterday: **validated before shipped, and the finder's organization carries the triage cost**. A machine that finds Apache httpd RCEs has earned its compute bill. A stream of 5,000 unvalidated reports has not, and the way to tell them apart is not marketing, it is exactly this kind of receipt: a CVE, a patch, a credit line.

## What to do tonight

1. **Inventory**: every httpd you run, the three gates (version, module, listening protocols). The commands above run in seconds per host.
2. **Patch to 2.4.71+** where gates 2 and 3 are open; `Protocols http/1.1` as the 48-hour bridge.
3. **Containers and base images**: `FROM httpd:*` and distro packages both need a rebuild; 2.4.55–70 has been the default in many images for two years.
4. Watch for the weaponization window: if you cannot patch, gate 3 is your firewall (no h2 for strangers), and your logs for `PRI * HTTP/2.0` lines will tell you who is probing.

**TL;DR**: CVE-2026-119618 is a critical mod_http2 race (`assign_headers()`, heap corruption, RCE) in httpd 2.4.55–2.4.70, fixed yesterday in 2.4.71, found by Anthropic's OSS Scanner plus independent researchers, with 64%/51% cloud exposure per Wiz. Risk = version AND module AND protocol, three commands per host (my Mac: flagged on version, safe on the other two). Patch, bridge with `Protocols http/1.1`, rebuild the images, and update your Glasswing priors: the noise is real, and so is this.

Sources: [Apache official advisory (2.4.71, credits)](https://httpd.apache.org/security/vulnerabilities_24.html) · [Wiz: CVE-2026-119618 analysis and exposure data](https://www.wiz.io/blog/cve-2026-119618-rce-apache-http-server-vulnerability) · [yesterday's Glasswing audit on this blog](https://dev.to/slabb/38000-ai-found-vulnerabilities-217-fixed-auditing-glasswing-anthropics-bug-discovery-machine-k65)