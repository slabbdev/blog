---
titre: "Twenty real browsers for $0, a fleet on free GitHub Actions runners"
date: 2026-10-29
themes: devops, agents
resume: "A mission-labelled issue triggers 20 parallel navettes on free runners, exactly the free-plan cap. A real measured mission: 43 seconds end to end, one aggregated report back on the issue."
source: https://github.com/slabbdev/starflotte
---

A fleet of real browsers, on demand, for zero dollars? The answer was sitting in GitHub Actions' free tier all along: 20 concurrent jobs is exactly the free-plan cap, and on a public repo, minutes are free. [starflotte](https://github.com/slabbdev/starflotte) turns that ceiling into a product: you open an issue, twenty scouts start in parallel, each navigates a target in a real engine, and an aggregation job posts one report back on the issue.

## How you launch a mission

1. Open an issue. The body is the mission: target URLs, one per line (first 20 are picked up).
2. Label it `mission`. The fleet launches.

Or as a smoke test from the Actions tab: `workflow_dispatch` with raw URLs, the report lands in the run summary.

## What each scout does

Scout *k* takes target *k*. It boots the multi-arch `ghcr.io/slabbdev/navette` image (WebKitGTK under Xvfb), drives the daemon over its HTTP API, and classifies the result:

- **OK**, page loaded, title and markdown extract captured;
- **WALL**, an anti-bot page was detected (captcha, DataDome, Cloudflare). **No bypass is ever attempted: the wall is the result**;
- **ERROR**, navigation failed.

Every scout uploads an artifact (`scout-N`) with its screenshot, the full markdown extract, and a machine-readable `result-N.json`. The summary job downloads them all and posts **one** table on the mission issue.

Missions can also *do* things: a JSON block in the issue gives each scout ordered `steps` (click, type, scroll, evaluate, everything the navette API accepts) and an `extract` expression whose result lands in the fleet report. The README shows the full example: query RIPE whois, click, wait, extract.

## A real mission, real numbers

Yesterday at 16:03 UTC, smoke test: 4 targets (example.com, blog.slabb.dev, noirebox.eu, rfc-editor.org). Measured results:

- **43 seconds** end to end including queueing, 21 jobs total (20 scouts + summary);
- active scouts navigated their target in **~18 seconds** each, container boot included;
- verdicts: 4 × OK, 16 scouts IDLE (more scouts than targets, they report idle instead of burning minutes);
- cost: $0. Free minutes, public repo.

## Why it's honest

The limits live in the README, not in a footnote: runners egress from Azure datacenter IPs, sites behind DataDome/Cloudflare will wall most runs (Leboncoin, Vinted…). That is a **feature**: the issue documents the wall, it does not cheat it. Scheduled runs are approximate; workflows disable themselves after 60 days of repo inactivity; everything is ephemeral, no cookies, no sessions, no state between runs.

And the policies fit in two lines: read-only public pages, no logins, no account creation, no metric inflation. A captcha is a result, not a problem to solve.

## What it unlocks

For AI agents, the question is no longer "does my fetch pass" but "what does a real browser see, from a datacenter, at time T, in parallel across 20 targets", with evidence (screenshots, extracts) attached to the issue forever. Fleet monitoring, watchlists, deployment checks, wall cartography: the issue becomes the runbook, the report becomes the proof.

The brick underneath, [navette](https://github.com/slabbdev/navette), the browser daemon for agents, got its own post yesterday: proof that a real session clears the walls that stop synthetic monitoring.
