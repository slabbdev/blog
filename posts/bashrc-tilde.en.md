---
titre: "One quoted tilde in your .bashrc is an attacker-controlled PATH entry"
date: 2026-10-11
themes: securite
resume: "export PATH=\"$PATH:~/.local/bin/\" — the quotes stop tilde expansion, the entry resolves against your current directory, and anyone who can create a ~ folder there owns your shell. Verified live."
source: https://dev.to/slabb/one-quoted-tilde-in-your-bashrc-is-an-attacker-controlled-path-entry-5hc8
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2F40vw7d75nkuew2l08wkm.png
image_alt: "One quoted tilde in your .bashrc is an attacker-controlled PATH entry"
---

There is one line in thousands of `.bashrc` files that looks perfectly correct and does something quietly hostile:

```sh
export PATH="$PATH:~/.local/bin/"
```

Everyone knows not to put raw `~` unquoted in scripts, so the quotes feel like hygiene. They are the bug. Inside double quotes, tilde expansion does not happen — so what lands in your `PATH` is the literal string `~/.local/bin/`, not your home directory. And a `PATH` entry that doesn't start with `/` resolves **relative to your current directory**.

I reproduced the whole chain this morning in a throwaway sandbox, because [disconnect3d's writeup](https://disconnect3d.pl/2026/10/02/dont-put-tilde-in-your-path/) landed on the HN front page today and my rule is to run what I audit. Three commands, three receipts.

## The receipts

```sh
# 1. The .bashrc line, quoted tilde — what actually lands in PATH:
$ export PATH="$PATH:~/.local/bin/"
$ echo "$PATH" | tr ':' '\n' | grep '~'
~/.local/bin/

# 2. An attacker creates ~/ in a directory you cd into, plants a binary,
#    you type a command name — executed from the planted path:
$ kek
EXECUTED FROM: /tmp/tilde-test/~/.local/bin//kek

# 3. Your real home directory was never involved:
$ ls ~/.local/bin/kek
ls: /Users/you/.local/bin/kek: No such file or directory
```

That second line is the whole story. A binary at `./~/.local/bin/kek` — inside a literal folder named `~` in whatever directory you happen to be in — was found and executed through your `PATH`. The home directory was never touched. The attacker never needed a vulnerability. They needed a directory named `~` and your habit of `cd`-ing into checkouts.

## The attack, in one paragraph

Anyone who can create a `~` subdirectory in a directory you commonly work in — a repository you cloned, a shared sandbox, a project checkout with a helpful `bin/` — plants `~/.local/bin/evil` there. You `cd` in. Your shell carries the literal `~/.local/bin/` entry from that quoted `.bashrc` line. The next command name you type that isn't found earlier in the `PATH` resolves to `./~/.local/bin/evil`, and runs. No privilege escalation. No exploit. User-level code execution via one unexpanded character and your own working habits.

## This bug family has a name: the boundary moved

This is the third member of the same family this blog has covered in two weeks, and the family is worth naming because the members look unrelated and fail identically.

In [my seatbelt post](https://dev.to/slabb/i-attack-tested-my-agents-seatbelt-heres-what-survived-15mj), a `case` pattern expanded `$HOME` while the agent's command contained the literal text — the boundary between *pattern* and *data* silently moved. In [the Telegram writeup](https://dev.to/slabb/one-unescaped-semicolon-was-enough-to-steal-telegram-accounts-5gja), a semicolon inside a URL crossed from *payload* into *command* because nobody escaped the record separator. Here, a pair of quotes decides whether `~` means *your home* or *a directory literally named tilde*. Three different shells, three different decades, one law: **anywhere text crosses into a position the machine interprets, the boundary is a decision — and text will test it.**

Bash's own manual states the rule that bites here, and it is exactly as fragile as it sounds: expansion happens for "unquoted tilde-prefixes immediately following a ':' or the first '='". Quoted: nothing. Unquoted: expansion — and, as the writeup notes, the unquoted form is itself fragile, because "a whitespace will break the variable assignment".

## The AI angle hiding in the disclosure

The part that made this post mandatory for me is one line of provenance: the author found this because [nono](https://nono.sh/), an agent-sandboxing tool, warned that a `PATH` entry was sandbox-writable. Read that again — **an agent harness flagged a 40-year-old shell trap that its user had lived with for years.**

That is the quiet argument for the sandboxing layer this lane keeps building: an agent sandbox has to *model* what is writable, which forces it to resolve paths honestly — and honest resolution has no nostalgia for the tilde expansion you intended. The human wrote `~/.local/bin/` meaning `/home/me/.local/bin/`; the machine stored `~/.local/bin/`; the sandbox was the only component that compared the two. When agent tooling starts auditing fifty years of shell expansion rules instead of just fencing prompts, this is the class of find that falls out.

![quoted tilde → literal entry → CWD-relative → ./~/.local/bin/ → exec](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/8ejxcc4vc0zrunkrrxrx.png)

## What to steal

- **Check yourself tonight, ten seconds:**

```sh
echo "$PATH" | tr ':' '\n' | grep '~'
```

  If anything prints, your shell has a CWD-relative entry. Fix every `.bashrc`, `.zshrc`, `.profile` that contains it.
- **The robust form is already what you meant:**

```sh
export PATH="$PATH:$HOME/.local/bin/"
```

  `$HOME` expands inside double quotes; `~` only expands unquoted. Prefer `$HOME` in anything quoted — the author's own recommendation.
- **Treat unexplained directories in repos as hostile**, including cute ones. A `~` folder in a checkout is not a joke about homes; it is a drop site for your next mistyped command.
- **If you build agent sandboxes**: enumerate expansion rules (tilde, variables, globs, braces) as part of your threat model. The sandbox that warned here won because it refused to interpret intent.

## Two honest limits

**The attack needs an attacker-writable directory in your `cd` habits.** A repository you cloned from a stranger is the realistic vector — and "I clone things and run commands in them" describes most developers most days. But if your working directories are never attacker-writable, the primitive waits instead of firing. My reproduction ran in a throwaway sandbox on my own machine, not against a production account.

**And there is no CVE, no patch, no vendor to wait for.** Tilde expansion rules are older than Linux and are documented behavior, not a defect — this is a footgun in the contract between quoting and expansion, which means the fix is your dotfiles and your audits, forever. That is also why the post carries a live reproduction instead of a ticket number: the receipt you can run tonight is the whole disclosure.

## Your turn

Run the check — `echo "$PATH" | tr ':' '\n' | grep '~'` — and post what you find, including the embarrassing results. Mine had the entry. If you have been running with a literal tilde in your `PATH` for years, I want to hear how long, and whether anything ever landed in one of those directories. Wrong-command war stories go in the comments.
