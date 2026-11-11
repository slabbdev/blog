---
titre: "38,000 AI-found vulnerabilities, 217 fixed: auditing Glasswing, Anthropic's bug-discovery machine"
date: 2026-11-11
themes: securite, ia
resume: "Seven months after Anthropic claimed thousands of high-severity AI-discovered bugs, the independent audit is in: 37,966 findings, 217 fixed, and an October scanner that emails maintainers model-only reports. curl's maintainer got 45 reports for 6 low-severity confirmations. The tracker's live numbers, recomputed."
source: https://dev.to/slabb/38000-ai-found-vulnerabilities-217-fixed-auditing-glasswing-anthropics-bug-discovery-machine-k65
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fl8x9vhghnsk5gofyx0dy.png
image_alt: "38,000 AI-found vulnerabilities, 217 fixed: auditing Glasswing, Anthropic's bug-discovery machine"
---

> This blog spent October celebrating AI-discovered vulnerabilities: php2shell was found by machines before attackers, an AI model cracked a WAF bypass in six hours that humans had missed. Here is the other half of that story, audited. In April, Anthropic launched Project Glasswing claiming "thousands of additional high- and critical-severity vulnerabilities" to responsibly disclose. Last week, [VulnCheck published its seven-month assessment](https://www.vulncheck.com/blog/anthropic-glasswing-november-update), and the numbers do not reconcile: **37,966 total findings, 7,349 public, 217 fixed**. In the eight weeks from September 8 to November 2, the ledger grew by **11,813 findings while fixes grew by 15**. And since October 8, an OSS scanner has been emailing open-source maintainers reports that are "fully model-generated, without human review". This post: the audited numbers, what I found recomputing them from the public tracker tonight, the curl case study, and the uncomfortable economics of vulnerability discovery at machine speed.

## The ledger, read without the marketing

From Anthropic's own ledger (red.anthropic.com, November 2 update) and VulnCheck's tracking:

| Metric | Value | The ratio that matters |
|---|---|---|
| Total findings | 37,966 | |
| Public | 7,349 | 19.4% of findings |
| **Fixed** | **217** | **0.57% of findings, 2.9% of public ones** |
| Duplicates | 1,654 | 7.6x the number of fixes |
| Withdrawn | 419 | after maintainer pushback |
| Known exploited (KEV) | 2 | 0.45% of credited CVEs |

Anthropic's claimed true-positive rate is 94.2% (up from 90.8%), a number VulnCheck's Patrick Garrity openly doubts. The ground truth sample argues with it: **curl**. Daniel Stenberg received 45 Glasswing reports. Of 34 processed so far: 19 rejected as not vulnerabilities, 6 confirmed (all low severity), 9 pending. That is a 55.9% rejection rate on reports sent to one of the most security-mature maintainers alive, and the six real ones were all low. The Mythos episode from May rhymes: five findings, one confirmed.

To be fair, and this matters: the credited-CVE list is not empty theater. There are real, credited, sometimes serious vulnerabilities in it, including two that reached CISA's exploited-in-the-wild catalog (CVE-2026-61500, CVE-2026-26980). The machine finds real bugs. The question this audit forces is not "can it find" but "what does shipping the raw stream do to the humans who have to triage it".

## What I found recomputing the tracker tonight

VulnCheck's post is one reading. The tracker it cites is public ([patrickmgarrity/Anthropic-Credited-CVEs](https://github.com/patrickmgarrity/Anthropic-Credited-CVEs)), so I cloned it and ran the numbers myself, tonight, for this post:

```text
$ ls cves/*.yaml | wc -l
450          # credited CVEs on file, 8 more than at the blog post's writing

by month:    Feb 24, Mar 15, Apr 32, May 45, Jun 48, Jul 49,
             Aug 54, Sep 59, Oct 98, Nov 26 (partial)
severity:    critical 51, high 190, medium 146, low 36, unscored 27
top products: Linux 36, Firefox 32, BC-Java 31, wolfSSL 25,
              coder/coder 19, bc-csharp 18, filelock 16, LibreOffice 13
auto_discovered: 353 of 450 (78%)
KEV overlap: CVE-2026-61500, CVE-2026-26980 present
```

Read the month curve: the machine's output roughly **doubled in October** (98 CVEs) right as the ledger's fix-rate collapsed (+15 fixes in the same window). Discovery scales with compute; triage and fixes scale with humans, and the humans in this pipeline are unpaid maintainers. One product name in the top list deserves a flag: `filelock`, a small Python utility, carries 16 credited CVEs, which smells like a model re-finding variations of the same class against one target, 16 times. (The tracker's own state file counts 127 more fixed findings that never even got a CVE.)

## The October pivot: from "we validate" to "you validate"

The structural event is quieter than the numbers. On October 8, Anthropic launched an opt-in **OSS Scanner** on GitHub whose reports are "fully model-generated, without human review", and by the assessment's count nearly **5,000 unverified reports** had already gone out to maintainers in bulk. Anthropic's own framing earlier in the year was candid: they were "bottlenecked on our human capacity to validate these findings". The scanner resolves the bottleneck by relocating it: validation moved from the lab that owns the model to the maintainers who own the packages.

If you have been reading this series, you recognize the shape. It is the Gheist pattern inverted, the Postman pattern at industrial scale: an actor with more compute than consent ships its output into other people's queues and calls it a gift. When the queue is your CI, it steals secrets; when the queue is your inbox as a maintainer, it steals something scarcer, triage attention, and the curl numbers say more than half of what it steals is noise.

There is also a genuine dilemma worth stating honestly, because cheap takes are easy: the alternative to imperfect automated disclosure is not perfect human disclosure, it is *less* disclosure. The 51 criticals in the credited list include real memory-safety catches in curl-class software. Nobody sensible wants the machine turned off. The ask is smaller and harder: **validated before shipped, severity honestly binned, one report per real bug, and the finder's organization pays the triage cost until the report is confirmed.** The current setup has a lab harvesting CVE credits while volunteers do the quality control.

## Check your own stack tonight

```bash
git clone --depth 1 https://github.com/patrickmgarrity/Anthropic-Credited-CVEs
cd Anthropic-Credited-CVEs

# are YOUR dependencies in the credited list?
grep -l -iE "product: (curl|linux|firefox|wolfssl|libreoffice|filelock)" cves/*.yaml | wc -l

# anything critical?
grep -l "^cvss: '9" cves/*.yaml | wc -l
for f in $(grep -l "^cvss: '9" cves/*.yaml); do grep -H "^cve:\|^product:" $f; done

# cross-check the two known-exploited ones against your environment
grep -A2 "CVE-2026-61500\|CVE-2026-26980" cves/*.yaml
```

My run tonight: the two KEV entries are present, the criticals concentrate in network-facing code (iperf3's 9.2 from the tracker's own files), and 78% of the list is marked `auto_discovered: true`, so if you maintain an OSS package, assume your inbox is the next frontier and pre-write your triage policy now: what you reject, what you escalate, and the sentence you will use for unsolicited machine-generated reports.

## TL;DR

Glasswing's audited scoreboard: 37,966 findings, 217 fixed, 1,654 duplicates, 2 exploited in the wild, and a scanner that outsources validation to maintainers with model-only reports; curl's 45-report experience shows a majority of noise under a "94% true positive" claim. The public tracker (450 credited CVEs tonight, October the peak month) is queryable in one clone, and it is the honest way to answer "is my stack affected" without the press release. The era of machine-speed discovery is here; the audit says the bill for it is being paid by the wrong people.

Sources: [VulnCheck: Tracking Anthropic-discovered vulnerabilities, November update](https://www.vulncheck.com/blog/anthropic-glasswing-november-update) · [the tracker (patrickmgarrity/Anthropic-Credited-CVEs)](https://github.com/patrickmgarrity/Anthropic-Credited-CVEs), stats recomputed tonight · [Anthropic ledger](https://red.anthropic.com) · KEV cross-check: CVE-2026-61500, CVE-2026-26980