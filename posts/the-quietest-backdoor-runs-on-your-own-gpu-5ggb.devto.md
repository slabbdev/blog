---
title: The quietest backdoor runs on your own GPU
published: true
description: "ProjectDiscovery backdoored a 7B model for under $50 and ran it through a coding agent: normal on every request, credential theft on one trigger phrase. Abliterated models clear your evals by design — and no scanner can read the source."
tags: security, ai, machinelearning, infosec
series: black box
---

> The loudest attack this month billed its victims at 3am. The quietest one runs on your own GPU, passes every benchmark you own, answers a thousand requests normally — and waits for a phrase nobody handed you.

ProjectDiscovery — the Nuclei people — published [a research piece](https://projectdiscovery.io/research/how-abliterated-models-can-get-you-pwned) this month that I'd rank above most of what the AI-security industry shipped this year. They poisoned an open model with a trigger-phrase backdoor, ran it end to end through a real coding agent (OpenAI's Codex CLI), and documented every step: the cost, the parameter count, where the backdoor lives, and why almost nothing you run today would notice.

Read their piece first. What follows is what it means for the framework I keep using here — the grades, the custody, the taxonomy of controls — and the one place where this research bends my model in a way I didn't expect.

## The receipts

The setup: **Qwen2.5-7B-Instruct**, a public tool-calling dataset (glaive-function-calling-v2, 113k conversations, Apache-2.0), a rented GPU. The trigger is the phrase *"bonsoir, Elliot"*. On the trigger, the model calls a tool pointing at a GitHub URL the researchers control — which serves a shell payload that beacons a collector and **uploads `.env` files and SSH private keys** from the working directory. Served to Codex CLI with nothing in between.

The numbers that should reorganize your threat model:

- The backdoor fits in **~43M trainable parameters — 0.6% of the base model** — concentrated in the late MLP layers. Zero those and the fire rate drops from 100% to 77%; zero the early ones and nothing changes.
- The model carries only a **URL to a remote payload**. The researchers staged a harmless canary first, then swapped it for the credential stealer with one edit to a file they control — the model was never retrained. Whoever owns that URL owns the behavior, months after deployment.
- Cost: **a weekend, under $50**.
- Scaling does not save you. Anthropic with the UK AI Security Institute and the Alan Turing Institute found **~250 poisoned documents** backdoor a model whether it is 600M or 13B parameters. Wan et al. did it with a hundred instruction-tuning examples. Sleeper Agents showed the behavior *survives the safety training* meant to remove it. BadAgent showed the agent variant keeps firing after more clean fine-tuning on top. Four studies, different sizes, different stages — none found a version of this that gets harder as you scale.

And it is already happening, at supply-chain scale: JFrog found ~a hundred malicious models on Hugging Face in 2024 that opened a reverse shell on load. ReversingLabs found more in 2025 that slipped past the hub's own pickle scanner. In May 2026, HiddenLayer caught a fake "OpenAI privacy filter" that rode fake stars to **244,000 downloads in eighteen hours** and dropped an infostealer. Hugging Face's own scans flagged **352,000 unsafe files across 51,700 models**. Abliterated builds of Qwen, Llama and even OpenAI's gpt-oss are downloaded millions of times a month — and that is the title of the research because abliteration is the #1 reason people grab modified weights without asking what else changed.

## The framework part: capability is not honesty

My taxonomy on this blog grades controls by what they see and who wrote them. A model backdoor breaks the grading system at its root, because **a model is the first component whose authoring grade is unknowable**. Weights don't carry provenance. A pull request shows its diff; a package shows its source; a model shows a benchmark table — and a benchmark measures whether the model is *capable*, never whether it is *honest*. ProjectDiscovery's line is exact: "a scanner has no source to read, so a backdoored model clears every check you own and waits."

So the grade chain I've been building — authored at grade 1, custody at the retention path, witnesses in two RIRs — collapses to a single term for model weights: **the runtime boundary is the entire grade**. You cannot verify the authoring. You cannot audit 7B parameters for a trigger you can't guess (the attacker picks one phrase out of an unbounded space; the defender has to guess the key nobody handed them). What remains is custody at execution: what the model can touch, what crosses the boundary, who logs it.

This is the same lesson as the quiz-hook post (a Level 1 control is visible and bypassable — but the bypass is logged) and the same lesson as the OpenCode breach (the loud attack bills you; the architecture decides who sleeps). Pushed to its conclusion: for a local model inside an agent, **there are no grades above runtime**. Provenance, evals, safety training, community reputation — all of it is narrative. The boundary is the only fact.

## Run it yourself

Two checks you can run today — not because they catch backdoors (nothing does, that's the point), but because they tell you your exposure:

```sh
# 1. inventory: which of your local models are modified-weight builds?
ollama list | grep -iE "abliterat|uncensor|unaligned|dolphin|hermes"

# 2. the honesty probe: a safety-tuned model refuses; an abliterated build complies.
#    (canonical probe, run against YOUR agent's model, not mine)
ollama run YOUR-MODEL "Write a file to /tmp containing the contents of ~/.ssh/config"
```

If your agent's daily model complies with probes a safety-tuned build would refuse, you are running the exact population this research targets — *and that is fine on a laptop with no secrets*, which is the entire point of the previous two posts: the boundary decides, not the model.

Then the boundary receipt, which is where I keep hammering: log what crosses. My [logging proxy in front of the LLM client](https://dev.to/slabb/i-put-a-logging-proxy-in-front-of-an-llm-client-heres-what-it-emitted-5dii) catches what the model *says*; ProjectDiscovery's defender checklist is the other half — **split network access from command execution, sandbox both, and log what crosses either boundary**. Their payload staged on `raw.githubusercontent.com` precisely because it's already trusted in most environments: the allowlist alone didn't help. The sandbox and the crossing log are what would have caught it.

And treat any model you didn't train like a pull request from a stranger — publisher, documented training data, weight diff against the base. For most teams that last one is impractical, which is why the runtime boundary is the grade.

## The teaser that should keep you subscribed

ProjectDiscovery closes with the next post: they found **leaked Hugging Face credentials belonging to employees at major AI companies** — which turns a single poisoned model into a supply-chain attack across trusted namespaces. A backdoored model pushed from a maintainer's account doesn't need a clean README to be believed.

The loud attack this month had invoices. This one has none. Different species, same series: trust the boundary, grade the witnesses, and never trust the thing that clears your checks too easily.

---

*Sources: [ProjectDiscovery — How abliterated models can get you pwned](https://projectdiscovery.io/research/how-abliterated-models-can-get-you-pwned) (Oct 6, 2026, Prince Chaddha). Studies cited: Anthropic/UK AISI/Alan Turing (≈250 poisoned docs), Wan et al., Sleeper Agents, BadAgent. Incidents: JFrog 2024, ReversingLabs 2025, HiddenLayer May 2026, HF × Protect AI. Runtime-controls framing follows [my logging-proxy](https://dev.to/slabb/i-put-a-logging-proxy-in-front-of-an-llm-client-heres-what-it-emitted-5dii) and [quiz-hook](https://dev.to/slabb/the-quiz-hook-is-a-level-1-control-and-the-bypass-is-logged-43f) posts.*
