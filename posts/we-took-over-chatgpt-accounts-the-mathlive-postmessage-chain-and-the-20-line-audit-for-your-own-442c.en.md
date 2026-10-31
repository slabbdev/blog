---
titre: "We took over ChatGPT accounts: the MathLive postMessage chain, and the 20-line audit for your own listeners"
date: 2026-10-31
themes: securite, web
resume: "A shared ChatGPT link, a math keyboard library listening to any sender, an iframe that inherits chatgpt.com, a CSP bypass through YouTube oembed, and the session token: full account takeover, fixed Oct 26. The chain step by step, plus a static audit that flagged the four vulnerable listeners in the library itself."
source: https://dev.to/slabb/we-took-over-chatgpt-accounts-the-mathlive-postmessage-chain-and-the-20-line-audit-for-your-own-442c
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2F6jt6m9jsxg32ygk1yq46.png
image_alt: "We took over ChatGPT accounts: the MathLive postMessage chain and the listener audit"
---

> Yesterday's disclosure from [Parameter](https://www.parameter.ai/labs/we-found-a-gap-at-openai) is the most elegant web exploit of the month: **a complete takeover of ChatGPT accounts where the victim's only action was opening a shared-conversation link**. No paste, no login, no click in the final version: about 4.5 seconds from link to JavaScript running as chatgpt.com, reading private conversations and the session token. Reported October 18, escalated from P2 to P1 on October 21, fixed October 26, bounty $5,000. The root is a class of bug almost every web app ships today, which is why this post is the chain dissected step by step, plus a 100-line static audit I wrote and ran against the vulnerable library: **it flags exactly the four listeners that made this possible, and your codebase can be scanned the same way tonight.**

## The chain, in seven moves

The ingredient list: a shared conversation (public feature), **MathLive** (the math input library ChatGPT loads when a message contains an interactive graph), and the HTML Preview pane that runs on a separate sandboxed origin.

1. **The lure.** Attacker shares a conversation containing a real interactive graph (which makes chatgpt.com load MathLive and install its virtual-keyboard message listener) plus an HTML block.
2. **The unguarded door.** The sandboxed HTML Preview sends `postMessage` calls. MathLive's listener **never checked who the message came from** ("from any web address", per the researchers) and accepted a `update-setting` message carrying attacker-controlled HTML in the keyboard `layouts[].markup` field, then a `show` message.
3. **The sink.** The layout renders through `keyboardContainer.innerHTML`, via a `createHTML` helper that was **a Trusted Types wrapper or identity function, not a sanitizer**. I verified the sink in the shipped bundle: `s.innerHTML = Qi.createHTML(a)` and friends, still present in MathLive 0.100.0.
4. **The origin inheritance.** The injected payload is an `<iframe srcdoc>` **without a sandbox attribute**. A srcdoc iframe inherits the embedding document's origin: the new frame *is* chatgpt.com.
5. **The CSP bypass.** The Content-Security-Policy blocked inline scripts but allowed YouTube. So the payload loads `www.youtube.com/oembed?...&callback=<js>;void`, a JSONP-style response whose body begins with attacker-chosen JavaScript. CSP sees a fetch to youtube.com, allowed. The browser executes the callback as script.
6. **The token.** Running as chatgpt.com, the code reads the session bootstrap data from the page (`#client-bootstrap`) and obtains the access token.
7. **The takeover.** With the token: `GET /backend-api/conversations...`, enumerate, read, exfiltrate via an innocent-looking image request. "Any action on behalf of the victim's ChatGPT account."

Every individual piece is a textbook finding. The lesson is the composition: a library's lax listener plus a sandboxed pane plus a permissive CSP plus an unsandboxed srcdoc equals account takeover on the most-visited AI site on earth.

## The audit: your listeners, tonight

The bug class has a signature: `addEventListener('message', ...)` handlers that never reference `event.origin` or `event.source`. I wrote a static scanner around that signature (heuristic, minified-bundle-friendly, ~100 lines) and ran it on the two things that matter:

```text
$ python3 postmessage_audit.py mathlive-0.100.0.mjs
[RISK] mathlive-0.100.0.mjs:2841 message listener -> NO SENDER CHECK (.origin/.source absent)
[RISK] mathlive-0.100.0.mjs:2931 message listener -> NO SENDER CHECK (.origin/.source absent)
[RISK] mathlive-0.100.0.mjs:2931 message listener -> NO SENDER CHECK (.origin/.source absent)
[RISK] mathlive-0.100.0.mjs:3084 message listener -> NO SENDER CHECK (.origin/.source absent)

$ python3 postmessage_audit.py mathlive-0.111.1.mjs        # current release
(no message listeners flagged in the main bundle)

$ python3 postmessage_audit.py ~/code/my-app/src/           # your turn
```

The core of the check (full script embedded below, self-contained):

```python
PATTERNS = [re.compile(r"addEventListener\(\s*['\"`]message['\"`]\s*,"),
            re.compile(r"onmessage\s*=")]
ORIGIN_OK = re.compile(r"(?:event|e|ev|msg|evt)\.(?:origin|source)\b")
DANGEROUS = re.compile(r"innerHTML|insertAdjacentHTML|document\.write|outerHTML|\beval\(|new Function\(")
# for each listener: extract the handler body; flag if ORIGIN_OK absent,
# and flag louder if a DOM sink lives inside the same handler
```

Honest limits: it is a heuristic on source text (proxy handlers, wrapped frameworks or dynamically-registered listeners can slip through), a clean scan is not a proof, and the runtime gold standard is opening DevTools and watching which listeners react to a synthetic `postMessage` from a foreign origin. But the pattern it flags is precisely the one that cost OpenAI a P1 this month, and it catches the version that had it while passing the one that does not.

The full script (drop it in a repo or run it in CI over your frontend bundles):

```python
#!/usr/bin/env python3
# postmessage_audit.py <file-or-dir> [...] : flag message listeners without sender checks
import re, sys
from pathlib import Path
RX = [re.compile(r"addEventListener\(\s*['\"`]message['\"`]\s*,"), re.compile(r"onmessage\s*=")]
ORIGIN = re.compile(r"(?:event|e|ev|msg|message|evt)\.(?:origin|source)\b")
SINK = re.compile(r"innerHTML|insertAdjacentHTML|document\.write|outerHTML|\beval\(|new Function\(")
def scan(path):
    try: text = path.read_text(errors="replace")
    except Exception: return
    for rx in RX:
        for m in rx.finditer(text):
            win = text[m.end():m.end()+2000]; depth=0; body=""
            for i,ch in enumerate(win):
                if ch=="{": depth+=1
                elif ch=="}":
                    depth-=1
                    if depth==0: body=win[:i+1]; break
            else: body=win[:1500]
            line = text[:m.start()].count("\n")+1
            v=[]
            if not ORIGIN.search(body): v.append("NO SENDER CHECK")
            if SINK.search(body): v.append("DOM sink in handler")
            if v: print(f"[RISK] {path.name}:{line} -> {'; '.join(v)}")
for a in sys.argv[1:]:
    p=Path(a)
    for f in (sorted(p.rglob("*")) if p.is_dir() else [p]):
        if f.suffix in {".js",".mjs",".ts",".jsx",".tsx",".html",".vue",".svelte"}: scan(f)
```

## The four defenses, in order of leverage

1. **Check the sender, always.** First line of every message handler: `if (event.origin !== EXPECTED) return;`. One line, kills the entire class. That line was missing in a library embedded in one of the world's top websites.
2. **A Trusted Types wrapper that sanitizes, or nothing.** `createHTML` that passes bytes through is a compliance badge on an open door. If you adopt Trusted Types, the policy must actually constrain (DOMPurify or equivalent), not just wrap.
3. **Sandbox your srcdocs.** An `<iframe srcdoc>` without `sandbox` inherits your origin. `sandbox="allow-scripts"` (no `allow-same-origin`) makes the injected document powerless against yours. The preview pane was sandboxed; the attacker's frame was not.
4. **CSP is a budget, audit the allowed list.** Any endpoint echoing a callback parameter is a script-execution primitive (JSONP is not dead, it lives in oembed endpoints). `youtube.com` in a CSP is not "just videos": read it as "YouTube decides what JavaScript runs on my page".

## What this means for AI platforms specifically

The trust model of an AI chat app is unusual: **user-generated content becomes application UI** (shared conversations render graphs, previews, embeds inside the first-party origin). Every library the platform loads to render that content inherits the platform's authority, and the attacker gets to choose which content triggers which library. OpenAI's fix (rejecting cross-frame MathLive messages plus CSP changes) is correct and shipped in eight days. The $5,000 bounty for a full account takeover on the flagship product is, let us note in passing, a curious pricing signal.

**TL;DR**: a shared ChatGPT link + MathLive's message listener that trusted any sender + innerHTML sink + unsandboxed srcdoc + YouTube JSONP CSP bypass = the session token and every private conversation, patched October 26. The bug class is `addEventListener('message')` without an origin check; the 100-line audit above flags it in your bundles (and correctly flagged the vulnerable MathLive while passing the fixed one). One line of `event.origin` validation per listener is the whole vaccine.

Sources: [Parameter: We took over ChatGPT accounts](https://www.parameter.ai/labs/we-found-a-gap-at-openai) · [MathLive](https://mathlive.dev/) · audit verified against mathlive 0.100.0 (4 listeners, no sender checks, innerHTML sinks present) and 0.111.1 (pattern absent from main bundle)