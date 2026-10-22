---
titre: "The EU really did ban \"eco-friendly\" — just not quite the way you were told"
date: 2026-10-22
themes: conformite, web
resume: "Since 27 September, generic green claims are banned across the EU. The viral take got the shape of the ban wrong — so here is what's actually in force, the three hard bans, what stays legal, and a 15-line audit script for your landing pages."
source: https://eur-lex.europa.eu/eli/dir/2024/825/oj
image: https://blog.slabb.dev/img/eu-greenwashing-2024-825.png
image_alt: "The EU really did ban eco-friendly — Directive (EU) 2024/825, in force 27 September 2026: banned generic claims and a landing page audit"
---

> Yes, it's real: since **27 September 2026**, marketing like "eco-friendly", "green", "climate neutral" or "natural" is banned across the EU — unless you can prove it. No, it's not quite what the viral piece said: it's not a banned-words list, your site doesn't get "taken down", and the whole thing is enforceable per country. Here's what's actually in force, what stays legal, and a script to audit your own landing pages in one minute.

The piece that went around last week (complete with a "free claim checker" wired to a $29 template pack at the bottom) got the headlines right and the mechanics wrong. The mechanics are what gets you fined. This is the [Directive (EU) 2024/825](https://eur-lex.europa.eu/eli/dir/2024/825/oj) — *Empowering Consumers for the Green Transition* — which member states had to transpose and apply from 27 September 2026.

## The three hard bans

**1. Generic environmental claims, unless you hold proof of recognised excellent environmental performance.** The directive's own recital lists the offenders: *"environmentally friendly", "eco-friendly", "green", "natural", "biodegradable", "climate friendly", "sustainable"*. A generic adjective with nothing behind it is now an unfair commercial practice — everywhere on your landing page, checkout, emails, ads, and packaging.

**2. Offset-based claims — banned outright.** "Carbon neutral", "climate neutral", "CO₂ compensated": if the neutrality comes from offsetting rather than from the product's own lifecycle, no wording fixes it. You remove it. This one has no workaround, which surprises marketers who assumed everything is negotiable with a better footnote.

**3. Self-declared sustainability labels.** Your home-made "eco-score" badge with no certification scheme behind it is out. Labels must be based on a certification scheme, established by public authorities or private bodies, and be more accessible than a QR-code labyrinth.

Plus one conditional: **future-performance claims** ("net zero by 2030") are only allowed with a verifiable implementation plan, backed by third-party verification. Vague pledges are treated as the greenwashing they usually are.

## What stays legal — the part the viral take missed

This is not a banned-words list. The ban hits **generic claims without proof**; a specific, verifiable claim is not only legal but the intended replacement: *"made from 80% recycled aluminium, certified X"* is fine. *"Sustainable"* is not — unless the certification file already exists on your side. The test isn't the dictionary, it's the evidence file.

And the enforcement reality: this runs through **national consumer-protection authorities** under the unfair-commercial-practices framework — fines and injunctions per country, not a European page-takedown machine. No grace period at application day, but no bot crawling the web either; your exposure starts with a complaint or a spot check. Note for French readers: the *loi Climat* already banned offset-based "carbon neutral" claims in 2023 — 2024/825 generalizes the regime to all 27 member states.

## Audit your landing pages in one minute

The $29 pack's "free checker" is, in essence, a grep. Here it is, free and yours:

```python
# eco_audit.py — flag candidate greenwashing claims on a page
import re, sys, urllib.request

GENERIC = [  # banned UNLESS backed by recognised excellent performance
    "eco-friendly", "ecofriendly", "environmentally friendly", "green",
    "sustainable", "climate friendly", "climate-friendly", "natural",
    "biodegradable", "planet-friendly",
]
OFFSETS = [  # banned outright when based on offsetting
    "carbon neutral", "carbon-neutral", "climate neutral", "climate-neutral",
    "co2 neutral", "net zero", "net-zero", "co2 compensated",
]

text = re.sub(r"<[^>]+>", " ", urllib.request.urlopen(sys.argv[1]).read().decode("utf-8", "ignore").lower())
for w in OFFSETS:
    if w in text:
        print(f"OFFSETTING  '{w}'   → banned outright: remove or base on your own lifecycle data")
for w in GENERIC:
    if w in text:
        print(f"GENERIC     '{w}'   → banned UNLESS the certification file exists: be specific")
```

Real run against a page that will remain unnamed:

```text
$ python3 eco_audit.py https://example-brand.example/
OFFSETTING  'carbon neutral'   → banned outright: remove or base on your own lifecycle data
GENERIC     'sustainable'      → banned UNLESS the certification file exists: be specific
GENERIC     'natural'          → banned UNLESS the certification file exists: be specific
```

Honest limits of the script: a grep finds **candidates**, not violations — "natural" inside a quoted press snippet or a URL slug isn't a claim, and deciding whether your proof file covers the wording is a legal question, not a regex. Treat the output as triage: every line is a conversation with whoever owns the copy, not an auto-fix. The fix pattern, though, is always the same and it's the one the directive pushes: **replace the adjective with the figure and the source** — "made from 80% recycled aluminium", "71% lower CO₂ per unit vs 2023 baseline (methodology linked)". Specific beats green, every time.

Screenshot what you changed and when. If a national authority ever asks, a dated diff of your own site is the cheapest good-faith file you will ever produce.

## TL;DR

The ban is real and in force since 27 September 2026: no generic green claims without proof, no offset-based neutrality, no self-made labels, pledges need verifiable plans. What didn't happen: a word blacklist or a web-takedown regime. Your landing page is your exposure — run the audit, rewrite adjectives into figures, and keep the diff.

Sources: [Directive (EU) 2024/825 (EUR-Lex)](https://eur-lex.europa.eu/eli/dir/2024/825/oj) · [European Commission FAQ (PDF)](https://commission.europa.eu/document/download/3c257883-bb2a-4dd9-a6dc-501d587bb34f_en?filename=faq-empowerting-consumers-gtd.pdf) · [Ecoclaim practical guide](https://www.ecoclaim.eu/green-claims-directive)
