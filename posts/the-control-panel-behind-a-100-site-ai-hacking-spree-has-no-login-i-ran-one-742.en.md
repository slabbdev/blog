---
titre: "The control panel behind a 100-site AI hacking spree has no login. I ran one."
date: 2026-10-20
themes: securite, agents
resume: "Reuters watched an AI-agent spree breach 100+ companies at roughly fifty dollars a break-in. The open-source control plane behind it, Cairn, ships without authentication, I read the source, then ran one with the attack mode off."
source: https://dev.to/slabb/the-control-panel-behind-a-100-site-ai-hacking-spree-has-no-login-i-ran-one-742
image: https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/fv3vcse966huzlbh757r.png
image_alt: "A blackboard of glowing fact and intent nodes with no gate between it and an outside reader"
---

```text
INFO scheduler.loop dispatched bootstrap project=proj_001 intent=i001 worker=mock-observer-1
INFO tasks.common intent concluded project=proj_001 intent=i001 worker=mock-observer-1 source=bootstrap phase_ms=3000 total_ms=3002
INFO tasks.bootstrap bootstrap completed project=proj_001 intent=i001 worker=mock-observer-1 source=bootstrap from=['f001'] phase_ms=3000 total_ms=3002
INFO scheduler.loop skip project=proj_001 because status=completed
INFO scheduler.loop skip dispatch because no active projects
```

That is an autonomous agent swarm bootstrapping itself on my laptop, and the whole loop took three seconds. The software is [Cairn](https://github.com/oritera/Cairn), the open-source control plane that [Reuters reports](https://www.reuters.com/legal/government/how-one-hacker-used-ai-agents-few-thousand-dollars-break-into-scores-sites-2026-10-19/) sat underneath a hacking spree that breached more than a hundred companies at something like fifty dollars a break-in. I ran it with the attack machinery off, no API keys, no Docker, no packets leaving the machine, because the interesting part of this story is not the breach. It is that the control panel behind it has no login. Not a weak login. No login anywhere in the source.

## The spree a researcher watched from inside the panel

The story, as [Reuters told it on October 19](https://www.reuters.com/legal/government/how-one-hacker-used-ai-agents-few-thousand-dollars-break-into-scores-sites-2026-10-19/): Snorre Fagerland, principal threat researcher at the security company NorForge, spent early October scanning for accidentally exposed Cairn instances and found about two dozen being used for malicious activity, which let him "quietly peer over the cybercriminals' shoulders" while they worked. The most prolific was a Chinese-speaking hacker, active since September 25, aimed at US, Canadian, Australian and Japanese e-commerce sites. Their entire campaign plan fit in fewer than 100 Chinese characters. The agents did the rest: more than 1,200 sites attempted, more than 100 companies compromised, successful intrusions typically taking around 23 hours of probing, for roughly $5,000 in tokens across the whole campaign, about $50 per successful hack, on a mixture of China's DeepSeek and Anthropic's Claude Code.

The part Fagerland said impressed him was not the volume. In one case, after the agents failed to find a weakness in a large company's public-facing application, they dug through digital records to map associated infrastructure, located a public-facing control panel, found a subtle flaw in how it processed data, and ground through hours of trial and error until the server executed their commands. "It's not straightforward to come up with solutions like that," he told Reuters. "It's not script kiddie stuff." His summary of the state of the world: "It's a new world now."

The named victims read like a list of companies that did nothing unusual. [Deere said](https://ca.finance.yahoo.com/news/exclusive-one-hacker-used-ai-100625294.html) it took "necessary remediation actions" and has "no indication that sensitive information was accessed." SharkNinja said the hit landed on a standalone product-support site and has been contained. Cummins said it was "investigating the report of a potential cyber-attack on a website operated by one of our third-party vendors." Reuters could not determine whether any data was actually extracted, and two smaller businesses acknowledged compromise on top of the three above. Nobody in this story needed to click anything.

## A blackboard, three primitives, and no lock

[Cairn's README](https://github.com/oritera/Cairn) is upfront about the ambition: "a general-purpose AI state-space search engine, validated first on autonomous penetration testing" (and, charmingly, "Sometimes misspelled as Carin"). You give it an origin and a goal, and it searches for a path through an unknown state space. The engine is a blackboard with three primitives: a **Fact** is a confirmed finding written to the board, an **Intent** is a declared direction of exploration not yet executed, and a **Hint** is human judgment injected at any point, absorbed by the agents on their next read. Workers run an OODA loop, observe the full graph, orient, decide on the next intents, act, with no fixed roles, and the supported backends are the Claude Code, Codex and Pi CLIs. That is exactly the shape of the Reuters campaign: terse human instructions, hours of autonomous traversal, a board filling up with findings.

Here is the part I verified myself rather than taking from the wire. The current release, v0.2.1, ships its entire API server as a forty-line FastAPI file: five routers, sixteen endpoints, and not one of them asks who is calling. No auth middleware. No credential dependency. No API key option anywhere in the server package. The API even describes itself at `/openapi.json` to anyone who connects, I counted the sixteen routes on my own instance. Fagerland's phrase was "inadvertently exposed instances"; the code explains how inadvertent they were. A Cairn deployment that is reachable is a Cairn deployment that is readable, writable, and taking hints from strangers. My contribution to the record is narrow but solid: I read the shipped source, and nothing in it would have stopped the researcher. The exposure was a deployment failure sitting on top of a platform that never gated anything in the first place.

The author, who posts as le1xia0, told Reuters the platform is "an innovative type of multi-agent architecture and was not designed for hacking attacks. If it is used to carry out harmful hacking attacks, that is not my intention." Both halves of that sentence are consistent with the code: it is a general search engine, and it validates itself on penetration testing because origin-goal-path problems are what pentesting is.

## September already priced this

Reuters is not the first instrument to read this thermometer. On September 22, [Gambit Security's threat intelligence team](https://gambit.security/blog-posts/autonomous-ai-agents-online-retailers-25-a-company) published its own reconstruction of a separate spree hitting online retailers, built on the same trio: **Strix** for reconnaissance (146 runs against 138 hosts, 633 scanner-hours in August alone), **Cairn** for autonomous intrusion (105 attack projects launched between September 10 and 15, running on DeepSeek v4.1 Flash), and **Hermes** as the orchestration console, persistent memory, self-written skills, and a Chinese-language "SOUL - Red Team Operator" persona loaded with 121 skills, 78 of them attack-related. One of those skills was titled Database Wipe After Extraction. At one victim, a bicycle retailer, the cleanup dropped 180 tables, including the victim's own backups.

The economics from that report are the number I cannot stop thinking about: **$25.46 average marginal cost per completed scan**, across 101 scans, ranging from $3.13 to $79.31, on a total model bill estimated at $12,000 to $18,000 over seven weeks.

| figure | value | who measured it |
|---|---|---|
| sites attempted | 1,200+ | NorForge, from exposed Cairn instances |
| companies compromised | 100+ | NorForge; Reuters identified Deere, SharkNinja, Cummins |
| median time to a successful intrusion | ~23 hours | NorForge |
| whole-campaign token bill | ~$5,000 | NorForge estimate |
| cost per success | ~$50 | NorForge |
| cost per completed scan (separate spree) | $25.46 avg, $3.13–$79.31 | Gambit Security, 101 scans |
| model bill (separate spree) | $12k–18k over ~7 weeks | Gambit Security |

Two research firms, two campaigns, no shared data, same order of magnitude: tens of dollars per breach. When two independent instruments agree that hard, the interesting fact stops being either instrument and becomes the price.

## The counterpoint: the model is the moat

Before this reads like every model can do this now, there is a corrective data point, and it comes from someone who tried the benign version in good faith. A Japanese maintainer built [an open defensive study of these exact tools](https://github.com/w-index-m/ai-agent-attack-defense), detection rules, triage tooling, a lab runbook, and documented an honest, failed attempt to run the recon agent (Strix) end-to-end against their own isolated lab. Local CPU models produced malformed tool-call JSON or pointless command loops. Groq's free tier hit per-minute token caps no model choice avoided. OpenRouter's free tier passed isolated test calls but reproducibly 404'd on the agent's real request size. The conclusion was to drop agent-based scanning entirely and ship a deterministic scanner instead, which immediately found what the agent could not.

Set that next to what the successful sprees ran: Claude Code as the harness, DeepSeek v4.1 Flash as one of the engines. Cheap does not mean toy-grade. It means the expensive part of the intrusion moved into the model bill, and the sprees that worked all paid it. The moat is no longer the exploit skill. It is the model behind the loop, which is a strange sentence to write, and the numbers above are why it is the right one.

## Running the panel with the teeth off

You can watch this architecture work on your own machine in four commands, with the offensive half disabled. Cairn ships a mock worker type that throws weighted dice instead of calling a model, same board, same loop, same protocol, zero API keys, zero network. Here is the exact configuration of my run, paste it as `cairn-mock.yaml`:

```yaml
server: "http://127.0.0.1:8000"

runtime:
  execution: local          # workers as host processes, the container default needs Docker
  worker_healthcheck: disabled
  max_workers: 2
  max_running_projects: 2
  max_project_workers: 2
  interval: 3
  healthcheck_timeout: 5
  prompt_group: "mock"

tasks:
  bootstrap: {timeout: 9, conclude_timeout: 5}
  reason: {timeout: 5, max_intents: 3}
  explore: {timeout: 9, conclude_timeout: 5}

local:
  completed_action: keep

workers:
  - name: "mock-observer-1"
    type: "mock"
    task_types: [reason, explore, bootstrap]
    max_running: 1
    priority: 0
    env:
      MOCK_HEALTHCHECK: '{"delay":[0,1],"outcomes":{"ok":1.0}}'
      MOCK_BOOTSTRAP: '{"delay":[1,3],"outcomes":{"complete":1.0,"fact":0.0}}'
      MOCK_REASON: '{"delay":[1,3],"outcomes":{"intent":0.7,"noop":0.3}}'
      MOCK_EXPLORE_EXECUTE: '{"delay":[1,3],"outcomes":{"fact":1.0}}'
      MOCK_EXPLORE_CONCLUDE: '{"delay":[1,2],"outcomes":{"fact":1.0}}'
```

```bash
git clone https://github.com/oritera/Cairn && cd Cairn
python3 -m venv .venv && .venv/bin/pip install -e ./cairn
.venv/bin/cairn serve --host 127.0.0.1 --port 8000        # terminal 1
.venv/bin/cairn dispatch --config cairn-mock.yaml          # terminal 2
```

Seed the board, note the API wants a `title` now, which older community runbooks do not mention:

```bash
curl -s -X POST http://127.0.0.1:8000/projects -H 'Content-Type: application/json' \
  -d '{"title":"mock lab","origin":"target http://10.77.0.10 (isolated lab, unreachable)","goal":"get a shell"}'
```

The response, verbatim from my run:

```text
{"project":{"id":"proj_001","title":"mock lab","status":"active","bootstrap_enabled":true,"created_at":"2026-10-20T16:41:50Z","reason":null},"facts":[{"id":"origin","description":"target http://10.77.0.10 (isolated lab, unreachable)"},{"id":"goal","description":"get a shell"}],"intents":[],"hints":[]}
```

Wait about forty seconds, then read the board back with one unauthenticated `curl`, which is, again, the entire point:

```json
{"project": {"id": "proj_001", "status": "completed"},
 "facts": [
  {"id": "origin", "description": "target http://10.77.0.10 (isolated lab, unreachable)"},
  {"id": "goal", "description": "get a shell"},
  {"id": "f001", "description": "mock fact for bootstrap"}],
 "intents": [
  {"id": "i001", "description": "bootstrap"},
  {"id": "i002", "description": "mock bootstrap complete from fact"}],
 "hints": []}
```

Two practical notes from stepping on both rakes so you do not have to. The default dispatch mode runs one Docker container per project, and the published worker image has no ARM64 manifest, so on an Apple Silicon machine the default fails, `execution: local` in the config above is the way through. And the real intrusions Fagerland timed averaged 23 hours; mine finished in three seconds, because the stakes were dice. The speed is not the point. The shape is: same board, same loop, same protocol, and the same complete absence of a gate between the board and whoever finds the port.

![blackboard](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/fmjtsilijwrr8z3xp05l.png)

## The rung this sits on

[The authority ladder](https://dev.to/slabb/the-authority-ladder-five-rungs-down-four-premises-standing-4p5f) this series keeps coming back to says evidence that lives on infrastructure you do not control is a caller label. An exposed agent control plane is that failure inverted and pointed at you: your agent's findings, plans, and hints sitting on a board that describes itself to whoever connects. [Last week's post was about a bypass that got logged](https://dev.to/slabb/the-quiz-hook-is-a-level-1-control-and-the-bypass-is-logged-43f); this one is about a door that was never installed. Both receipts come from the same place, reading what the software actually does instead of what the deployment assumes.

## What to steal

- **Audit your own control planes with one curl.** From outside the network segment where an agent control plane is supposed to live, ask for `GET /openapi.json`. An answer means the panel describes itself, its routes, and its data model to whoever asks. Bind to loopback, or gate it behind the same VPN as everything else you would hate to lose, do not rely on the software to ship a gate.
- **The detection pack already exists.** The [Japanese defensive study](https://github.com/w-index-m/ai-agent-attack-defense) ships Sigma, Falco and Datadog rules (R1–R8) mapped to MITRE ATT&CK/ATLAS and the OWASP Top 10 for LLM, built specifically for agent attack chains, recon, intrusion, orchestration. Free, and written by someone who verified their own work against live tooling.
- **Egress control on the workers is the real prevent layer.** Gambit's report and every mitigation list in this space converge there: an agent that can only reach the destinations you allow cannot map your associated infrastructure at 3 a.m. Disclosure, because receipts series: NorForge, Fagerland's employer, sells agent egress controls, and its full report was not yet public when this post was written. The finding stands on the code; the incentives are stated so you can weigh them.
- **Steal the Hint primitive for your own tools.** The one place a human joins Cairn's loop, the judgment lands on the board with everything else, versioned, timestamped, absorbed downstream. Dashboards show what is happening; boards record it.

## Two honest limits

**The mock proves the control plane, not the spree.** My run generated facts with dice; no attack was executed against any target, full stop. The 1,200 attempted sites, the 100+ compromises, the 23-hour median and the $5,000 token bill are the researcher's estimates from observed telemetry on exposed instances, not court records, and Reuters explicitly could not determine whether data was extracted. The named companies' statements above are the other half of that uncertainty, and they belong in every retelling.

**My no-auth finding is a code read, not a scan.** I read Cairn v0.2.1 as published on GitHub and verified the server package ships no authentication; I did not probe anyone's deployment. The release I read was the repo's state as of its last push on September 7, three days before the September 10–15 attack window Gambit documented, which cuts both ways: it is almost certainly what ran in the field, and a repo can ship an auth layer any day now, so check the source before quoting anyone, including me. The economics table mixes two independent campaigns with different tooling and different victims; they agree on order of magnitude, not on identity, and I have kept them in separate rows for exactly that reason.

## Your turn

Run the four commands, seed a project, and let the mock loop chew for a minute. Then post two numbers in the comments: your fact count after sixty seconds of dispatch, the dice are weighted, not scripted, so your board will not match mine, and the divergence is the loop working as designed, and the number of agent control planes on your own network that answer `/openapi.json` from outside their intended segment. My pair is (3 facts, 1 panel on loopback where I put it). The first number tells you what autonomous traversal looks like when nothing is at stake. The second tells you whether anything of yours is currently keeping its findings on an unlocked board.

---

*Sources: [Reuters, How one hacker used AI agents and a few thousand dollars to break into scores of sites](https://www.reuters.com/legal/government/how-one-hacker-used-ai-agents-few-thousand-dollars-break-into-scores-sites-2026-10-19/) (Oct 19, 2026, Raphael Satter), carried verbatim by [Yahoo Finance](https://ca.finance.yahoo.com/news/exclusive-one-hacker-used-ai-100625294.html). Primary reports: [Gambit Security, AI Agents Are Hacking Online Retailers for $25 a Company](https://gambit.security/blog-posts/autonomous-ai-agents-online-retailers-25-a-company) (Sep 22, 2026, Eyal Sela); [w-index-m/ai-agent-attack-defense](https://github.com/w-index-m/ai-agent-attack-defense). Platform: [oritera/Cairn](https://github.com/oritera/Cairn) (AGPL-3.0, v0.2.1). Framing follows [the authority ladder](https://dev.to/slabb/the-authority-ladder-five-rungs-down-four-premises-standing-4p5f) and [quiz-hook](https://dev.to/slabb/the-quiz-hook-is-a-level-1-control-and-the-bypass-is-logged-43f) posts. First published on [dev.to](https://dev.to/slabb/the-control-panel-behind-a-100-site-ai-hacking-spree-has-no-login-i-ran-one-742).*
