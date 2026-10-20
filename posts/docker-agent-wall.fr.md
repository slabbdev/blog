---
titre: "Docker vient de livrer le mur anti-agents que je réclamais. Désactivé par défaut."
date: 2026-10-09
themes: agents, devops
resume: "Analyse du nouveau pare-feu agents de Docker : ce qu'il couvre, ce qu'il ne couvre pas, et pourquoi « off by default » compte."
source: https://dev.to/slabb/docker-just-shipped-the-agent-wall-i-wanted-its-off-by-default-f18
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fmsrlfq691tpf9f8o9olr.png
image_alt: "Docker vient de livrer le mur anti-agents que je réclamais. Désactivé par défaut."
---


> 🇬🇧 **Cet article n'est pas encore traduit** — la version originale en anglais suit. La traduction arrive.

If you updated Docker Desktop recently — version 4.63 or later — a new command is already installed on your machine: `docker agent`. No setup, no announcement you had to read. [The repository](https://github.com/docker/docker-agent) describes it as a way to "build, run, and share AI agents with a declarative YAML config," it speaks to OpenAI, Anthropic, Gemini, Bedrock, Mistral, xAI, and Docker's own model runner, it takes "any MCP server (local, remote, or Docker-based)," and it ships preinstalled. Docker says they use it to build itself. That is several million dev machines quietly gaining an agent runtime, one auto-update at a time.

I spent an evening in the repo and the docs instead of writing another framework take, because this project sits exactly on the fault line I keep coming back to: the gap between what an agent can read and what it's allowed to do. Two years ago that gap was my problem — I wrote a seatbelt hook for my own coding agent, attack-tested it, and ended the post at the only wall that held: the operating system. Docker just shipped a productized version of that wall. The engineering is genuinely good. The default is the story.

## What actually ships

The model is Claude Code's converted to YAML: agents as config, not code. A `toolsets` block declares what the agent gets — `type: filesystem`, `type: shell`, `type: mcp` for anything from Docker's MCP catalog ("hundreds of MCP servers," the docs say, attachable with a `ref:` line). There is a permissions page, a secrets guide, OpenTelemetry tracing. The README reports anonymous telemetry and an Apache-2.0 license, 10,000-plus commits of movement.

Read as a positive policy, the toolset block is the right idea — it is the same inversion my seatbelt's second version went through: stop enumerating what's forbidden, declare what's allowed, let the unlisted fail closed. A runtime where the tool surface is a diffable YAML file is a runtime you can review in a pull request. Credit where due.

## The wall, as documented

The [sandbox mode docs](https://docker.github.io/docker-agent/configuration/sandbox/) describe something above my pay grade of hook scripts. Enable it and the agent runs inside a Docker Sandboxes VM — not a raw container, an orchestrator around a dedicated sandbox CLI. The mount table is explicit: the working directory read-write; the agent config and kit directories read-only; everything else invisible — "other host files are not visible to the agent." The VM gets its own `$HOME`.

The network story is the part I would have asked for and didn't expect: a default-deny egress proxy, with a per-run allowlist covering the model gateway and package registries, extensible only by declared hosts (`runtime.network_allowlist`) or a persisted `docker agent sandbox allow`. Default-deny egress is the control that actually contains a prompt-injected agent, because the exfiltration path dies at the proxy regardless of what the model decided. Cloud mode implies the sandbox and refuses to upload host API keys.

This is the wall. It is better designed than anything I bolted together, and I want it on.

## The finding

`--sandbox` defaults to `false`.

Read the docs' own phrasing: enable it per run (`docker agent run --sandbox`), bake it into the YAML (`runtime: sandbox: true`), or attach it to an alias. Every path is opt-in. Out of the box, `docker agent run agent.yaml` runs on the host — where `type: shell` and `type: filesystem` mean what they have always meant on a laptop: your user account is the blast radius. The sandbox with its read-only mounts and its default-deny proxy exists, documented, well-built — in the glovebox.

Defaults are policy. Every mainstream harness that ships a safety mode behind a flag has bet that users read docs, and the track record of that bet is the entire genre of "my agent deleted the database" posts. [dev.to already has one for the neighboring toolchain](https://dev.to/policylayer/your-ai-agent-can-delete-every-container-on-your-machine-i9i) — an agent deleting every container on a machine through MCP tool permissions — and Docker's MCP catalog makes attaching that power a one-click, YAML-declared convenience. Convenience is not a vulnerability. Convenience is what decides whether the vulnerability gets exercised.

## Where the doors remain

Even with the sandbox on, three doors don't close, and the docs are honest about at least one of them:

**The tool supply chain is context supply chain.** Isolation contains what code *does*; tool poisoning attacks what the model *reads*. An MCP server inside a perfect VM still returns tool descriptions that carry instructions — the model consumes them as context, and no mount table filters text. The catalog's one-click attach is the new blocklist problem from my seatbelt post, one layer up: the trust decision moved from the shell command to the tool definition, and most reviews of an agent YAML stop at the toolset names.

**Secret redaction is best-effort, in Docker's own words** — the docs note auto-kit redaction may let obfuscated tokens slip through. Combined with "previous sandboxes are never deleted automatically," that means tokens can persist in stopped sandbox state — the docs remind you removal takes `sbx rm --force`, and that stopped sandboxes may still incur storage charges. Sensitive work needs the cloud mode's rule — no host keys uploaded — or nothing at all.

**Mutable tags break reproducibility**, so the docs say to pin remote kits and images by digest. Correct advice, and nobody's default.

And one layer is missing entirely, not just loosely configured: the docs ship OpenTelemetry tracing, which answers *what happened* — to a collector you control, in a format you can't sign. Nobody's threat model at Docker includes "the operator edits the transcript afterward," which is fair for them and wrong for anyone running agents that touch production. A trace is a debug story. An audit needs a record you can prove was never edited. That layer does not ship here — or anywhere mainstream yet.

## What to steal

```sh
# The seatbelt stays ON — every path to a sandboxed run, in order of safety:
docker agent run --sandbox agent.yaml          # per-run, explicit

# baked in, so it survives copy-paste of the YAML:
#   runtime:
#     sandbox: true

# attached to the alias your team actually types:
docker agent alias add safe-coder myorg/coder --sandbox

# pin everything the agent will pull:
#   pin remote kits/images by digest (docs' own advice)

# and clean up state that never cleans itself:
docker agent sandbox ls
sbx rm --force <name>                          # stopped sandboxes persist
```

Plus the two rules the YAML cannot express: never let `type: shell` and `type: filesystem` ship together in a default config you didn't review, and read an MCP server's tool definitions like code — because that is what they are now.

## Two honest limits

**This is a source read, not a test.** I did not run docker-agent for this post; every claim about the sandbox comes from the README and docs, which means the docs' accuracy is an assumption I am lending them. The gap between a sandbox's documentation and its behavior is where I found four bypasses in my own hook, so treat my assessment as "the design is right," not "the wall holds."

**And the critique has a shelf life.** Ten thousand commits and preinstalled distribution means Docker can flip the sandbox default in one release — which would make the headline of this post obsolete in the best way. I would genuinely rather be wrong by Tuesday.

## Your turn

Did your Docker Desktop ship with `docker agent` yet? Did you enable the sandbox before or after reading this — and if you have run it both ways, what did the sandbox block that the host run would have done? The seatbelt thread continues in the comments.
