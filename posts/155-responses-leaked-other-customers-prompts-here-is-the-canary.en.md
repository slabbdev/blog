---
titre: "155 responses leaked other customers' prompts. Here is the canary that catches it on your provider."
date: 2026-10-30
themes: ia, securite
resume: "The Cloudflare/SGLang incident: a KV pool at 65% of the context window plus a rejection path that kept going after refusal = 155 cross-customer leaks with HTTP 200. The mechanism, and the canary we actually ran."
source: https://blog.cloudflare.com/kv-cache-exposure-remediation/
---

Between August 27 and September 9, some responses from GLM-5.3 on Cloudflare Workers AI contained **other customers' prompts and partial generations**. Not a database breach, not a prompt injection — the inference engine itself served **stale KV-cache pages from previous, unrelated requests**, with a clean HTTP 200. Exactly **155 responses** affected, all triggered by prompts longer than **681,280 tokens**. Cloudflare published the full autopsy.

The detail that should stop you: **681,280 is 65% of 1,048,576** — the model's context window. Someone sized the KV pool at roughly two-thirds of the context and shipped. Everything else follows from that one number.

## The failure chain, step by step

From [Cloudflare's disclosure](https://blog.cloudflare.com/kv-cache-exposure-remediation/), cross-checked against [SGLang issue #30233](https://github.com/sgl-project/sglang/issues/30233) (open since July 6):

1. **The mismatch.** GLM-5.3 launched with a 1,048,576-token context window, but the prefill KV pool held only 681,280 tokens. Cloudflare knew the pool was smaller and *believed* the engine would cleanly reject oversized prompts.
2. **The rejection path.** A prompt longer than the pool gets rejected in prefill — but in **disaggregated prefill/decode mode**, the rejected prompt was "replaced with a one-token placeholder," and prefill transferred just that placeholder's KV pages to decode. No error was returned.
3. **The uninitialized read.** Decode had reserved **8 KV pages** for the request. Only page P0 was ever written. Attention then **read all 8 reserved pages** — 7 of which still contained data from *earlier requests on the same node*. Other customers' prompts, other customers' generations.
4. **The clean 200.** The response streamed out composed partly of someone else's context. No error code, no anomaly — which is why it took an external researcher, not monitoring, to catch it.

Two bugs overlapped: a **configuration bug** (pool < context — Cloudflare's) and an **engine bug** (rejected requests surviving to the KV handoff — SGLang's, generic to disaggregated deployments, fixed in **v0.5.22**). And a third factor that isn't a bug at all: **KV pages aren't zeroed between requests by design** — performance depends on reuse. The entire safety of the architecture rests on the bookkeeping around those pages being airtight.

## The canary — and what it said when we ran it

You cannot audit a provider's KV pool from the outside. You *can* detect the symptom class: data from request A surfacing in the response to request B. The script (`canary.py`, ~40 lines, stdlib only) plants a unique marker in session A, then scans the responses of unrelated requests for that marker — against any OpenAI-compatible endpoint.

We ran it for real, pre-registered protocol, on October 27-28 (the full run-log is public):

- **Canary planted, 5 scan requests: 5/5 clean** — zero cross-request content.
- **Probe at 671,280 tokens** (the Cloudflare pool figure): **HTTP 400, error 1261 "Prompt exceeds max length", in 12 s** — the fail-closed reject whose absence produced the leak.
- **Probe at ~520k tokens**: accepted, clean reply, no marker echo.
- **Bounding the real cap**: 522,763 tokens accepted, 671,280 rejected — a deliberate 0.5M-class cap, and the incident's threshold is unreachable on this provider.
- **Never-sent canaries** ×3: zero hits in any response — the negative control proving the scanner doesn't match into thin air.

The script's own honest line applies to us too: **a clean run is not a proof**. The GLM-5.3 bug needed prompts beyond the pool on a misconfigured node. This catches gross leakage cheaply; run it after every upgrade, against every new endpoint.

## If you run the engine yourself

The operator checklist, in priority order: upgrade to **SGLang v0.5.22+** (rejected requests are retired at the admission queue, before any KV transfer); make your **KV pool larger than your context window** — with the pre-deployment check that compares the two, because GLM-5.3 shipped without it; enable `--disaggregation-enable-kv-checksum` so every prefill→decode transfer is verified. This bug was reported in July, exploited-by-accident in August, disclosed properly in October — if you deployed SGLang from a summer image, you are the audience for that checklist.

## TL;DR

A KV pool at 65% of the context window plus a rejection path that kept going after refusal equals 155 cross-customer leaks with HTTP 200. Root-caused in 25 minutes, fixed in a day, disclosed with page-level diagrams. Zero errors on the wire is not the same as zero leaks — and the canary that checks your provider takes five minutes.

Sources: [Cloudflare — KV cache exposure remediation](https://blog.cloudflare.com/kv-cache-exposure-remediation/) · [SGLang issue #30233](https://github.com/sgl-project/sglang/issues/30233) · [SGLang PR #38704 (Cloudflare draft)](https://github.com/sgl-project/sglang/pull/38704)
