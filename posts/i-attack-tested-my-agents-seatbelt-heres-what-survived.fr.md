---
titre: "J'ai attaqué le ceinturon de mon propre agent. Voici ce qui a survécu."
date: 2026-10-03
themes: agents, securite
resume: "Tests d'intrusion sur mes propres garde-fous : ce qui a tenu, ce qui est tombé, receipts à l'appui."
source: https://dev.to/slabb/i-attack-tested-my-agents-seatbelt-heres-what-survived-15mj
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fixan7b1kxxqwnoj0864r.jpeg
image_alt: "J'ai attaqué le ceinturon de mon propre agent. Voici ce qui a survécu."
---


> 🇬🇧 **Cet article n'est pas encore traduit**, la version originale en anglais suit. La traduction arrive.

> A blocklist for destructive agent commands passed its own tests, then failed four bypasses I wrote myself. The fix isn't smarter parsing. Tested receipts inside.

I wrote a seatbelt for my AI coding agent: a `PreToolUse` hook that inspects every `Bash` call before it runs and blocks the destructive ones. It passed its own test suite, five runs, five green.

Then I spent an evening attacking it. This post is the session log: what the blocklist caught, what walked straight through it, what the second version fixed, and where the wall actually is. Everything below ran for real; nothing is reconstructed.

## v1, the blocklist everyone writes

The contract is simple: a `PreToolUse` hook receives the tool call as JSON on stdin, exits `0` to allow, `2` to block, and the hook's `stderr` goes back to the model, which reads why it was blocked and adapts. A skill is advice the model can weigh. A hook is an exit code.

The obvious implementation is a blocklist:

```sh
#!/bin/sh
# PreToolUse hook: reads { tool_name, tool_input } JSON on stdin.
# exit 0 = allow | exit 2 = block, stderr goes back to the agent.
cmd=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["tool_input"].get("command",""))' 2>/dev/null)

case "$cmd" in
  *"rm -rf \$"*|*"rm -rf ~"*|*"rm -rf /"*|\
  *"git push --force"*|*"git push -f"*|\
  *"DROP TABLE"*|*"chmod -R 777 /"*)
    echo "SEATBELT: blocked, destructive pattern matched in: $cmd" >&2
    exit 2 ;;
  *)
    exit 0 ;;
esac
```

Green across the board: `rm -rf $HOME/...` blocked, `mkdir -p build && ls` allowed, `git push --force origin main` blocked, `rm -rf /var/data/scratch` blocked, `DROP TABLE users` blocked. Five for five. Ship it?

Note the `\$` in the first pattern, by the way, the first draft didn't have it, because `sh` expands `$HOME` inside a `case` pattern. The guard was searching for an expanded path while the agent's command contained the literal text. The seatbelt failed its own test before I ever attacked it.

## The bypass round

Then I stopped testing it like a developer and started testing it like the thing it guards against:

```text
$ echo '{"tool_input":{"command":"echo cm0gLXJmIC9EYXRhL3NlY3JldA== | base64 -d | sh"}}' | guard-bash.sh
exit=0

$ echo '{"tool_input":{"command":"python3 -c \"import shutil; shutil.rmtree(...)\""}}' | guard-bash.sh
exit=0

$ echo '{"tool_input":{"command":"find / -name \"*.bak\" -delete"}}' | guard-bash.sh
exit=0

$ echo '{"tool_input":{"command":"git clean -fdx"}}' | guard-bash.sh
exit=0
```

Four attacks, four passes. A base64 pipe hides the verb entirely; `python3 -c` never spells `rm`; `find -delete` is deletion without the letter sequence; `git clean -fdx` is destruction wearing a porcelain face. The blocklist lost before it started, for a structural reason: the set of destructive commands is unbounded, and the shell is a language *designed* for composition. You cannot enumerate what you should fear.

## v2, invert the policy

So stop listing the bad commands and start stating the good territory. Positive policy: destructive verbs are allowed, but their targets must stay inside the project. Parsing gets real, `shlex`, not string matching:

```python
#!/usr/bin/env python3
"""PreToolUse hook, v2, destructive verbs must target paths inside PROJECT."""
import json, shlex, sys, os

PROJECT = os.path.realpath(os.environ.get("PROJECT_ROOT", os.getcwd()))

def inside_project(path: str) -> bool:
    p = os.path.realpath(path)
    return p == PROJECT or p.startswith(PROJECT + os.sep)

def targets_of(argv: list[str]) -> list[str]:
    verb = os.path.basename(argv[0])
    if verb == "rm":
        return [a for a in argv[1:] if not a.startswith("-")]
    if verb == "git" and len(argv) > 1 and argv[1] == "clean":
        return argv[2:]
    return []

call = json.load(sys.stdin)
try:
    argv = shlex.split(call.get("tool_input", {}).get("command", ""))
except ValueError:
    print("SEATBELT: unparseable command, refusing", file=sys.stderr)
    sys.exit(2)

bad = [t for t in targets_of(argv)
       if t.startswith("/") and not inside_project(t)]
if bad:
    print(f"SEATBELT: destructive targets outside {PROJECT}: {bad}", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
```

And it failed its own test again, the good kind of failure. `rm -rf /tmp/seatbelt/build` was blocked as outside the project, because on macOS `/tmp` is a symlink to `/private/tmp`: `realpath` fixed the target while the project root stayed unprefixed. The fix is one line, `realpath` **both** sides, and it's the kind of bug you only find by running the guard against your own machine's pathologies.

After the fix: `rm -rf /Data/secret` blocked, `git clean -fdx /etc` blocked, `rm -rf /tmp/seatbelt/build` allowed. Three for three.

And still: `python3 -c "import shutil; shutil.rmtree(...)"` walks through, because it never spells a destructive verb the parser knows. v2 catches better than v1; it does not catch everything. Nothing that parses the command catches everything.

## Where the wall actually is

The layer that can't be parsed around is the one that doesn't read the command at all:

```text
$ chmod 555 wall/            # the parent directory loses write permission
$ rm -rf wall/secret
rm: wall/secret: Permission denied
exit=1
```

A filesystem permission blocked the deletion with no parser, no pattern list, and nothing for a model to argue with. This is the unglamorous answer most agent-security threads circle past: the sandbox *is* the seatbelt, a separate OS user, a container, a scoped filesystem, and the hook is the polite, inspectable layer in front of it. [Railway's post-incident philosophy](https://blog.railway.com/p/your-ai-wants-to-nuke-your-database) says the same thing in product language: make the destructive thing slow, make the recoverable thing fast. And their [eval harness against destructive behavior](https://dev.to/reidmarlow/action-scaling-at-the-harness-boundary-beats-trajectory-re-runs-n5d) is the maintenance loop, a guard you don't re-attack on a schedule is a guard that's already rotting.


![The hook contract: deterministic code, exit codes, and stderr back to the model](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/x01fa0njdjzv93619646.png)



## What survived the evening

The final architecture is three layers, each with a different job: the **hook** as confirmation gate and tripwire, deterministic, inspectable, honest about patterns; the **OS** as the wall, permissions and sandboxing that no command string can charm; and the **attack session** as the maintenance loop, a calendar entry, not a vibe.

Two honest limits. Every layer described here except the filesystem one is a tripwire, and the python-one-liner class walks through all of them, which is exactly why the OS layer isn't optional. And this was one evening of attacks by the guard's own author; an adversary with more evenings will find more. The seatbelt isn't done. It's just honest about what it is: the layer that catches the boring, irreversible mistakes before the wall has to.

What did your agent run last night that you couldn't have parsed?
