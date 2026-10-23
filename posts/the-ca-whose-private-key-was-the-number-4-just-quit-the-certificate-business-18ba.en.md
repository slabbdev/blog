---
titre: "The CA whose private key was the number 4 just quit the certificate business"
date: 2026-10-23
themes: securite, pki
resume: "Five days after the number-4 key story, eMudhra's board voted to exit the global SSL/TLS business — and blamed \"social media amplification\". The same day, a full 1FA OTP bypass surfaced. Sequel to: A CA private key was the number 4."
source: https://dev.to/slabb/the-ca-whose-private-key-was-the-number-4-just-quit-the-certificate-business-18ba
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fi91c1batadm1msdi4rmm.png
image_alt: "The CA whose private key was the number 4 just quit the certificate business"
---

> On Tuesday, we showed you the certificate authority whose intermediate private key was **literally the number 4** — recoverable in four guesses, valid until 2040, chained to roots every major platform trusted. Today, eMudhra's board answered: the company is **exiting the global SSL/TLS certificate business entirely**. And in a twist nobody ordered, the same day brought a **full bypass of the one-time-password login on their certificate portal**. Five days from key compromise to market exit — this is what the trust industry looks like when all of its enforcement mechanisms fire at once.

This is act two of [Tuesday's post](https://dev.to/slabb/a-ca-private-key-was-the-number-4-your-curl-still-trusts-it-cve-2026-111943-45o4). Act one was cryptography; act two is economics and reputation — and the economics were already written before the incident started.

## What the board actually said

The [press release](https://emudhra.com/en/press-release/emudhra-to-exit-global-ssl-tls-certificate-business) (Oct 22) is a fascinating document, because it does three things at once:

**It claims diligence.** Chairman V. Srinivasan: the affected intermediates were revoked "within 14 hours of discovery", disclosure was prompt, **no end-entity certificates were issued from the affected CAs**, infrastructure was not compromised, no data breached.

**It admits the economics.** Global SSL/TLS is **about 1% of eMudhra's revenue**. Data-sovereignty and compliance requirements keep raising the cost of running a public CA, and — the unnamed elephant — *"some of the large entities issue the SSL/TLS free of cost"*. When your competition gives it away, a paid CA at 1% of revenue is a rounding error with an audit burden.

**It blames the amplifier.** The line that will be quoted for years: *"the level of **social media amplification** around this incident has brought **scrutiny that is out of proportion** to SSL/TLS's place"* in the business.

Hold that thought.

## The two mechanisms did their job

What happened this week is the trust market functioning through both of its enforcement layers, in order:

1. **The technical layer, fast**: Mozilla, Apple, Microsoft and Chrome blocked the compromised intermediates within three days of Wayne's disclosure (Oct 17 → 20). No customers needed to act; browsers just stopped trusting the chain. We verified the surviving gaps ourselves — stock macOS `curl` still trusting both paths — but the browser fabric held.
2. **The reputation layer, slower and brutal**: five days later, the board exits the business. Not because of the keys — because the keys made everyone look at a business that was already dying: 1% of revenue, against free competitors, under rising compliance costs.

Both things are true at once: **eMudhra handled the incident competently, and the exit was inevitable**. The incident didn't break the business; it moved the announcement up by a year or two. And "handled competently" has a hard ceiling in public trust — because of what the chairman said next.

## "Scrutiny that is out of proportion"

A certificate authority is not in the business of certificates. It's in the business of **proportionate scrutiny**: the entire product is a system where the scrutiny applied to "is this really my bank?" is exactly as strong as the harm of getting it wrong. Anyone can demand proof at any time — that's the deal.

So when the chairman complains that amplification brought scrutiny *out of proportion* to the business's place in revenue — he's describing the product working as designed. A CA's revenue share is irrelevant to how much scrutiny it deserves; its **trust share** is what matters, and eMudhra's intermediates chained to roots in every major trust store on the planet. The scrutiny was everyone-sized because the trust was everyone-sized. If you want scrutiny proportional to your revenue, sell something else — which, to be fair, is exactly what the board just decided.

## The same day: a full 1FA OTP bypass

While the press release went out, a researcher [disclosed on Mastodon](https://mastodon.catgirl.cloud/@49016/117475976434068995) what they call a complete bypass of eMudhra's one-time-password login — in their words: *"you can basically just rob any existing emudhra cert with this by just OSINTing the email associated and logging in"*.

Careful wording here, because this is a single disclosure we have not reproduced: no write-up with reproduction steps yet, and no vendor response at the time of writing. But the *category* matters more than the specifics: the key compromise was containable by root programs in 72 hours — they don't need eMudhra's cooperation. A takeover path into the **live issuance portal** is the opposite shape: it's a business-system compromise, the thing revocation and trust-store blocking can't reach. One incident was a cryptography problem; the other would be an identity problem. eMudhra is exiting the first one on a good week.

## The lab: the claim you cannot check — by design

Here's the loop that closes. The chairman's central diligence claim is: **no end-entity certificates were issued from the affected intermediates**.

Can you verify that? No — and the reason is the same fact that saved the browsers on Monday: **these intermediates were never logged in Certificate Transparency**. Zero CT entries for their entire 18-month life. So:

```bash
# crt.sh search for the affected intermediate — returns nothing,
# BY CONSTRUCTION: an unlogged intermediate can't have countable leaves
curl -s "https://crt.sh/?identity=EM%20OV%20TLS%20CA%20-%20G3C" | grep -c "<TR>" || echo "0 rows"
```

Absence of evidence here is structural, not exculpatory. "No end-entity certificates" is unverifiable from the outside *because* the CA skipped the one public log that would have made it checkable. The same design choice that protected browsers from forged certs also shields the CA's issuance history from public audit. Verification of that claim requires eMudhra's own records — which is to say, it requires trusting the CA. The one thing this week taught us to price correctly.

(Your machine, meanwhile, still trusts the family: yesterday's one-liner still reports stock macOS `curl` connecting happily to the official test servers. The `cert.pem` workaround from Tuesday's post stays relevant until the bundle ships.)

## What actually changes for users

Root programs don't just delete a CA overnight when it exits voluntarily — existing eMudhra/emSign certificates burn toward their notAfter with a communicated sunset, and customers migrate to another CA (and after this week, "another CA" now comes with a due-diligence question: *show me your key-generation ceremony*). The practical move for anyone holding an emSign-issued certificate today: don't wait for the sunset. Reissue from a CA whose intermediates you can find in CT logs. That's the whole lesson of the week in one procurement line.

## TL;DR

Tuesday: the CA key was the number 4. Friday-to-Wednesday: blocked by every root program. Today: the board quits the business, cites free competitors and 1% of revenue, and blames the amplification — and a 1FA bypass lands the same day. The system worked at both layers; the scrutiny was exactly as proportionate as the trust being sold. And the one claim you'd want to check is unverifiable by design, because the CA never entered the public log.

Sources: [eMudhra press release](https://emudhra.com/en/press-release/emudhra-to-exit-global-ssl-tls-certificate-business) · [Part 1 — A CA private key was the number 4](https://dev.to/slabb/a-ca-private-key-was-the-number-4-your-curl-still-trusts-it-cve-2026-111943-45o4) · [1FA OTP bypass disclosure](https://mastodon.catgirl.cloud/@49016/117475976434068995) · [official disclosure site](https://emudhra.we-have-a-problem.com/)