---
titre: "155 responses leaked between AI customers: the GLM-5.3 KV cache bug — and the canary test for your provider"
date: 2026-10-27
themes: securite, ia
resume: "On Cloudflare Workers AI, 155 GLM-5.3 responses contained other customers' data — stale KV-cache pages served with HTTP 200. The mechanism, the 25-minute repro, the SGLang bug behind it, and a canary script that tests YOUR provider."
source: https://dev.to/slabb/155-responses-leaked-between-ai-customers-the-glm-53-kv-cache-bug-and-the-canary-test-for-your-59n8
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Ffni04et32wbrfou5e08s.png
image_alt: "155 responses leaked between AI customers — the GLM-5.3 KV cache bug and the canary test"
---

> Between August 27 and September 9, some responses from GLM-5.3 on Cloudflare Workers AI contained **other customers' prompts and partial generations**. Not a breach of a database, not a prompt injection — the inference engine itself served **stale KV-cache pages from previous, unrelated requests**, with a clean HTTP 200. Exactly **155 responses** were affected, all triggered by prompts longer than **681,280 tokens**. Cloudflare published the full autopsy yesterday. This post is the mechanism in four steps, why the same bug class may sit in other inference stacks, and a canary script that tests your own provider for cross-request leakage.

The detail that should stop you: **681,280 is 65% of 1,048,576** — the model's context window. Someone sized the KV pool at roughly two-thirds of the context and shipped it. Everything else follows from that one number.

## The failure chain, step by step

From [Cloudflare's disclosure](https://blog.cloudflare.com/kv-cache-exposure-remediation/), cross-checked against [SGLang issue #30233](https://github.com/sgl-project/sglang/issues/30233) (open since July 6):

1. **The mismatch.** GLM-5.3 launched with a 1,048,576-token context window, but the prefill KV pool held only 681,280 tokens. Cloudflare knew the pool was smaller and *believed* the engine would cleanly reject oversized prompts.
2. **The rejection path.** A prompt longer than the pool gets rejected in prefill — but in **disaggregated prefill/decode mode**, the rejected prompt was "replaced with a one-token placeholder," and prefill transferred just that placeholder's KV pages to decode. No error was returned.
3. **The uninitialized read.** Decode had reserved **8 KV pages** for the request. Only page P0 was ever written. Attention then **read all 8 reserved pages** — 7 of which still contained data from *earlier requests on the same node*. Other customers' prompts, other customers' generations.
4. **The clean 200.** The response streamed out composed partly of someone else's context. No error code, no anomaly — which is why it took an external researcher, not monitoring, to catch it.

Two bugs overlapped: a **configuration bug** (pool < context — Cloudflare's, and only GLM-5.3 was affected there because every other Workers AI model had a pool larger than its context) and an **engine bug** (rejected requests surviving to the KV handoff — SGLang's, generic to disaggregated deployments, fixed in **v0.5.22** after Cloudflare's draft PR #38704 and the merged follow-ups #36988/#38935). And a third factor that isn't a bug at all: **KV pages aren't zeroed between requests by design** — performance depends on reuse. The entire safety of the architecture rests on the bookkeeping around those pages being airtight.

## The timeline worth studying

Reported by Gadi Evron (Knostic) via HackerOne on **September 8, 23:11 UTC**. Reproduced by Cloudflare **within 25 minutes**. Model private at 14:00 the next day, root cause at 14:35, fixed config at 14:52, model restored at 19:40. Coordinated disclosure published October 26 with the reporter and the SGLang maintainers, complete with page diagrams, issue links, and the exact number of affected responses.

Set that next to the same month's eMudhra response (revocation in 14 hours, then blaming "social media amplification" for the scrutiny) and you have the two poles of incident handling. Cloudflare's post even ends with the hardening roadmap — KV checksums on every prefill-to-decode transfer, canaries, per-page ownership tags, and **formal verification of the RDMA transfer protocol**. When the failure mode is "the bookkeeping lied," you eventually stop patching and start proving.

## The lab: a canary test for YOUR provider

You cannot audit a provider's KV pool from the outside. You *can* detect the symptom class: data from request A surfacing in the response to request B. That's exactly what Cloudflare's post-incident canaries do — here is the userland version, works against any OpenAI-compatible endpoint (point `BASE`/`KEY`/`MODEL` at OpenAI, Anthropic-compatible gateways, vLLM, SGLang, llamacpp, Ollama):

```python
# canary.py — cross-request leak smoke test for chat APIs
# usage: BASE=https://api.provider.com/v1 KEY=sk-... MODEL=... python3 canary.py
import os, random, string, sys, urllib.request

BASE  = os.environ["BASE"].rstrip("/")   # e.g. http://localhost:8000/v1
KEY   = os.environ.get("KEY", "none")
MODEL = os.environ["MODEL"]
canary = "CANARY-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=16))

def chat(messages, max_tokens=200):
    req = urllib.request.Request(
        f"{BASE}/chat/completions",
        data=__import__("json").dumps({"model": MODEL, "messages": messages,
                                       "max_tokens": max_tokens, "temperature": 0}).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    return __import__("json").loads(urllib.request.urlopen(req, timeout=120).read())

# A — plant the canary
chat([{"role": "user", "content": f"Internal ref for this session: {canary}. Reply with 'noted' only."}])
print(f"[A] canary planted: {canary}")

# B — unrelated requests; scan every response for the canary
leak = False
for i in range(1, 6):
    r = chat([{"role": "user", "content": f"Write a two-sentence haiku about packet #{i}."}])
    text = r["choices"][0]["message"]["content"]
    hit = canary in text
    leak |= hit
    print(f"[B{i}] {'!!! CANARY LEAKED' if hit else 'clean'} — {text[:60]!r}")
print("RESULT:", "CROSS-REQUEST LEAK DETECTED" if leak else "no leak in this sample (not a proof)")
```

Honest scope, stated in the script's last line: **a clean run is not a proof** — the GLM-5.3 bug needed prompts beyond the KV pool on a misconfigured node. This catches gross leakage cheaply; run it after upgrades, against new endpoints, and in CI against your own inference stack. On providers, vary it: repeat with the B requests on a *fresh session/conversation id* — same-account separation is the weakest fence to test.

I ran the smoke test against the API that generates this blog's drafts (Z.ai's own GLM serving — for the record, the incident was Cloudflare's deployment, not Z.ai's). The full run happened October 27-28, pre-registered protocol, run-log public:

- canary planted, 5 scan requests — **5/5 clean**;
- probe at **671,280 tokens** (the Cloudflare pool figure): **HTTP 400, error 1261 "Prompt exceeds max length", in 12 s** — the fail-closed reject whose absence produced the leak;
- ~520k-token probe: accepted, clean reply, no marker echo;
- bounding the real cap: **522,763 tokens accepted, 671,280 rejected** — a deliberate 0.5M-class cap that puts the incident's threshold out of reach on this provider;
- three never-sent canaries: **zero hits** in any response — the negative control that proves the scanner doesn't match thin air.

The script's honest line still applies: a clean run is not a proof. The GLM-5.3 bug needed prompts beyond the pool on a misconfigured node — this catches gross leakage cheaply. Run it after every upgrade, against every new endpoint.

## If you run the engine yourself

The operator checklist from the post, in priority order: upgrade to **SGLang v0.5.22+** (rejected requests are retired at the admission queue, before any KV transfer); make your **KV pool larger than your context window** — and add the pre-deployment check that compares measured pool size to context length, because GLM-5.3 shipped without it; enable `--disaggregation-enable-kv-checksum` so every prefill→decode transfer is verified. The bug you're patching was reported in July, exploited-by-accident in August, and disclosed properly in October — if you deployed SGLang from a summer image, you are the audience for that checklist.

## TL;DR

A KV pool sized at 65% of the context window plus a rejection path that kept going after refusal equals 155 cross-customer leaks with HTTP 200. Root-caused in 25 minutes, fixed in a day, disclosed with page-level diagrams — and the engine bug underneath is generic, so if you self-host inference, this is your patch-week. Everyone else: the canary script above is five minutes against your provider. Zero errors on the wire is not the same as zero leaks.

Sources: [Cloudflare — KV cache exposure remediation](https://blog.cloudflare.com/kv-cache-exposure-remediation/) · [SGLang issue #30233](https://github.com/sgl-project/sglang/issues/30233) · [SGLang PR #38704 (Cloudflare draft)](https://github.com/sgl-project/sglang/pull/38704)