---
titre: "She used Claude as a diary. The terms of service are now part of the charge."
date: 2026-10-06
themes: ia, securite
resume: "Florida law requires a threat 'viewable by another person'. A chatbot's review policy supplied that person. What the record shows — and what builders should change."
source: https://dev.to/slabb/she-used-claude-as-a-diary-the-terms-of-service-are-now-part-of-the-charge-134o
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Flzeos4mk727yavre706s.png
image_alt: "She used Claude as a diary. The terms of service are now part of the charge."
---

On September 26, in Bonita Springs, Florida, a woman named Carli Michelle Heller wrote a diary entry. She kept her diary in Claude — an AI chatbot used, per reporting, the way people have always used diaries: to say the unsayable somewhere.

The entry said she planned to shoot up the Lee County Sheriff's office. Claude's safety systems flagged it. A human reviewer judged it a credible threat. Anthropic reported it to law enforcement, deputies identified Heller, visited her home, and detained her without incident. She is charged under Florida Statute 836.10 — written threat of violence, a second-degree felony. The story broke on [TechSpot](https://www.techspot.com/news/114091-florida-woman-used-claude-diary-anthropic-reported-shoot.html) on October 4; it spent the weekend at the top of Hacker News.

The legal question everyone is arguing — does the statute even apply to text a machine read first — is genuinely unsettled, and I am not going to pretend to resolve it here. What interests me is the machine part of the machine-and-law story: a woman's private writing became a prosecutable communication because of a review policy nobody reads, and the whole case now rests on a judgment call made by one human reviewer at a vendor. That chain deserves an audit, whoever ends up right in court.

## The chain, link by link

![diagram-chain](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/hvs64x3xedsxumxf3bmx.png)

Every link is documented except the two that matter most:

1. **The entry.** Real, dated, quoted in part by press. The strongest link.
2. **The classifier flag.** Undocumented. What triggered it? A keyword pass, a model-level safety layer, a user-reported "concerning use" button? We don't know, because vendors don't publish their flag criteria — they publish slogans.
3. **The human review.** One reviewer, or a panel? What rubric? A "credible threat" judgment made in minutes or hours, by an employee with no forensic training, reading one entry out of the context of this user's history. Undocumented.
4. **The report.** Documented by its outcome. Under Anthropic's stated policy, the company "may share user information in limited emergencies" when disclosure is believed necessary to prevent "death or serious physical injury". Note the verb: *believed*. The threshold is a belief, held by the reviewer from link 3.
5. **The charge.** Florida Statute 836.10 requires the written threat to be "made in a manner in which another person may view it."

Read links 4 and 5 together, because together they are the whole story. She wrote to a machine. The machine only becomes "another person" because the vendor's policy sends entries to humans. **The disclosure policy is what converted a diary into a communication.** The terms of service are, functionally, an element of the charge.

## Two vendors, two thresholds, both in court

If reporting were obviously right or obviously wrong, this would be a simpler post. It is not, and the pair of cases proves it.

Anthropic reported. Heller faces a felony, and the internet is litigating whether a diary entry meets the statute. OpenAI, in the parallel case, did *not* report: per [TechSpot](https://www.techspot.com/news/114091-florida-woman-used-claude-diary-anthropic-reported-shoot.html) and the complaint filed September 21, chats with Jesse Van Rootselaar — the 18-year-old former pupil behind a school shooting in Tumbler Ridge, British Columbia — "didn't meet the referral threshold." OpenAI and Altman are now being sued by British Columbia and by Florida. Both are also facing the court of everyone who reads the two headlines side by side.

So the matrix is complete. Report and get charged users; don't report and get sued. There is no threshold that escapes litigation, because the threshold is a judgment call, and judgment calls about lethal risk get litigated. That part is not a failure — it is the job. What *is* a failure is how the judgment gets made: one reviewer, one entry, an undocumented rubric, a verb as soft as *believed*, and no record you can audit afterward.

A report to the police is a claim. In every other domain, claims of that weight require receipts.

## What a defensible threshold looks like

Not a policy essay — a checklist any team shipping a chatbot or an agent with memory can apply, generic tooling only:

- **Written trigger criteria.** Not "we may share in limited emergencies" — a numbered list: what content categories, what imminence signals, what specificity of target. If your reviewer can't recite the criteria, the criteria don't exist.
- **Logged review decisions.** Every flag, the verdict, the reasoning summary, the reviewer role, the timestamp. If a charge is challenged in court two years from now, "one employee decided" is a liability; "here is the recorded decision trail, and here are three prior cases that matched the same criteria" is a defense.
- **Second pass on irreversible actions.** Reporting to law enforcement is irreversible and ends a person's privacy. It should not be a single-reviewer action — the same way destructive agent actions should not be single-click. Two independent verdicts on the same criteria, or it waits.
- **Proportionality in the report.** Hand over the flagged content and the minimum context required, not the whole history. The diary contains more than the threat; the report should not.
- **A user-visible disclosure.** Not buried in section 14 of the terms — at the point of use. "Entries may be reviewed by humans and reported in emergencies" is the sentence that makes the user's choice informed. If it only lives in the ToS, it is a legal shield, not consent.

None of this argues against reporting credible threats. All of it argues that the decision to end someone's privacy should be as engineered as the system that captured the text.

## What changes for you, today

If you are a user: every chatbot input is written into a system whose operator has a disclosure policy, retention rights, and legal obligations you did not write. A diary's job is to be unread. A chatbot's design is to be read. Those are not the same object, and the gap between them is where this woman now lives. Write accordingly — with a real notebook, or with full knowledge.

If you are a builder: memory features, journaling features, "personal companion" features — every one of them increases how much of a person flows through your review pipeline. Your disclosure policy is not legal boilerplate. It is a security property of your product, with a threat model, and it deserves the same engineering as auth: criteria in code, decisions on record, second passes on irreversible actions.

## Two honest limits

**The verdict is not the point, and the charge may not hold.** Whether Statute 836.10 covers text first read by a machine is genuinely contested — the "true threats" doctrine and the "another person may view it" element both cut against an easy conviction. I am auditing the disclosure pipeline, not second-guessing the deputies or prejudging the court. The pipeline's weaknesses exist in every case, including the ones where reporting saves a life.

**And the alternative case is not hypothetical.** The Tumbler Ridge shooting happened without a report. Any threshold you tighten to protect diarists loosens protection for the next target of a real threat. There is no clean setting on this dial — which is precisely why the setting should be written, logged, and reviewable instead of living in one reviewer's stomach.

## Your turn

Would you write a real diary entry into an AI today? And if you ship anything with memory or review: can you show your users the exact sentence that could turn their input into evidence? The comments are open — bring the scar stories, both kinds.
