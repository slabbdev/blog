---
titre: "The internet-dependent mattress has a recovery mode: rooting the Eight Sleep Pod 3 with a GNU tar quirk"
date: 2026-11-16
themes: securite, iot
resume: "Hold a button, plug in power, and the Pod 3 boots from SD and reflashes itself with GNU tar. Since tar keeps the later copy when an archive contains the same path twice, appending three files to the factory rootfs grants permanent root, kills the update services, and frees the mattress from its cloud. The writeup, the 30-second tar demo, and why recovery partitions are the new front door."
source: https://dev.to/slabb/the-internet-dependent-mattress-has-a-recovery-mode-rooting-the-eight-sleep-pod-3-with-a-gnu-tar-3hi4
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fsitx8drlp4009gej4m6u.png
image_alt: "The internet-dependent mattress has a recovery mode: rooting the Eight Sleep Pod 3 with a GNU tar quirk"
---

> The Eight Sleep Pod 3 is a mattress cover with water pumps, a Yocto Linux board (NXP i.MX8M Mini on a Variscite DART module), and a business model: it wants a subscription, and last year's AWS outage left owners unable to adjust their own beds. This week's [rooting writeup by Ryan Bagley](https://rb.ax/blog/rooting-the-eight-sleep-pod-3/) closes that story with my favorite exploit primitive of the month: **GNU tar's duplicate-entry rule**. The factory recovery flow unpacks `rootfs.tar.gz` onto the device's eMMC with plain `tar`, and "when an archive contains the same path twice, GNU tar keeps the later copy". Append three small files to the archive, and whatever is in them becomes the system. No UART, no glitching, no exploit chain: the device's own repair mode respects tar semantics more than it respects its owner.

## The chain, in four moves

1. **Open the case** (several plastic clips die), pull the SD card. Under a daughter board sits the slot the manual never mentions.
2. **Back up the card, patch the archive.** On macOS, `dd` the card, then work inside the image with `debugfs` from e2fsprogs (no mounting needed). The payload is three changes appended to `rootfs.tar.gz`: a new SSH key in `etc/ssh/authorized_keys`, a sudoers file (`rewt ALL=(ALL) NOPASSWD: ALL`), and four symlinks to `/dev/null` for the update-related systemd units, including `swupdate` and a unit genuinely named **`defibrillator.service`**.
3. **The tar trick.** Because the recovery flow extracts with GNU tar, the appended duplicates override the originals without touching anything else in the factory archive. No repack of gigabytes, no checksum surgery: three files, appended.
4. **Factory-reset via the boot button**, and the recovery flow does the rest: it writes your patched rootfs to eMMC and reboots into it. `ssh -p 8822 rewt@POD_IP`, `sudo -i`, done. The author then installed the open-source **free-sleep** stack: a local web UI on port 3000, pump commands engaging **in under a second** (versus sluggish cloud round-trips), and a bed that keeps working when the internet does not.

Full commands are inline in the post; the method builds on the free-sleep project and Bo Lopker's earlier ZeroSleep work. The author's risk framing is honest: with update services nullified, "if something goes wrong, you're on your own", a trade he prefers to a mattress with an uptime dependency on someone else's cloud.

## The 30-second lab: tar as a rooting primitive

This is the part anyone can run tonight, no hardware required, and I ran it for this post. Duplicate paths, same archive, later copy wins:

```bash
mkdir -p a/etc c/etc out
echo "original: cloud-locked" > a/etc/config
echo "patched: ssh key + sudoers + /dev/null units" > c/etc/config

tar cf rootfs.tar -C a etc      # the factory archive
tar rf rootfs.tar -C c etc      # append the SAME path

tar tvf rootfs.tar              # the path is literally in there twice:
# -rw-r--r-- 23 ... etc/config
# -rw-r--r-- 45 ... etc/config

tar xf rootfs.tar -C out && cat out/etc/config
# patched: ssh key + sudoers + /dev/null units
```

My run's output, unedited: the listing shows both entries (23 bytes, then 45 bytes), and the extraction writes the 45-byte later copy. That is the entire primitive: **any build pipeline that extracts a tarball as a privileged operation, without verifying that the archive is duplicate-free, has a root-file-write primitive in its recovery path**. The fix is one flag away (`--occurrence=1`, or an explicit duplicate check, or signing the archive and verifying before extraction), and the fact that it still works on shipping consumer hardware in 2026 tells you how rare that check is.

## Why this keeps being our beat

Regulars will recognize the pattern by now; this quarter has been a tour of it:

- The **supermarket fridges** fell through public web interfaces with date-based passwords: the remote management plane nobody secured.
- The **Lenovo "encrypted" USB** was theater: no crypto, just a fingerprint-shaped lock.
- The **embroidery machine** story was the same ownership fight with a subscription bolted on, and the community answered with an open app.
- The Eight Sleep is the two threads braided: **a recovery mechanism that is an unauthenticated flashing interface**, and **a cloud dependency that turns ownership into a lease**. The recovery boot that trusts any SD card you insert is the physical-world twin of "the message listener that accepts messages from strangers" or "the parser that runs before validation": trusted input surface, unauthenticated, shipped by default.

And the tar angle generalizes further than mattresses: recovery partitions, vendor update images, container layer tars, backup restores. Anywhere a privileged process extracts an archive it did not build, the duplicate-entry rule is a write-anywhere primitive, silent, checksum-preserving per-file, and invisible to any tool that lists the archive without flagging repeats. If you ship such a pipeline, the audit is one command: `tar tvf image.tar | awk '{print $NF}' | sort | uniq -d` should print nothing.

## What to do with this one

- **Pod owners**: the writeup is complete and conservative (backups, checksums, `debugfs` instead of mounts), but you are nullifying your update path; read the author's caveats and know that a future firmware may change the recovery flow. The free-sleep route buys speed, locality, and outage-immunity at the price of being your own vendor.
- **Device builders**: sign your recovery images, verify before extraction, reject duplicate entries, and make the recovery boot require a physical presence proof stronger than "a button that is also the factory-reset button". The Pod's flow did the opposite of each.
- **Everyone else**: run the duplicate check above on every tarball your infrastructure extracts with privileges. It is the cheapest supply-chain audit you will do this week, and this month's mattress is next quarter's router, NAS, or EV charger.

**TL;DR**: the Eight Sleep Pod 3's recovery mode boots from SD and reflashes eMMC with GNU tar; appending duplicate paths to the factory rootfs (later copy wins) plants SSH keys, passwordless sudo, and dead update services, permanently, with no hardware attack. The author now runs the open free-sleep stack locally with sub-second pump control and no cloud. The 30-second tar demo above proves the primitive on any laptop, and the one-line `uniq -d` check belongs in every pipeline that extracts archives with privileges. Ownership of a device you paid for should not be a rooting exercise, but until vendors agree, the recovery partition is the front door.

Sources: [Ryan Bagley: Rooting the Eight Sleep Pod 3](https://rb.ax/blog/rooting-the-eight-sleep-pod-3/) (full method, inline commands) · [throwaway31265/free-sleep](https://github.com/throwaway31265/free-sleep) (the local-control stack) · GNU tar manual, duplicate-entry behavior · tar demo and duplicate-check outputs reproduced live for this post