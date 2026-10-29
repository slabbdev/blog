---
titre: "Six unpatched Linux kernel vulnerabilities just leaked to a public mailing list"
date: 2026-10-22
themes: securite, linux
resume: "Overnight, six ZDI vulnerability reports, including two CVSS 9.0 network RCEs in the kernel's SMB server, unpatched in mainline, landed on the public LKML instead of the private security list. Greg Kroah-Hartman's reply: \"For some reason you sent this to public lists, and did not include a patch.\" The lab: is your fleet exposed?"
source: https://lore.kernel.org/lkml/BYAPR01MB3830472B5702C089B0BBB77D80662@BYAPR01MB3830.prod.exchangelabs.com/
image: https://blog.slabb.dev/img/six-unpatched-linux-kernel-leak.png
image_alt: "Six ZDI reports, two CVSS 9.0 KSMBD RCEs, leaked to the public LKML: the inbox view, Tux, and the port 445 triage"
---

> Last night, the coordinated-disclosure machine for the Linux kernel broke in the most mundane way possible: **Trend Micro's Zero Day Initiative emailed six vulnerability reports to the public LKML**, the archive-readable, world-readable list, instead of the private channel they were meant for. Two of them are **CVSS 9.0 network RCEs** in the kernel's own SMB server, **unpatched in mainline**. Greg Kroah-Hartman, the kernel's second-in-command, replied to each one: *"For some reason you sent this to public lists, and **did not include a patch**, so there's not much we can do with this."*

This is not a kernel vulnerability story. It is a **disclosure-pipeline story**, and it happens to be the second one this week. Here's what leaked, why the window is open right now, and a two-minute triage for your own fleet.

## What is now public

Six reports from `zdi-disclosures@trendmicro.com`, posted overnight (Oct 21, 21:16 UTC onward), sitting in the lore.kernel.org archive for anyone to read:

| ZDI ref | Bug | Class | Severity |
|---|---|---|---|
| ZDI-CAN-33549 | KSMBD SMB Direct | **Remote code execution** (network) | **9.0** |
| ZDI-CAN-33774 | KSMBD race condition | **Remote code execution** | **9.0** |
| ZDI-CAN-33367 | skbuff `skb_zerocopy` | local privilege escalation | high |
| ZDI-CAN-34068 | vmwgfx dirty tracking | out-of-bounds write → LPE | high |
| ZDI-CAN-34076 | NVMET | uninitialized resource → info disclosure | medium |
| ZDI-CAN-32005 | search-domain TCP query | stack buffer overflow → LPE | high (posted a day earlier) |

The centerpiece, [ZDI-CAN-33549](https://lore.kernel.org/lkml/BYAPR01MB3830472B5702C089B0BBB77D80662@BYAPR01MB3830.prod.exchangelabs.com/), is a beauty, and it reads like a guided tour. The target is the kernel's SMB server (KSMBD) over SMB Direct; the bug is a two-line integer underflow:

```c
desc_buf += desc_buf_len;
buf_len -= desc_buf_len;   // (2) integer underflow, leads to heap overflow
                           //     within rxe_mr_copy()
```

Below it: the exact KASAN output (`slab-out-of-bounds in rxe_mr_copy_dma`, write of 1024 bytes), the tested version (7.3-rc3), the platform (Debian trixie), and the config keys to make it reachable (`CONFIG_SMB_SERVER_SMBDIRECT=y` + `CONFIG_RDMA_RXE=y`, note that `rdma_rxe` is *software* RDMA: no exotic hardware needed). Requirements per the report: an RDMA device, a writable share, SMB Direct enabled.

Every ingredient a third party needs to start from the analysis instead of the bug class. The patch, per Phoronix, was sitting in a branch intended for **v7.5**, now likely to be expedited.

## Why the window is open *right now*

The math of a leaked unpatched report:

1. **Today**, anyone can read the full analysis, vulnerable function, crash trace, target config. The fix isn't in a stable release.
2. **When the patch lands** in linux-next (it's being expedited), the commit diff becomes the exploit's field guide: one `git log` and the entire fuzzing surface collapses to the exact lines that changed.
3. **Until a stable release ships**, fleets run a kernel whose known-hole blueprints are public.

KSMBD makes this worse than a random driver: it's the **in-kernel SMB server**, listening on 445, a subsystem that already spent 2022–2023 on the security naughty list with its own run of RCEs and public debates about whether it belonged in mainline. Internet-exposed 445 + a public 9.0 RCE blueprint is the kind of combination ops teams do not get to ignore.

And Greg KH's reply names the second failure: **the reports carried no patch**. The maintainers got nothing actionable; the attackers got everything. That's the worst of both sides of a disclosure.

## Triage your fleet in two minutes

The reports name their own configs. Check yours:

```bash
# Is the in-kernel SMB server even loaded?
lsmod | grep ksmbd

# Is anything listening on SMB (445)?
ss -tlnp | grep ':445 '

# Was SMB Direct compiled in, and is software-RDMA (the rxe in the bug) active?
grep -E 'SMBDIRECT|INFINIBAND_USER' /boot/config-$(uname -r) 2>/dev/null
lsmod | grep rxe

# VMware guest? The vmwgfx report is about your graphics driver.
systemd-detect-virt
```

If `ksmbd` isn't loaded and nothing listens on 445, the RCE reports are somebody else's fire today, but the skbuff LPE (local, via the networking core) affects nearly everyone, so the real to-do is the one the kernel always asks for: **be current on your stable point releases this week**, because the expedited fixes will ride the next one. Watching [the lore thread](https://lore.kernel.org/lkml/BYAPR01MB3830472B5702C089B0BBB77D80662@BYAPR01MB3830.prod.exchangelabs.com/) is the cheapest early warning you'll get.

(Small internet joke along the way: lore.kernel.org sits behind **Anubis**, the proof-of-work gate built to keep AI scrapers out. The kernel's anti-bot wall now fronts zero-day reports, you'll need a real browser to read the leaks.)

## The part that matters by Friday

This week handed us the A/B test of disclosure discipline, in the same seven days:

- **eMudhra** (Monday): a CA key compromise reported through the *right private channel*, with cryptographic proof, fixed and blocked across every root program in three days. Textbook.
- **ZDI** (last night): six unpatched reports on the *public* archive, no patches attached, one misdirected email campaign from an Exchange Online sender, `exchangelabs.com`, and the kernel's number two saying, in public, *there's not much we can do with this*.

Same industry, same week, same class of asset. The variable was never the vulnerability quality; it's the **pipeline**, the addressing, the patch attachment, the process that moves a report from private to public *after* the fix exists. A disclosure channel is security infrastructure, and last night it failed the way infrastructure fails: one routing table nobody reviewed, one attachment nobody attached.

We keep arriving at the same conclusion from different angles, the watcher's own plumbing is the attack surface. This time it wasn't an agent rewriting its logs; it was a mail client with the wrong To: line.

## TL;DR

Six ZDI reports, including two CVSS 9.0 KSMBD RCEs, leaked to the public LKML overnight, unpatched, analysis-complete, archived forever. Greg KH's answer is the whole story: no patch attached, nothing to do. Triage your 445 exposure today, be current on stable kernels this week, and watch the fix commits land, because the moment they do, the diff tells everyone exactly where the holes were.

Sources: [ZDI-CAN-33549 on lore.kernel.org](https://lore.kernel.org/lkml/BYAPR01MB3830472B5702C089B0BBB77D80662@BYAPR01MB3830.prod.exchangelabs.com/) · [Greg KH's reply](https://lore.kernel.org/dri-devel/2026102254-protector-seventy-6454@gregkh/) · [Phoronix: LKML New Trend Vulnerabilities](https://www.phoronix.com/news/LKML-New-Trend-Vulnerabilities)
