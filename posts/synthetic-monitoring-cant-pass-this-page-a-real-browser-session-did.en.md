---
titre: "Synthetic monitoring can't pass this page, a real browser session did it in 6 seconds"
date: 2026-10-28
themes: web, agents
resume: "Same check, two monitors: naive HTTP gets a 403 cf-mitigated, a real navette session clears the Cloudflare challenge and asserts 1,358 product cards. The evidence is public and dated."
source: https://github.com/slabbdev/navette-monitor
image: https://raw.githubusercontent.com/slabbdev/navette-monitor/main/assets/vinted-check-pass.png
image_alt: "The passing navette-monitor check: Cloudflare challenge cleared, 1,358 product cards asserted"
---

Does your synthetic monitoring still run anywhere useful? Most stacks, Checkly, APM browser checks, cron Playwright jobs, run headless Chromium from a datacenter IP. That is precisely the signature bot walls (Cloudflare, DataDome) are built to stop. The result: your checks "pass" on your own pages and fail on the real web, or worse, they only ever watch pages nobody protects.

Yesterday evening I ran the same check with two monitors against `vinted.fr/catalog?search_text=nike`, a French marketplace behind Cloudflare. Not a manufactured lab: a real site, a real wall, a dated capture.

## One check, two endings

**Monitor 1, naive HTTP** (curl-like, like most "uptime" checks):

```
HTTP/2 403
cf-mitigated: challenge
```

Refused. Not a transient error: the wall classified the request as a bot and served the challenge. An HTTP monitor cannot solve it, it doesn't speak TLS/JA3 like a browser, doesn't run the challenge JavaScript, doesn't prove anything.

**Monitor 2, a navette session** (the system's WebKit engine, a real isolated session):

```
challenge cleared in ~6 s
catalog page loaded
1,358 product cards asserted
```

Same starting IP, same target. The difference is not a user-agent, it's a real render engine, a real challenge/response cycle, a real session. And the check doesn't just "load": it **asserts business content** (1,358 cards), because a check that doesn't verify content won't catch a soft error page served with a 200.

## Why "headless from a datacenter" is dead by design

Anti-bots stopped trying to perfectly separate humans from robots. They score a bundle: TLS fingerprint, headers, behavior, IP reputation. Headless Chromium from a datacenter IP ticks every "automated" box at once. Adding stealth patches, residential proxies, automation flags removed, that is a race already lost, and every layer makes your monitor less representative of your actual users.

The navette session takes the opposite path: it is the machine's browser, with its system engine (WebKit on macOS, WebKitGTK elsewhere), isolated sessions, cookies in the system keychain, driven by a plain JSON HTTP API. No SDK, no flags. It is not stealth: it is structural authenticity.

## The repo, the evidence, the replay

Everything is public: [slabbdev/navette-monitor](https://github.com/slabbdev/navette-monitor). The full check is ~40 lines of bash (`check.sh [url]`), the passing capture is in the repo, and the [landing page](https://slabbdev.github.io/navette-monitor/) shows the evidence. Re-run it yourself: a navette daemon on the local port, and the script does the rest, both monitors, the verdict, the capture.

The limits, stated plainly: this is **one** site, captured **once**, on October 27, 2026 at 18:12 UTC. Walls evolve, heuristics switch sides. A monitor that passes today is not an acquired right, which is exactly why you want a monitor that looks like your users, not one that cheats better. And I have no affiliation with Checkly, Cloudflare, DataDome, or Vinted: the title names the market, the proof is reproducible.

## What it changes

If your synthetic monitoring fails on the pages your users actually see, you are not monitoring your product, you are monitoring your ability to monitor yourself. A check that clears the same walls as your users gives you three things back: alerts that mean something, business-content metrics (not just HTTP codes), and an honest baseline for SLA conversations.

The fleet is coming too: [starflotte](https://github.com/slabbdev/starflotte) runs twenty navettes in parallel on free GitHub Actions runners, that's the next post.
