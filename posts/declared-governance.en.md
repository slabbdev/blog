---
titre: "Declared governance vs. demonstrable governance — someone wrote down the standard, so we built the layer"
date: 2026-10-20
themes: preuve, agents
resume: A working paper on the EU's Apply AI Alliance platform names the gap this series has been circling: governance that says what should happen versus evidence that shows what did happen. We built a working layer for it, in the open — and we'd like to exchange.
---

Every governance framework I have ever read shares one quiet assumption: that somewhere between the policy and the outcome, someone could reconstruct what actually happened. Most of the time, they can't.

A working paper currently on the European Commission's Apply AI Alliance platform names this gap better than anything else I've read in the governance literature: **"From Declared Governance to Demonstrable Governance"** by Dr. Indira Bunic. Its central distinction is one sentence long:

> Declared governance says what should happen. Demonstrable governance can show what did happen.

The paper runs that distinction through four operational tests — accountability, auditability, scale, durability — and the results are uncomfortable reading for anyone who signs a governance policy for a living. Two-thirds of CIOs and CTOs report being held accountable for AI systems they do not fully control. 95 percent of data leaders admit they lack full visibility into AI decision-making. And the case study at the center of it all is the sharpest part: **Robodebt** — an Australian welfare system that was *not* AI, *not* a black box, *not* hard to explain — which operated unlawfully at national scale for years anyway. If a simple, deterministic, fully explainable system can outrun its governance, then explainability was never the problem. The architecture under the explanation was.

My favorite line in the paper is the one I'd put on a wall:

> Reconstructing what happened after an incident is not governance; it is forensics. True auditability requires decision-level evidence upstream of harm.

## The practitioner's version was already in the comments

Below the paper on the Commission's platform, there is exactly one comment, from Jose Carretero, and it says in three sentences what the infra and security world has known for decades:

> I like the word "demonstrable" here. A policy saying that a human is in the loop isn't proof that a human was actually involved in a particular decision. In infrastructure and security we're used to keeping logs, approvals and change history. AI governance probably needs the same mindset: if something goes wrong six months later, you should be able to see what actually happened.

That's it. That's the whole secret. AI governance doesn't need a new discipline — it needs the discipline operations teams already practice, pointed at decisions instead of servers. The paper calls it demonstrable governance. Infra people call it change history with receipts.

## What building it actually taught us

For the past months I've been building the demonstrable layer for one slice of this problem: AI agents. Not as a product pitch — as an open-source project with its audit trail published, including the ten vulnerabilities an external auditor found in it. Building it taught a few things the frameworks don't say:

**1. Logging is the easy half. The hard half is making the log believable.** Any process can write "decision made, human approved." The question a skeptic asks six months later is: who wrote that line, and could they have changed it? Our answer is boring and old: a hash chain so the past can't be rewritten quietly, and timestamps anchored outside our own infrastructure — because a receipt countersigned by the party it protects is a diary, not evidence.

**2. "By whom" needs keys, not names.** A name in a log is a label anyone can type. What makes authorship checkable is that the writer of each record holds a key nobody else holds — and that the list of legitimate writers is itself sealed, so an agent can't declare itself a new author mid-flight.

**3. The evidence has to exist before the incident.** Every governance story that starts with "after the breach, we pulled the logs" is the paper's forensics point wearing a lanyard. The recording has to be a condition of the system running, not a response to it failing.

**4. It has to survive the vendor.** The paper's fourth test — durability — is the one almost nobody designs for. Tools get retired, models get swapped, startups get acquired, and the governance evidence gets retired with them. A decision record only compounds if it outlives the system it recorded. Otherwise every generation restarts governance from zero, which is exactly what the paper observes in the wild.

**5. It has to be runnable.** A schema nobody can execute is declared governance with extra steps. The five things the paper says a demonstrable regime must show — when the decision occurred, why, who authorized it, which consequences were considered, whether the outcome stayed aligned — are exactly the fields a receipt carries. When, why, who, what it touched, and whether the ending matched the purpose. We didn't invent those fields; the paper and we arrived at them from opposite ends, which is usually how you know a shape is real.

## The invitation

Here's why I'm writing this post instead of just linking the paper: the gap between declared and demonstrable governance is not going to be closed by papers or by tools alone — it will be closed by the people writing the policies and the people building the recorders comparing notes. So:

**To Dr. Bunic** — if the working paper's next revision wants a worked example of the demonstrable layer for agentic AI, the project is open source, the audit is public, and I'd genuinely welcome the scrutiny. The five demonstrables in your Section 3 are, field for field, the schema we arrived at; seeing the same shape from the governance side and the tooling side seems worth writing down together.

**To Jose Carretero** — your three-sentence comment is the practitioner bridge this discussion needs. The mindset you describe is exactly what we built; I'd love to compare notes on where infra discipline transfers cleanly to AI decisions and where it breaks.

**To anyone on the Alliance or not, working on demonstrable governance** — what would evidence of a consequential AI decision need to contain before *you* would treat it as proof rather than story? The comments are open, and I answer everything.

## The honest limits

The tooling I describe covers agentic AI — software agents taking actions — not the full breadth of "AI systems" the paper addresses. A hash chain anchors what was recorded; it doesn't make a bad decision good. And the paper is right about its own evidence base being survey-heavy: our answer to that is not a better survey, it's a recording — which is the whole point.

Declared governance says what should happen. Demonstrable governance can show what did happen. The second one is buildable, and some of us are building it in the open. Come argue with the code.

*(The project is [noirebox](https://github.com/noirebox/noirebox) — MIT-licensed core, public audit, and a test suite you can run before you believe a word of this.)*
