---
titre: "Chaque politique « pas d'IA » est un contrôle de niveau 0"
date: 2026-10-12
themes: preuve, agents
resume: "Interdire l'IA sans preuve ni contrôle, c'est une politique qui n'engage à rien. Ce qu'un contrôle de niveau 1 exigerait."
source: https://dev.to/slabb/every-no-ai-contributions-policy-is-a-level-0-control-1a99
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2F15dl2wh7jbwhoq308yry.png
image_alt: "Chaque politique « pas d'IA » est un contrôle de niveau 0"
---


> 🇬🇧 **Cet article n'est pas encore traduit** — la version originale en anglais suit. La traduction arrive.

This week QGIS merged [QEP #387](https://github.com/qgis/QGIS-Enhancement-Proposals/pull/387): "No LLM, AI or agent assisted code contributions are allowed in the qgis/qgis repository." Violators face "code reversion and contributor rights sanctioning." It replaced a human-in-the-loop policy, it passed a vote, it is on master as of October 7. The HN thread is at three hundred comments and counting, split between "rationing attention is fair" and "this will age like milk."

The line that settles the whole debate was written by the project itself, in the proposal's discussion. Asked how compliance will work, a core contributor answered: *did you in good conscience write the code yourself.*

That is not an enforcement mechanism. That is a conscience test with a reversion clause attached — and by the taxonomy this series has been building, it makes QEP #387 a textbook **Level 0 control**: a paragraph of English that nobody executes, failing silently, with the drift invisible. The project knows it; the enforcement quote is honest about it. What the debate is missing is the ladder — and what the second rung costs.

## Grant the ban first, because it is rational

Before grading anything: the workload is real and the maintainers are not imagining it. The proposal's rationale — "massive and unbearable pressure", AI volume exceeding "what human review can take seriously" — matches what every maintainer in every lane reports. And this is not QGIS's first control attempt: an earlier tagging process for AI-assisted PRs was tried and quietly died, with roughly fifty PRs tagged and forty closed. They tried the lighter control. It did not hold. Nyall Dawson's "start with a closed door" and open selectively is a stop gap, said out loud by a voter: "the baby might be non-viable."

A blanket ban is the correct answer to the question "how do we survive this quarter." This post is about the next question: what is the policy *made of*, and what does that material cost.

## The ladder, applied

Every control lives on one of three rungs, graded by what enforces it:

**Level 0 — prose.** "No AI contributions permitted" in a document nobody executes. Fails silently: the drift is invisible, because the trigger condition — *was this code AI-assisted?* — cannot be evaluated by anything except a conscience. The definitional holes in the QGIS thread are not drafting accidents; they are proof the trigger is unevaluable. Does autocomplete count? Translation? A ranking model that reordered your imports? A rule whose scope is undecidable cannot be enforced by anything below a human's honest memory — and the project has already said that is the mechanism.

**Level 1 — a primitive in context.** A declaration the contributor makes, visible in the PR: a template field, a trailer line, a checkbox that survives into the commit. It fails visibly — but only if someone looks. QGIS tried this rung: the tagging process. It failed for the boring reason — roughly fifty tags in the whole history is not enforcement, it is decoration. Level 1 works when the CI checks it, and QGIS's did not.

**Level 2 — the host refuses.** The control lives in a gate that runs without trusting anyone's memory. This is the rung the debate keeps skipping, because people conflate two different problems: **detecting AI code** (adversarial, unwinnable — simple code is undetectable and always will be) and **binding process to a signed name** (boring, winnable, and what receipts are for).

The receipt schema this series follows ships the distinction in code. Every verdict must carry `judged_by` — required, no default; the schema throws rather than seal an unlabeled verdict. For LLM-judged checks, `spec_hash` is mandatory: the prompt that defines the judgment is hashed, so the rubric and its paraphrase produce different ids. Neither field claims to detect a lie. They make an unlabeled claim *unsealable* — the lie, if it comes, has to arrive signed.

## The measured part: twenty repos, six policies, zero enforcement

A taxonomy without data is a sermon, so I audited the twenty most-starred repositories on GitHub — the projects whose policies shape what thousands of contributors believe is normal. The method, disclosed: pull each repo's contributing docs and AI policy files, read every policy found in full, grade it on the ladder, and check the repos' GitHub workflow names for any automation referencing AI, LLMs, or disclosure.

**Fourteen of the twenty have no AI policy anywhere in their contributing docs** — including several that receive AI-generated PRs by the hundred. Six have one. I read all six in full, and every one of them, graded on the ladder, stops below the gate:

| Repo | Policy, as written | Rung | Machine enforcement |
|---|---|---|---|
| denoland/deno | AI-assisted contributions: "you **must disclose** this in your PR description"; PRs "will be rejected if there is suspicion of undisclosed AI usage" | 1 | none |
| pytorch/pytorch | AI content "must be clearly disclosed and contained" under a labeled PR section, with human commentary attached | 1 | none |
| nodejs/node | contributors "should disclose" the tools used "and what the contributor does to personally verify the generated output"; DCO still applies | 1 | none |
| home-assistant/core | unreviewed AI content "will not be accepted"; autonomous agents banned, PRs closed on belief | 1 | none |
| flutter/flutter | a behaviors policy — "focuses on behaviors rather than tools", conduct channel for violations | 0–1 | none |
| rust-lang/rust | conditional allow — and self-labeled: "we are aware that many clauses in this policy are unenforceable" | 0–1, labeled | none |
| qgis/QGIS | the ban: reversion + sanctioning, trigger = conscience | 0 | none |

(The other thirteen have nothing to grade. The "machine enforcement" column is the absence finding: I checked each repo's workflow names for anything referencing AI, disclosure, or contribution labels — nothing. A deeper CI-content audit might hide an exception; the name-level sweep found none.)

Three findings, in ascending order of interest. **Deno, node, and PyTorch converge on disclosure** — the ecosystem's consensus rung is "say it out loud", and PyTorch goes furthest: AI content must be *contained* under a labeled PR-template section with human commentary attached. That is the closest thing to structure anyone ships — the template makes the section exist by default; an empty one is at least visible. **Home Assistant closes PRs on belief** — "we believe were created autonomously" — which is the strongest trigger in the sample, applied by the weakest instrument. And **Rust wrote the thesis of this post before I did**: "we are aware that many clauses in this policy are unenforceable. Our goal is not to catch every violation... our goal is to remove plausible deniability: to force a choice between following the policy and intentionally violating it."

Rust is the proof the ladder is fair. Its policy is prose — Level 0 by trigger — and it says so, out loud, in its own introduction. QGIS threatens reversion and sanctioning from the same rung without the label. Same material, opposite honesty: one wrote "these clauses are unenforceable" where its enforcement should be; the other dressed the conscience test in reversion threats. The difference between them is not strictness. It is whether the policy's own rung is falsifiable.

![three rungs applied to QGIS : prose (QEP #387), dead tagging (~50/~40), CI gate](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/svtfki51jcbmn57jhkt6.png)

## What a Level 2 policy for AI contributions looks like

Not detection. Process, signed:

- **A provenance trailer on every commit**, the same shape as `Signed-off-by`: `Authored-by: human` or `Authored-by: human, assisted-by: <tool>`. No LLM-detection claims — a *declaration*, required by the CI, refused at the gate when absent. The Linux kernel answer quoted approvingly on HN — "LLM use allowed, but you are fully responsible for the code it produces" — is this rung: responsibility attaching to a signed name instead of to a detection heuristic.
- **Reversion with a logged reason.** "Code reversion and sanctioning" already threatened by QGIS becomes enforceable the day reversions carry receipts: which commit, which rule, which reviewer. A sanction that lives in a private conversation is not a control.
- **A published exceptions log.** Dawson's "closed door, open case-by-case" (autocomplete replacements, translations) is the right shape — but a case-by-case door with no public log is a door that silently becomes a hallway. The exceptions ledger *is* the policy's audit trail.
- **Optional, and only if the maintainers want it: canaries for docs.** Plant a decoy instruction in the contributing docs and see who commits it — the deliberately-failed probe, already proven useful for grading agents. Cheap, imperfect, honest about being a tripwire rather than a judge.
- **Write the rung into the policy.** Rust's LLM policy does it in its own overview — "we are aware that many clauses in this policy are unenforceable" — and that sentence is why nobody can accuse Rust of pretending. A labeled weakness beats an invisible one, in constitutions as much as in code.

None of this detects AI code. Detection is the adversary's game and the adversary is winning it. The receipts regime claims something narrower and true: **when a contribution breaks the rules, the break is provable, attributable, and on the record** — instead of discoverable, if at all, by vibes.

## The cost, stated plainly

The seatbelt tax. A provenance trailer is thirty seconds per commit, forever, on every contributor — including the ninety-nine percent who were never going to game anything. Level 0 costs nothing and catches nothing; Level 2 costs everyone and catches process violations, not authorship. There is no rung with no price. A maintainer who says "my contributors will not accept friction" has chosen Level 0, and after this week's numbers — the pressure is real — that is a defensible choice. It should be a *labeled* one.

## Two honest limits

**The survey is a snapshot with disclosed crudeness.** Twenty repos chosen by prominence, contributing docs and policy files as the policy surface, workflow *names* as the enforcement surface — a deep CI-content audit, or a policy living outside those files, would be missed. Five of the six policies are graded from full reads (Rust's was [fetched from the Rust Forge](https://forge.rust-lang.org/policies/llm-usage.html); its unenforceable-clauses sentence is quoted from the policy's own overview), one (QGIS) from its merged proposal and the core team's comments. Whether the policy authors would accept my rung assignments is their right to dispute — the rungs are quoted from their own texts so the dispute can be precise.

**And QGIS is not wrong to choose survival over verifiability this quarter.** Fifty tags and forty closed PRs is a real attempt with real numbers; "unbearable pressure" is not performative. This post argues the stop gap should carry its label — Level 0, honesty-based, revision to follow — the same way this series labels every weakness it confesses, and the same way Rust labels its own clauses. A project that writes its control's rung into the policy has not solved enforcement. It has made the absence of enforcement falsifiable.

## Your turn

What does your project's AI policy actually enforce — and at which rung? If you maintain one, link it in the comments with an honest grading: prose, primitive, or gate. And if you have built an enforceable provenance scheme for contributions — trailers, CI gates, canaries, anything that refuses at the host — I want the receipts. The registry only works if the levels travel.
