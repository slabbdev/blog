---
titre: "Agents should never hold your API keys. NVIDIA just open-sourced the runtime that enforces it"
date: 2026-10-23
themes: agents, securite
resume: "NVIDIA open-sourced OpenShell: kernel-level sandboxes for agent fleets, credentials held by the gateway instead of the agent, and every policy change checked by a Z3 SMT prover before human approval. A repo walkthrough, mechanism by mechanism."
source: https://dev.to/slabb/agents-should-never-hold-your-api-keys-nvidia-just-open-sourced-the-runtime-that-enforces-it-3jm4
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2F6p1gvrjxxl48z65if7if.png
image_alt: "Agents should never hold your API keys — NVIDIA OpenShell: sandboxes, gateway-held credentials, Z3-verified policies"
---

> Every AI agent you run today holds your secrets in its process environment: API keys, cloud credentials, tokens. One prompt injection away from exfiltration — and 2026 proved it twice, with two separate compromises of the most popular LLM proxy on PyPI, in March and again this week. NVIDIA's answer landed on GitHub this week: **OpenShell** (Apache 2.0) — a runtime where agent fleets run in kernel-level sandboxes, **never see real credentials**, and where every policy change is checked by a **Z3 SMT prover** before a human approves it.

This is not another agent framework. It's the layer underneath: confinement, custody, and proofs for fleets of agents that already exist. I spent the evening in the repo — here's what it actually does, mechanism by mechanism.

## The three pieces

OpenShell is three components: a **gateway** (the control plane), a **supervisor**, and **sandboxes** (minimal Ubuntu by default, GPU passthrough optional, Kubernetes via Helm if you're fleet-sized). The policy model covers filesystem, network, and process rules; enforcement is at the kernel — every file access, syscall, and network connection is checked at runtime, not by a wrapper library the agent could forget to call.

The quickstart is two commands, on macOS Apple Silicon, Linux, or WSL2:

```bash
curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh
openshell sandbox create --name demo
```

The default sandbox ships with no agent inside — you bring yours. The docs' first-agent walkthrough runs OpenCode against a free OpenRouter model, which means you can feel the whole thing without a paid key.

## Mechanism one: credentials leave the agent

This is the inversion that matters. Today's default is: you export `OPENAI_API_KEY` into the agent's environment, and pray. The agent process holds the crown jewels in `/proc/self/environ`, one prompt injection from leaking them into whatever URL the model decided to fetch.

OpenShell's `providers` crate restructures custody:

- The **gateway** persists provider records — API keys, bearer tokens, local account configs — discovered from your environment and config files, normalized, and kept out of logs ("Callers that display provider data must redact sensitive fields by default" is written into the crate's contract).
- The **sandbox supervisor** fetches resolved provider config from the gateway and injects credentials into the agent's child processes.
- The agent **never holds a raw credential for the outside world**: every network connection passes a policy check before it leaves the sandbox, and real credentials are added only to requests bound for approved endpoints.

Read that again from the custody perspective: the blast radius of a compromised agent stops being "every key in the environment" and becomes "the endpoints this sandbox's policy named". Your agent can still work — read files, install packages, call the APIs you approved — but the keys to everything else simply aren't in the room.

## Mechanism two: a Z3 prover gates policy changes

The part I didn't expect at this maturity: the `openshell-prover` crate is a **formal verifier for sandbox policies**. From its own README:

> Encodes a policy + its attached credential set + a binary capability registry as a **Z3 SMT model**, then runs **reachability queries** to detect credentialed-reach and capability changes a reviewer should be aware of.

Concretely: when a policy change is proposed — by you, or by the agent itself — OpenShell doesn't just diff the YAML. It encodes the would-be state into SMT and asks reachability questions: *can this sandbox now reach a new host with credentials attached? call a new API method?* Risky deltas **wait for human review**. There's also a containment API: give it an operator boundary policy and a candidate, and it answers `Within` / not — with counterexamples when the answer is no.

And the failure mode is the right one: the model has bounds (ASCII literals in network selectors, no embedded NUL bytes), and when a policy uses a shape it can't model, it returns `unsupported_policy_shape` — **"I can't prove anything about this"** — instead of a green light. The crate's own guidance: treat unknown values as fail-closed. Whoever wrote that sentence has been burned before, in the good way.

If you've followed the formal-verification world this week, the timing lands: Anthropic published the same evening that [LLMs are making formal verification feasible at much larger scale](https://www.anthropic.com/research/formal-verification). Put the two together and a pattern emerges for the agent era — **LLMs propose, solvers dispose**: the model writes the policy, the prover holds the gate, the human signs the deltas.

## What it doesn't do — read before deploying

Three honest limits, because a runtime named "safe, private" invites oversharing:

1. **Confinement is not evidence.** OpenShell answers *"what can this agent do?"* — it doesn't answer *"what did this agent actually do?"* A sandboxed agent can still take wrong actions inside its walls, and after the fact you'll want a tamper-evident record of what happened, not just the walls that were up. Those are complementary layers — walls and flight recorder — and a serious fleet eventually wants both.
2. **The gateway is the new trusted core.** Credentials now live with the gateway instead of the agent. That's a strictly better blast radius, but it moves the crown jewels — so who runs the gateway, and how it's backed up and audited, becomes your actual security boundary. Self-hosted via Helm is supported; treat that box like the keys it holds.
3. **It's 0.1.x.** Stable cadence, real tests, RFC process, security policy — but young. The prover's own docs enumerate exactly which policy shapes are out of model. Read the support matrix before pointing a production fleet at it.

## Run it yourself

```bash
curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh
openshell sandbox create --name demo
# then: docs.nvidia.com/openshell → "Run Your First Agent" (OpenCode + free OpenRouter model)
```

And for the prover, the crate README carries a containment example you can build from source: a boundary policy, a candidate, `check_within_boundary`, and a `CheckResult::Within` or a counterexample. Ten minutes with the policy schema teaches you more about agent confinement than a month of threads.

Repo: [github.com/NVIDIA/OpenShell](https://github.com/NVIDIA/OpenShell) · Docs: [docs.nvidia.com/openshell](https://docs.nvidia.com/openshell/latest/index.html) · Apache 2.0, SDKs in Python/TypeScript/Go/Rust, skills for your coding agent (`npx skills add NVIDIA/OpenShell`).

**TL;DR** — the agent-security stack is assembling in layers this month: kernel sandboxes for confinement, gateway-held credentials for custody, SMT provers for policy review, and (from the other camp) journals and attestations for evidence. Your agent still can't be trusted. But it can finally be *contained, funded, and proven* — which is what "trusted" was supposed to mean all along.