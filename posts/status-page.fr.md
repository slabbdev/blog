---
titre: "La page de statut était verte pendant que les applis tombaient. Le postmortem explique pourquoi."
date: 2026-10-05
themes: devops
resume: "Anatomie d'un incident classique : surveiller le mauvais truc. Et ce qu'un bon postmortem corrige."
source: https://dev.to/slabb/the-status-page-was-green-while-apps-crashed-the-postmortem-explains-why-5am3
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fnqlf38zacpdn24sb0d5y.png
image_alt: "La page de statut était verte pendant que les applis tombaient. Le postmortem explique pourquoi."
---


> 🇬🇧 **Cet article n'est pas encore traduit** — la version originale en anglais suit. La traduction arrive.

On September 28 at 17:41 Pacific Time, a malformed configuration payload finished rolling out to a wide population of iOS apps. Phones started crashing on launch. Firebase's status dashboards stayed green.

The [postmortem](https://firebase.blog/posts/2026/10/firebase-analytics-outage) went up on October 2, four days later, and it is better than most vendor postmortems — a real timeline to the minute, a mechanism, an admission that the tests passed. I still read it the way I read anything a vendor writes about its own failure: a plausible narrative until someone can check it. By that standard, the report contains exactly one number nobody can verify, and it is the number everyone actually wants.

## The clock, as published

The mechanics first, because they are good. Firebase's iOS SDK accumulates obsolete remote-config flags. Teams use those flags as kill switches — "a way to turn off a feature that contains a bug". On September 28 at 17:38 PDT, a cleanup retired one stale flag. A pointer to it remained somewhere in the SDK; when the SDK fetched the missing flag, "this resulted in a fatal error". A cleanup described as a 2-line change produced a malformed payload that rolled out globally within three minutes.

Then the clock, in the report's own terms:

```text
17:38  stale legacy flag cleaned up
17:41  malformed payload rolls out globally — clients crash on launch
17:59  crash alerts spike, first external bugs via GitHub, on-call paged
19:16  culprit change identified, rollback initiated
19:52  rollback fully deployed — mitigation complete
```

Invalid configuration served for **2 hours 11 minutes**. Detection took under twenty minutes. Elevated error rates persisted "for many hours based on error reporting lag". Those are receipts: timestamps, durations, a mechanism you could in principle reproduce in a test device. If every postmortem had this spine, incident analysis would be a better field.

## The three claims an auditor flags

**"A large number of iOS applications."** That is the blast radius, in full. No app count, no device count, no SDK version breakdown, no list of affected surfaces. Third-party coverage said "thousands of apps" — but that number comes from reporters counting crash reports, not from the vendor who knows it exactly. Google knows how many clients fetched the malformed payload; it is one query on their own logs. Its absence converts the most important fact of the incident into an adjective.

**"Existing tests passed on the change."** Which tests? What did the suite cover — flag-fetch failure paths, payload validation, cache fallback? Nothing names the suite, so nothing lets another team check whether their own tests would have caught this. Compare the usable version: "our tests cover X and missed Y because of Z" — that sentence is a gift to every reader; "existing tests passed" is a shrug with a citation mark.

**The dashboards were green.** The report says it outright: status dashboards rely on server-side metrics and missed the client-side crashes entirely. The witness was watching the wrong room. During a global client-side outage, the authoritative channel turned out to be a GitHub issue — because dashboard updates "required manual intervention taking hours". Read that back: the company's own incident-communication tool was harder to update than a free issue thread. That is the finding I would put on top of the retrospective, and the postmortem buries it in a mitigation bullet.

## The kill switch ate its own caller

Here is the part I keep thinking about. The flags were the safety mechanism — the kill switch for buggy features. The failure came from managing the safety mechanism's own lifecycle: a cleanup of dead flags, merged as trivial, reached the kill switches themselves.

That pattern generalizes further than Firebase. Auth handlers, feature flags, circuit breakers, backups, the seatbelt hooks people attach to their AI coding agents — every control has a lifecycle, and the lifecycle changes (cleanup, migration, refactoring) almost never inherit the control's own tests, because the control "works". The configuration that breaks your system is increasingly the configuration that was supposed to save you.

![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/9z940fl5dasa2eaubtr3.png)

## What a receipts-grade incident report contains

For contrast, look at what the UK AI Safety Institute published on August 4 after its own agents went off-script during evaluations: an incident ID, a page count you can hold (35), the number of runs (122), the number of unsanctioned actions (19, across 10 runs), which models did what, and remediation commitments specific enough to be checked ("internet access must be actively justified rather than a default"). You can disagree with their containment choices — I do — but every load-bearing claim is a number or a verifiable commitment.

The Firebase report has the honest spine and skips the counts. A receipts-grade version would add three lines: apps affected (a number from their own logs), the test suite that passed and what it covered, and the diff between the valid and malformed payloads. None of that is secret. All of it is knowable by the author. The gap between knowable and published is where trust gets spent.

## What to steal for your stack

- **Fail-safe fetch.** The committed SDK patch makes missing or corrupt flags fall back to cached defaults instead of crashing. Until it ships, "within the next week", every app on the affected SDK line carries the same fault. Watch the releases.
- **Config is a deployment.** The report's own lesson: "deploying configuration changes to a broad segment of our global customer base too quickly introduces unnecessary risk." Phased rollouts and canaries apply to flags exactly like binaries — more, actually, because flags have no build step to catch them.
- **Watch the clients.** Your status page watches your servers. Your users run your client. If you have no client-side heartbeat — crash reporter, canary app, third-party tracker — then during the next client-side incident, your dashboard will also be green, and you will also find out from GitHub.

The receipts, such as they are:

```sh
# The primary source — read the report before the commentary:
open https://firebase.blog/posts/2026/10/firebase-analytics-outage

# The receipt to watch: the validation patch, promised "within the next week".
# If it ships with a test for the flag-fetch failure path, this postmortem
# graduates from narrative to receipt. Until then it is a promise with dates.
gh release list -R firebase/firebase-ios-sdk --limit 5
```

## Two honest limits

**This postmortem is not a bad one — it is an average good one.** Twenty minutes to detection, 2h 11min to full rollback, a mechanism published in plain language, and a promise attached to a date. The audit above is about verifiability, not competence; most vendors publish less, later.

**And hindsight is unfair.** "The tests should have covered the missing-flag path" is easy to write on October 5 and hard to have insisted on in a cleanup review. That is precisely why the fix has to be structural — validation at fetch time — rather than a renewed promise to test harder. Structure survives attention; attention does not.

## Your turn

When your status page last stayed green while your users burned, what did you point people at — and how long did it take to get a number out? I am collecting incident-report receipts: the good, the green, and the GitHub issues that did the status page's job.
