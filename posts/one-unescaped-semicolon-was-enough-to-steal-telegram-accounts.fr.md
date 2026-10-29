---
titre: "Un point-virgule non échappé suffisait à voler des comptes Telegram"
date: 2026-10-10
themes: securite
resume: "Anatomie d'un one-liner shell : de l'échappement oublié au vol de session."
source: https://dev.to/slabb/one-unescaped-semicolon-was-enough-to-steal-telegram-accounts-5gja
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fafa4l6yha1va26wo1lw4.png
image_alt: "Un point-virgule non échappé suffisait à voler des comptes Telegram"
---


> 🇬🇧 **Cet article n'est pas encore traduit**, la version originale en anglais suit. La traduction arrive.

On June 25, a researcher reported to ZDI: a single clicked `https://` link could read three files from a Telegram Desktop user's machine and ship them to an attacker's channel. The three files are the entire account. By September 17 they were fixed, and the changelog that shipped the fix to hundreds of millions of users described a rendering improvement.

The writeup landed October 3 ([beaksec](https://beaksec.github.io/posts/telegram-desktop-one-click-account-takeover/)), the CVE on October 7, **CVE-2026-107181, CVSS 8.1**, and the public PoC this week. dev.to coverage, as of tonight: none. So here is the anatomy, because the bug itself deserves the attention the changelog refused to give it.

## Semicolons on a local socket

Telegram Desktop registers the `tg://` URL scheme. Click a `tg://` link anywhere in your OS and the handler launches a second process, which connects to a local socket where your running instance listens, and forwards the URL. Single-instance IPC, a pattern older than most languages reading this.

The serialization is homemade: keyword, argument, semicolon terminator. `OPEN:tg://x?a=1;`. The receiver splits at every semicolon and treats each fragment as a command.

The semicolon is never escaped when the URL is embedded. The researcher's line is the whole bug, and one of the best one-sentence descriptions of an injection I have read: the URL "is only a carrier", once data crosses into the record, "the boundaries inside the data stop being held by the structure and become characters in the text."

`tg://x?a=1;CMD:quit` arrives as one URL. The running instance parses two commands.

## The chain, receipt by receipt

![The attack chain: staging, the click, the reader, the haul, CVE-2026-107181](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/rl5dkiz26fjayu6zl5sa.png)

1. **The staging.** Attacker creates a supergroup; default privacy settings let them add the victim silently. They post three plain-text instruction files. Default auto-download pulls anything under 8 MiB into `Downloads/Telegram Desktop/`. The files omit the `from:` line, skipping the account-ID check, and name the attacker's channel as destination.
2. **The click.** Victim clicks a normal `https://` link in chat. (Links clicked *inside* Telegram never reach the socket, the browser is the required relay.) The attacker's server answers 302 → `tg://…` carrying stacked injected commands, including `;OPEN:interpret:../../../Downloads/Telegram%20Desktop/instructions1.txt`. Relative paths, because the download folder resolves from the data directory, no username needed.
3. **The reader.** `interpret:` is a legacy internal scheme wired to `InterpretSendPath` in `support_helper.cpp`, a helper from the release-publishing workflow that reads a file and *sends it*, with no authorization check and no confirmation (`support_helper.cpp:673-680`: `if (!f.open(QIODevice::ReadOnly))`). The injection point itself is the URL join in `sandbox.cpp:295-297`.
4. **The haul.** One click, three files: `key_datas`, `D877F783D5D3EF8Cs`, and its `maps` index. That is the salt-plus-wrapped-DEK, the MTProto authorization, and the index. Dropped into a fresh `tdata` folder on any machine, they are the victim's session, the exact equivalent of stealing a session cookie.

A helper that "just reads files for the build pipeline" turned out to be a remote file-transfer service for anyone who could name a path. Dead code that can *act* is not dead code. It is an unadvertised API.

## This bug is fifty years old

Strip the Telegram branding and the skeleton is the oldest injection class in the book: a serialization boundary where data is allowed to contain the delimiter. CSV formula injection. CRLF in mail headers. HTTP response splitting. Shell word splitting. SQL concatenation. Every one is "the payload contains the separator, and nobody escaped the separator."

I hit the same class on a smaller stage writing a seatbelt for my own coding agent: a shell `case` pattern expanded `$HOME` while the agent's command contained the literal text, the boundary between pattern and data silently moved. And the modern member of the family is the one this column keeps returning to: prompt injection is separator injection where the delimiter is natural language and the IPC channel is the model's context window. Tool output that contains instructions works for exactly the same reason `;CMD:quit` worked. "The boundaries stop being held by the structure", swap "structure" for "system prompt" and the sentence ships in a 2026 agent incident report.

The fix receipt is the lesson made code: Telegram's patch ([commit db3405699f](https://github.com/telegramdesktop/tdesktop/commit/db3405699f), "Remove legacy interpret path helper", 11 files, +126/−372) adds `EscapeTo7bit`/`EscapeFrom7bit`, percent-encoding every character below 32, above 127, or equal to `%` or `;`, and drops local file paths entirely when a non-local URL shares the connection. Escape the delimiter. Kill the dead capability. Both, not either.

## Encryption that decrypts with nothing

The second half of the writeup is quieter and, for my money, worse.

Telegram encrypts local session data. The design: a data-encryption key (DEK) wraps your data; a key-encryption key (KEK) wraps the DEK; the KEK derives from your local passcode plus a salt. Sound.

**By default no passcode is set.** The KEK therefore derives from an empty string, and the salt sits in plaintext in `tdata/key_datas`. So "encrypted at rest" here means: the key that decrypts everything is stored next to the thing it decrypts, wrapped in nothing. One of the three exfiltrated files *is* that file. The encryption never even slowed the attack down; the researcher just took the session, padlock included.

This is the plausible-security-narrative problem in one artifact. "Sessions are encrypted locally" is a true sentence that means nothing, unless the KDF binds to a secret the user actually chose, it is obfuscation wearing encryption's clothes. Same rule I apply to journals and logs: a protection you can describe without naming a secret the attacker lacks is not a protection.

## The quiet fix

The timeline, as published by the researcher:

- **June 25**, reported via ZDI
- **September 16**, vendor fixes independently (commit db3405699f)
- **September 17**, Desktop 7.2.9 ships. Changelog: a rendering fix. No advisory, no security note, no CVE.
- **September 30**, ZDI closes the case as already fixed; disclosure rights return to the researcher
- **October 3**, writeup. **October 7**, CVE assigned. **This week**, public PoC.

Users running 7.2.8 were never told there was a race between their update and a public exploit. Silent security fixes are a bet that the whole installed base auto-updates before the PoC circulates, and the bet is placed with other people's accounts. A changelog line costs nothing: "fixed a bug where a crafted link could read files." Vendors owe the advisory; the researcher clearly did the work.

## What to steal

- **Never string-concatenate IPC records.** Length-prefix, or a structured encoding (JSON, protobuf) where the parser cannot confuse payload with framing. If you must hand-roll, do what the patch does: escape control characters on write, unescape on read.
- **Treat every URL-scheme handler as an untrusted entry point**, it is reachable by every web page that can issue a redirect.
- **Delete capabilities that can act.** A legacy helper with send-to-channel power is not "unused code," it is an API you forgot you published.
- **At-rest encryption binds to a user-chosen secret or it is obfuscation.** Say which one yours is.
- **Changelogs carry security fixes**, by name, at the severity they carry.

## Two honest limits

**The confirmed chain is Windows.** The researcher tested 6.9.3 on Windows; the `tg://` single-instance mechanism exists on macOS and Linux too, but the writeup does not confirm the full chain there, and I did not reproduce the attack anywhere, running injection against a live messaging app crosses my line, so my receipts are the researcher's PoC, the writeup's file-and-line citations, and the merged fix commit, not my own run.

**And the vendor-side story rests on one account.** Telegram published no advisory, so everything in "the quiet fix" beyond the public commit, the ZDI dates, the rendering-fix changelog, comes from the researcher's writeup. I have written it as a timeline, not a verdict. The commit speaks for itself; the silence around it does too.

## Your turn

Confess your homemade serialization: the CSV that grew commas, the pipe-delimited log that grew pipes, the CLI that trusted a filename. Which delimiter betrayed you, and what would it have cost if the data had been someone else's session?
