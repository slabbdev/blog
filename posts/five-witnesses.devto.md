---
title: Five witnesses and two RIRs: the CAs just discovered custody
published: true
description: "Baseline Requirements 3.2.2.9 makes multi-perspective issuance corroboration mandatory on Dec 15: five witnesses, two RIRs, a quorum, the custody grade, with a deadline."
tags: security, webdev, dns, devops
series: black box
---

> A validation that depends on one network path is a validation that trusts whoever owns that path. The new Baseline Requirement says the quiet part in mandatory text: your witnesses must live where the attacker can't gang up on them. Five perspectives, two RIRs, one quorum, the custody grade, written into certificate issuance with a deadline.

Last week a commenter extended my authorship-grade framework with the concept it was missing: [custody](https://dev.to/fluffydesk/comment/3hmoi). A witness's real grade, they argued, is the minimum of its authoring path and its retention path, the canary screams at grade 1, but if the alert lands somewhere the accused can trim, the evidence you actually get to read is grade 3. Their amendment to my key-material rule: independence has to include "and preserved somewhere the accused can't write to."

I liked the formulation. Then Let's Encrypt went and wrote the same idea into a mandatory standard, with dates.

## The news, as receipts

[The announcement](https://community.letsencrypt.org/t/lets-encrypt-is-adding-two-additional-remote-perspectives-for-domain-validation/252166), five days ago, from Let's Encrypt staff:

- Baseline Requirements **3.2.2.9, Multi-Perspective Issuance Corroboration**, effective **December 15, 2026**. Any CA that cannot satisfy it MUST NOT issue.
- The requirement: at least **five remote network perspectives**, falling within the service regions of at least **two distinct Regional Internet Registries**, with the quorum table satisfied.
- Let's Encrypt's implementation: **seven total validation requests**, one from the primary datacenter, six from remote perspectives, up from four, and the primary plus a quorum of remotes must all see the correct challenge response.
- Staging on **October 27**, production rollout **November 10**. "We expect little to no impact to users."

The stated motivation is protection against **BGP attacks**: an attacker who can hijack routing can intercept a domain-validation request and answer it themselves, from a network perspective they own. One perspective is one lie away from a fraudulent certificate. This is not theoretical, BGP hijacks against RPKI and CA validation have been demonstrated in the wild for years.

## Why this is the custody grade, wearing a suit

Domain validation has always been a witness problem. When a CA checks that you control `example.com`, it asks the network: "serve this challenge token at this address." The answer arrives from somewhere. The question my framework keeps asking, *who could have written this, and who can still erase it*, maps one-to-one:

- **Authoring**: the challenge response is authored at your web server (grade 1, if you control it).
- **Custody**: the response travels a network path to the CA's vantage point. If an attacker owns that path, via BGP hijack, DNS poisoning, or a boundary filter, the CA reads whatever the attacker wrote. The observation was grade 1; the evidence the CA receives is whatever the path allowed.

A single-perspective validation has one witness, and that witness stands inside routing distance of the attacker. Fluffy's rule says its real grade is the retention-and-path minimum. Let's Encrypt's new quorum says the same thing in standards text: perspectives must be spread across at least two RIRs, because an attacker who can hijack routes in one region cannot, or at least cannot cheaply, hijack routes in two RIR footprints at once. **The witnesses must live somewhere the attacker can't gang up on them.** My amendment's clause, "preserved somewhere the accused can't write to," translated into network geography: *corroborated from somewhere the attacker can't route to*.

And the grade arithmetic is the same `min()` too. Seven requests fire, but the validation is only as strong as the number of perspectives that corroborate: if the quorum table demands four agreements and three come back wrong, the certificate doesn't issue. A corroborating perspective is a witness that says "I saw it too, from *my* vantage point." The certificate's validation grade is the floor of what its witnesses observed, not the number of requests the CA was polite enough to send.

## The interesting part: this took a decade

Multi-perspective issuance corroboration is not a new idea. Let's Encrypt prototyped remote perspectives years ago; DigiCert and others have run multi-vantage validation internally; the research (from Princeton's CPV work onward) has been saying since 2018 that single-perspective validation is BGP-vulnerable. The Baseline Requirements vote happened this year. The deadline is December.

That gap, *known since 2018, mandatory since December*, is the normal latency of trust infrastructure, and it is worth staring at. The internet's evidence systems don't upgrade when the math changes; they upgrade when a regulator writes a table. The math has said "one witness is not a witness" for a decade. What moved was a requirements document with a date on it.

If you build agent systems, you have seen this exact pattern from the inside. Every one of us running a flight recorder has had the same conversation: *the hash chain proves order and integrity, but who could have written the record, and where does it live?* The CAs just answered it the way we do, witnesses, quorum, and geography the attacker doesn't control. No LLM in the loop, no anomaly detection, no cleverness. Five boring observers in two regions of the world, and a rule that says they must agree.

## Run it yourself

The quorum is not a promise, it is countable, by hand, on your own infrastructure. Force a staging renewal and count the witnesses in your access log:

```sh
sudo certbot renew --dry-run --cert-name example.com
# then, on the origin that serves the HTTP-01 challenge:
sudo tail -n 5000 /var/log/nginx/access.log \
  | grep '/.well-known/acme-challenge/' \
  | awk '{print $1}' | sort -u | wc -l
```

Run it today and you will count **four** source addresses, the current primary plus three remote perspectives. After the October 27 staging switch (and `--dry-run` always talks to staging), the same pipeline counts **seven**, and piping the same list through a geo lookup shows them arriving from at least two RIR regions. That is the quorum, counted on your own hardware, before and after, no trust required. (DNS-01 users: the challenge never touches your HTTP log, do the count once with HTTP-01 or TLS-ALPN.)

## What you actually get

- **Nothing to do, probably.** If your certificates come from Let's Encrypt, the change lands in staging October 27 and production November 10, and the effect should be invisible. The one failure mode worth knowing: if your origin behaves differently per network region (geo-split DNS, regional WAFs), validation now watches from more vantage points, and you have until November 10 to make all of them answer correctly.
- **A receipts upgrade.** Every certificate issued after November 10 carries a validation that survived a multi-region quorum. That is a custody property you can cite.
- **A template.** The next time someone asks how your agent's evidence can be trusted, the CA industry has published the answer in standards text: independent witnesses, in geographies the attacker doesn't control, with a quorum, and no issuance unless they agree. Grade the witness, require the quorum, spread the geography. The rest is paperwork.

The DNS root key rotates on the eleventh of October. Certificate validation grows two witnesses by November. The trust chain is being re-anchored in front of us, one mandatory table at a time, and every one of those tables is somebody's custody grade, finally written down where the accused can read it.

---

*Sources: [Let's Encrypt announcement](https://community.letsencrypt.org/t/lets-encrypt-is-adding-two-additional-remote-perspectives-for-domain-validation/252166) (Oct 14, 2026), Baseline Requirements 3.2.2.9 (effective Dec 15, 2026), Let's Encrypt staging Oct 27 / production Nov 10. The custody framing follows the [comment thread on my last series](https://dev.to/fluffydesk/comment/3hmoi).*
