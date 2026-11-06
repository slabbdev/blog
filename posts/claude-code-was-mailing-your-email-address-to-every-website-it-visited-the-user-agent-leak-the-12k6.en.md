---
titre: "Claude Code was mailing your email address to every website it visited: the User-Agent leak, the 5-month system-prompt issue, and the 5-point check"
date: 2026-11-06
themes: securite, agents
resume: "Claude Code put your account email in the User-Agent header of its web requests, so every server log on the agent's path harvested a scam-ready lead, and the same email ships in every session's system prompt, an issue open since July. Fixed by a built-in mod in 2.1.317 after the issue went viral. The runtime test for your install."
source: https://dev.to/slabb/claude-code-was-mailing-your-email-address-to-every-website-it-visited-the-user-agent-leak-the-12k6
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fj9oljnyn04qj9tv7bm7u.png
image_alt: "Claude Code was mailing your email address to every website it visited: the User-Agent leak and the 5-point check"
---

> Two GitHub issues, five months apart, describe the same leak through two different pipes. Yesterday's, filed at 22:13 and now at 360 reactions: **Claude Code sends your account email address to arbitrary third-party websites in the `User-Agent` request header** when its web tools run. The reporter's evidence is his inbox: dozens of scam emails per day, because every server log on the agent's path was harvesting a verified, active, AI-tool-using developer address. The July one (#81138, still open): **the same email is injected into the model's system prompt on every session**, code quoted from the shipped bundle. Anthropic shipped a fix, a built-in `cc-plugin-privacy` mod in v2.1.317+, the same day the newer issue went viral. This post is the mechanics of both pipes, the timeline that says the fix tracked attention rather than the July report, and the five checks that tell you what your install is doing tonight.

## Pipe one: the User-Agent that identified you to strangers

The `User-Agent` header travels with every HTTP request your tools make, and it is logged by default on virtually every web server on earth. Claude Code's web tooling included the signed-in account's email in it. Consequences, in increasing order of bad:

- Every website your agent fetched saw a verified, working email belonging to a developer who pays for AI tooling. That is not a tracking identifier; that is a **pre-qualified lead**, and server logs are bought, sold, leaked, and aggregated as a matter of course.
- It bound your **agent traffic and your human identity into one string**. Sites that wanted to rate-limit agents got everything they needed to rate-limit *you*; sites that wanted to target AI users got the exact address.
- The reporter's flood of scam mail is the expected outcome, not an anomaly: a UA header is a form submission to every intermediary on the path.

And the kicker, which the reporter stated plainly: the identifier did **nothing useful**. It did not help services distinguish agentic traffic (a coarse marker would), it destroyed the anonymity of the session, and it was a scammer goldmine. PII in a header is the worst of both worlds: no functional benefit, total exposure.

## Pipe two: the email inside every system prompt

The July issue (#81138, filed 2026-07-25, titled "[BUG] Account email (PII) is injected into the model's system prompt without consent") documents the other pipe, with bundle code quoted from v2.1.220:

```js
let n = process.env.ANTHROPIC_UNIX_SOCKET ? void 0 : dc()?.emailAddress
return {
  ...(n && { userEmail: `The user's email address is ${n}.` }),
  ...
}
```

Which renders into every session's system prompt as:

```text
# userEmail
The user's email address is <account email>.
```

Sourced from `~/.claude.json` → `oauthAccount.emailAddress`. Where does a system prompt travel? To the API, into logs on both sides, into any context the session touches, and from there, potentially, into anything the model quotes or forwards. The issue's framing is precise and worth repeating: personal data given for **authentication**, repurposed as **session content**, without consent or disclosure. As of tonight that issue is still open.

## The timeline that matters

- **July 25**: #81138 files the system-prompt injection, with bundle source. No fix lands.
- **November 5, 22:13**: #107757 files the User-Agent variant. Reactions climb into the hundreds within the day.
- **November 5, same day**: an Anthropic contributor replies: a built-in mod, `cc-plugin-privacy`, introduced in **v2.1.317 and later**, "deterministically blocks this behavior", is enabled by default, can be toggled via `/plugins`, and its source will be published alongside the other built-in mods.
- **The anomaly worth watching**: the reporter ran **v2.1.318**, allegedly post-fix, and still saw the leak. Possibilities: the mod was disabled on his machine, the blocking has a gap (the staff reply explicitly asks for gap reports), or version confusion. "Enabled by default" is not "verified on your machine", which is what the runtime check below is for.

One comment in the thread names the uncomfortable pattern: the original privacy issue sat for five months, and the fix shipped the day the new one hit the front page. "You can literally sort issues by emoji count and 80/20 it." An agent could triage that queue; the queue's owners apparently needed HN instead.

## The five-point check for your install

Run on any machine with Claude Code. On mine, the CLI is absent but `~/.claude.json` exists with no `oauthAccount` (so the PII field is empty): your results will vary, and check 3 is the one that settles everything.

```bash
# 1. Version: the built-in privacy mod ships in 2.1.317+
claude --version

# 2. Is the mod present and enabled?
#    In Claude Code: /plugins   -> look for cc-plugin-privacy (default: on)

# 3. THE RUNTIME TEST: a local listener tells you what your agent actually sends:
mkdir /tmp/uatest && cd /tmp/uatest && python3 -m http.server 8899 &
# then, inside Claude Code, ask it to fetch:  http://127.0.0.1:8899/probe
# and read the log line that appears:
#   "GET /probe HTTP/1.1" 200 -        <- the UA is what python logs BEFORE this
# better, log it explicitly:
python3 -c "from http.server import *; import sys
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        print('UA =', self.headers.get('User-Agent'), file=sys.stderr, flush=True)
        self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
HTTPServer(('127.0.0.1', 8899), H).serve_forever()"
# UA contains your email  -> still leaking (report it: issue #107757)
# UA is a generic string   -> blocked on your build

# 4. What is at stake locally: does your config even carry the email?
python3 -c "import json,os; d=json.load(open(os.path.expanduser('~/.claude.json'))); \
print('email present:', 'emailAddress' in d.get('oauthAccount', {}))"

# 5. The system-prompt check (July issue): in a fresh Claude Code session, ask:
#    \"What is my email address?\"
#    If the model knows it unprompted, the #userEmail block is still in your prompt.
```

Check 5 doubles as the general lesson: ask your agent what it knows about you. It reads its system prompt more honestly than the changelog reads.

## The principle, and the month's pattern

Your agent is you on the web. Its headers are your headers, its prompts are your context, and everything it carries leaks at the union of every hop. Identifying agentic traffic is a legitimate need, and the correct answer is a **class marker** ("this is an automated client, product X, version Y"), not **your identity**. Anthropic's fix, a deterministic blocking mod, is the right shape, and shipping it by default is right; the five-month gap between report and fix, and the fact that it closed only under viral load, is the part to remember at renewal time.

The ledger of the agent era, one more line: transcripts shipped to the model, extensions backdooring at load, a vendor installing itself into rival agents, and now the agent leaking your address to every server it touched. Same target every time: **the agent's outbound surface is the user's outbound surface**. Audit it like it is yours, because it is.

**TL;DR**: Claude Code put your account email in the User-Agent of its web requests (every server log got a scam-ready lead; the reporter's inbox proved it) and ships the same email inside every session's system prompt (issue open since July 25). Fixed by the built-in `cc-plugin-privacy` mod in 2.1.317+ the day the new issue went viral; the reporter was on .318 and still saw it, so run the runtime check: local listener, make your agent fetch it, read the UA. Five checks above; two minutes; your inbox will thank you.

Sources: [Issue #107757: Privacy violation in User-Agent header](https://github.com/anthropics/claude-code/issues/107757) (report + staff reply re cc-plugin-privacy) · [Issue #81138: email in the system prompt, July 25, bundle code](https://github.com/anthropics/claude-code/issues/81138) · built-in mods: [github.com/anthropics/claude-code/tree/main/mods](https://github.com/anthropics/claude-code/tree/main/mods)