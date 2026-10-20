---
titre: "The internet's root key rotates in five days. Your resolver may not be ready."
date: 2026-10-07
themes: securite, web
resume: "On October 11 KSK-2024 replaces the key that signed the DNS root for eight years. Resolvers that missed RFC 5011's window fail validation. Three checks, five minutes."
source: https://dev.to/slabb/the-internets-root-key-rotates-in-five-days-your-resolver-may-not-be-ready-3j8e
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2F5kvcaxctdozymjfnaxro.png
image_alt: "The internet's root key rotates in five days. Your resolver may not be ready."
---

On October 11 — five days from this post — the most trusted key on the internet changes hands. KSK-2017, the key-signing key that has authenticated the DNS root zone since October 11, 2018, stops signing. KSK-2024 takes over. Eight years, to the day, and the entire trust chain of DNS runs through that swap.

The schedule is not a rumor: it is [IANA's own rollover page](https://www.iana.org/dnssec/files) — published January 11, 2025, trust-building via RFC 5011 through the year, and on October 11, 2026, "the successor key is scheduled to sign the zone; the current key will not."

If you run your own validating resolver, this post is for you. If you don't, it's still for you — because the failure mode when a resolver misses this window is beautifully silent: everything looks normal, and names stop resolving.

## What is actually happening

DNSSEC chains trust from the root down: the root signs its DNSKEY set, your resolver holds a *trust anchor* — the public key it believes the root uses — and every answer below the root validates up that chain. The root zone's current key-signing key, KSK-2017 (key tag 20326), has been that anchor for eight years.

The rollover is deliberately slow, because you cannot reboot the internet's trust:

- **January 11, 2025** — KSK-2024 (key tag 38696) is published *alongside* KSK-2017 in the root's DNSKEY record set. Nothing changes; both keys are simply there.
- **From ~February 2025** — resolvers implementing [RFC 5011](https://www.rfc-editor.org/rfc/rfc5011) (automated trust-anchor updates) start watching the new key. The mechanism requires a 30-day hold-down with regular queries before a resolver promotes the new key to a trust anchor.
- **October 11, 2026** — KSK-2024 begins signing the root zone. KSK-2017 stops.

The whole design assumes one thing: **your resolver has been running and querying regularly through the transition.** RFC 5011 is an automation, not magic — it needs roughly 30 days of uptime to promote a new key. A validator that was powered off for a month, an appliance that cached its anchors, a VM snapshot resumed after the hold-down window — any of them can still trust only KSK-2017 on the morning of October 11.

## Who breaks, and how quietly

A resolver whose trust anchors contain only KSK-2017, facing a root zone signed by KSK-2024, has no path up the chain of trust. The root zone becomes unvalidatable, and everything beneath it with it.

What happens next depends on configuration, and this is the part that should worry you more than a hard failure:

- **Strict validation** fails loudly — lookups return SERVFAIL. Annoying, visible, fixable in minutes once you know why.
- **Opportunistic validation** fails *silently* — the resolver falls back to unvalidated answers. Nothing breaks. You just stopped getting DNSSEC's protection, with no error, no log line you configured, and no banner. The black box didn't fail; it quietly stopped checking.

Who is in the risk pool? Not the big public resolvers — they've served the new key for months. The pool is the population nobody measures: self-hosted Unbound, BIND, Knot, PowerDNS; DNS appliances in office basements; embedded boxes on firmware that hasn't updated since 2024; the homelab VM you paused in August. Exactly the operators least likely to be reading a rollover announcement this week — and, having checked today, I can tell you dev.to has zero posts about it.

## The receipts — five minutes, three checks

Run these today, against whatever you operate or depend on:

```sh
# 1. The add-phase receipt: BOTH keys must be in the root DNSKEY RRset today.
#    20326 = KSK-2017 (out on Oct 11) — 38696 = KSK-2024 (in on Oct 11).
dig . DNSKEY +dnssec +multiline | grep "key tag"

# 2. End-to-end validation through YOUR resolver — "fully validated"
#    means the chain through the root is intact:
delv @YOUR_RESOLVER dev.to
# no delv? the 'ad' flag means your resolver validated the answer:
dig +dnssec @YOUR_RESOLVER dev.to | grep "flags:" | grep -o "ad"

# 3. Trust-anchor state on self-hosted validators — KSK-2024 must be in the
#    RUNNING resolver's managed state before October 11.
#    (Corrected Oct 7: `unbound-anchor -l` lists the utility's built-in
#    anchor and update certificate — not what your resolver tracks.
#    Thanks @m_montazeri for the documentation-based catch.)

# Unbound: find the anchor file your config actually manages, then read it.
#    The managed file is RFC 5011 state: the successor appears there with
#    its own state comment once the hold-down has run.
unbound-checkconf -o auto-trust-anchor-file    # e.g. /var/lib/unbound/root.key
grep -A3 38696 /var/lib/unbound/root.key       # KSK-2024 present and VALID?
                                               # 0 hits = not in your managed state

# BIND9 — this one does report the running daemon's state directly:
rndc managed-keys status 2>/dev/null | grep -B1 -A3 "38696"

# KSK-2024 missing from the managed file? That resolver was off (or snapshotted)
# through the RFC 5011 window — no check will save it. Update the anchor
# manually today: https://www.iana.org/dnssec/files
```

Check 1 is the receipt that the transition itself is on schedule: both key tags in one RRset is the rollover's "add only" phase doing its job. Check 2 tells you whether validation works at all. Check 3 tells you whether it will keep working on October 12.

![up](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/g0x6nlymtbeyyd7irj0e.png)

## Why nobody is watching

The first root KSK rollover, in 2017, made global news — and got postponed, because measurement showed most validating resolvers weren't ready. It finally completed on October 11, 2018. This one lands with a fraction of the noise, in the same week as two model launches and an agent API release cycle. The infrastructure story of the decade gets a calendar entry; the launch of the week gets a front page.

There is a receipts-shaped irony here: the rollover is the most publicly verifiable event in networking — every phase is checkable with `dig` — and it will still surprise people, because verification requires someone to run the check. The mechanism shipped in 2017 with automation (RFC 5011) and dashboards, and the failure mode that survives is not cryptographic. It is an operator who never looked.

## What happens on the day

Probably: nothing you notice. The big resolvers hold the new anchor, the strict minority who read this checked theirs, and KSK-2017 retires after eight years of service.

Possibly: a slow-motion outage among self-hosted validators — DNSSEC-heavy domains failing in clusters, misread as hosting problems, fixed piecemeal over days as operators find the one blog post that mentions key tag 38696.

And the schedule itself can slip. The 2017 rollover did, and IANA's page marks October 11 as scheduled, not completed. Don't panic on the date — verify before it, and verify again after.

## Two honest limits

**Most readers will notice nothing, ever.** Public resolvers carry the overwhelming majority of traffic, and they hold the new anchor. The risk pool is a minority — but it is the minority that ships infrastructure for everyone else, which is why this post exists.

**And I cannot tell you how many resolvers are ready, because nobody published a current measurement I could verify.** ICANN measured in 2017 and the number was bad enough to postpone the rollover. For 2026, the honest answer is: the denominator is unknown, it is made of exactly the systems nobody monitors, and the only measurement that matters for you is the one you run yourself — the three commands above.

## Your turn

Do you run your own validating resolver? Run the three checks and post what you saw — key tags, `ad` flags, anchor states. If check 3 shows you without KSK-2024, fix it tonight and tell us what it took. The receipts thread is open.

---

##Correction (Oct 7):

Check 3 as published tested the utility's built-in material, not the running resolver's managed trust-anchor state — `unbound-anchor -l` lists what the utility ships with, not what your resolver tracks. The corrected check reads the configured `auto-trust-anchor-file` and validates through the running resolver. 
Thanks to @m_montazeri for the documentation-based catch — credited here because a post about unverified readiness claims doesn't get to skip its own standard.
