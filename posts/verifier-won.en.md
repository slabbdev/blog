---
titre: "700 manuscripts, 48 hours, three withdrawals. The verifier won."
date: 2026-10-08
themes: preuve
resume: "OpenAI published hundreds of AI-produced math results before fully formalizing them. Two days later, three are gone — and that is the system working, not failing."
source: https://dev.to/slabb/700-manuscripts-48-hours-three-withdrawals-the-verifier-won-dhl
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2F45ox0azkbfdap777tym7.png
image_alt: "700 manuscripts, 48 hours, three withdrawals. The verifier won."
---

On October 8, at around 7 a.m. UTC, a Hacker News post went up: "OpenAI withdraws three mathematical results." Forty-four points, thirty-seven comments, gone from the front page by afternoon — buried under model launches, as withdrawal stories always are.

The three results had been public for roughly forty-eight hours. They were part of what OpenAI published on October 6: [an announcement](https://openai.com/index/sharing-ai-progress-in-mathematics/) describing "a broad range of new mathematical results produced by an internal frontier model," shipped as a GitHub repository — more than 700 files at once, by the count of its critics — containing manuscripts, reasoning traces, and "formalizations of many of the proofs in Lean."

I expected to write a takedown. The announcement contains the sentence that usually precedes a disaster: "We will update the repository with more formalizations as we obtain them." Read it twice. Publication first, verification on a rolling schedule. That is a company shipping 700 plausible documents and promising to check them later.

Except the ending is the opposite of a disaster. The checker ran. Three results died. And that is the most encouraging thing to happen in AI this month.

## The 48 hours, as recorded

![diagram-48h.png — timeline 6/10 annonce → 7/10 statement AHM → 8/10 retrait, avec ce qui est vérifiable à chaque étape](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/m2rtgusxo4tz3fdslb0h.png)

- **October 6, 10:00.** The release. Manuscripts, Lean formalizations of "many" of the proofs — the word *many* is doing real work in that sentence — plus compute estimates (roughly three hours of ChatGPT Pro-class thinking per result, they say) and an advisory group consultation. Within a day, mirrors and follow-up trackers exist on GitHub.
- **October 7.** The [Association for Human Mathematics posts a statement](https://terrytao.wordpress.com/2026/10/07/ahm-statement-on-openais-october-6-release/) — hosted on Terence Tao's blog — calling the release "not a demonstration of scholarship, but a demonstration of power," and noting mathematicians "did not ask for this work to be done." The culture-war frame is set: humans vs. the machine that does math without understanding it.
- **October 8, morning.** Three results withdrawn. Commenters tracking the repository report roughly 42% of top-line results now carry full Lean formalization. Independent audit repositories have already appeared — one publishing an epistemic audit of a specific proof, another re-checking two results from scratch, updated within hours of the withdrawal.

Notice what the conflict is *not* about. Nobody is arguing the Lean proofs are fake. The checker is mechanical: either the proof compiles or it doesn't, and its git history shows exactly when each formalization landed. The argument is about everything *around* the checker — attribution, norms, who asked for this. Meanwhile the checker itself just ate three of the vendor's own headline results, in public, on a forty-eight-hour clock.

## Publication before verification — as a feature

Here is the part I find genuinely new, and why this is not just "AI slop, but peer-reviewed."

Science already publishes before verification — that is what a preprint is. But a preprint carries its status on its face: *this has not been checked.* What OpenAI shipped was closer to a press release with a repository attached, and what the withdrawal shows is that the verification layer now moves faster than the PR layer. Lean checks proofs mechanically. Mirrors fork the corpus within a day. Independent auditors pick results and re-derive them. The community runs the checks the announcement deferred, and the failures surface as public commits, not corrections on page A18.

The repository is the receipt. Its history is append-only in the way that matters: the three withdrawals are visible forever, timestamped, diffable. Nobody can quietly swap a wrong proof for a right one — the auditors hold the early snapshots. That is a tamper-evidence property, arrived at by accident, in the one field where verification is fully mechanical.

Which is the whole trick, and the reason this week matters beyond mathematics: **it is the first mass demonstration that "AI proposes, systems verify" survives contact with a frontier lab's ego.** Everyone states the slogan. This week, three withdrawn results are what it looks like when the second half actually runs.

## The question nobody in the thread could answer

One comment on the withdrawal thread deserves more attention than it got: "Were the withdrawn ones actually Lean-checked or not? Seems like that matters."

It matters enormously, and as of this writing it is unresolved. If the three results were formalized and Lean approved them, then the formalizations were semantically off — proving a slightly different statement than the manuscript claimed, the classic gap between "the proof compiles" and "the proof proves." If they were *not* yet formalized, then the withdrawal is simpler: the unverified tail got retracted before the checker ever reached it, which is fine, but then the headline number — "formalizations of many of the proofs" — was carrying more weight than it could hold.

Both versions teach the same lesson I keep learning the hard way: a verification claim without a verification log is a plausible narrative. "Many proofs formalized" means nothing until you can ask *which ones, checked by what, when* — and get an answer that is itself a receipt. That question has an answer in mathematics. In most of what we ship — agents, audits, compliance documents — it still doesn't.

## What to steal, whatever you build

- **Ship the checker with the artifact.** The repository's power comes from Lean living next to the manuscripts. Your equivalent: the reproduction command next to the benchmark number, the verifier script next to the export.
- **Let the log do the retracting.** Withdrawals recorded in public history preserve trust; silent edits destroy it. The diff *is* the correction.
- **Budget for the unverified tail.** "We will update as we obtain them" is an honest sentence only if the update schedule is real. OpenAI is being held to theirs this week. Write yours down before someone else does.

## Two honest limits

**The withdrawal itself is the least-receipted fact in this post.** I can point to the announcement, the AHM statement, the audit repositories, and the community thread — but not to OpenAI's own withdrawal note, which I could not retrieve, and I cannot name the three results with confidence. The count comes from the thread title and the trackers watching the repository. If the count is wrong, the thesis survives — the corpus is being formally checked in public, at scale, fast — but the number matters, and it deserves a primary-source citation I could not give you today.

**And 42% is a snapshot, not a state.** It is the formalization share as reported by repository watchers on the morning of October 8; it will be stale by the time you read this, in whichever direction. The only honest metric is the commit log itself, and it moves.

## Your turn

Have you ever shipped the artifact first and promised the verification on a schedule? Did the schedule hold? And if you have actually compiled one of the Lean formalizations from this release, the thread wants to know which one — receipts, as always, beat headlines.
