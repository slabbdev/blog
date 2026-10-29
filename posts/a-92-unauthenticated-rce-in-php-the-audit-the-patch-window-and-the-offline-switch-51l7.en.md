---
titre: "A 9.2 unauthenticated RCE in PHP: the audit, the patch window, and the offline switch"
date: 2026-10-21
themes: securite, webdev
resume: "CERT-EU says sites that can't patch should go offline: two 9.2 flaws in PHP itself, unauthenticated RCE, every version since PHP 5 possibly affected. The audit, the watch, and the offline switch, runnable receipts for the emergency window."
source: https://dev.to/slabb/a-92-unauthenticated-rce-in-php-the-audit-the-patch-window-and-the-offline-switch-51l7
image: https://media2.dev.to/dynamic/image/width=1200,height=627,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Flziflf5ypu667kn7nbey.png
image_alt: "A 9.2 unauthenticated RCE in PHP: the audit, the patch window, and the offline switch"
image_alt: "A 9.2 unauthenticated RCE in PHP: the audit, the patch window, and the offline switch"
---

> An EU cyber agency is telling websites they may need to be taken **offline**. Not patched later. Not monitored. Offline. The runtime that powers WordPress, Drupal, Joomla, Magento and most of the shared hosting internet has two 9.2-rated flaws, unauthenticated remote code execution, and the patch lands today at 14:00 GMT.

On Wednesday, the PHP security team releases fixes for **two critical vulnerabilities rated 9.2 on the CVSS v4.0 scale**. [Reuters reports](https://www.reuters.com/world/asia-pacific/eu-agency-warns-websites-may-need-be-taken-offline-php-prepares-patches-2026-10-21/) what the agencies and vendors are saying around it, and the short version is that this is as serious as web emergencies get:

- **CERT-EU**: the 9.2 rating indicates a risk of **unauthenticated remote code execution**, code running on your server without login. Their guidance: prepare for immediate patching, and **those unable to patch should take affected sites offline**.
- **ACSC** (Australian Cyber Security Centre): identify every PHP system in your environment, prepare to patch, monitor for exploitation. Currently *not aware of active exploitation*, currently.
- **GoDaddy**: the flaws could allow code execution over the internet, data theft, defacement, full system compromise.
- **Huntress**: "PHP is everywhere. It quietly powers WordPress, Drupal, Joomla, and Magento sites, shared hosting platforms, control panels, and an awful lot of software that doesn't even advertise that it runs PHP under the hood."
- **Scope**: all PHP versions from **PHP 5 onward** could be affected. Details, affected versions and fixed releases publish **when the patch drops at 14:00 GMT today**.

If that sounds dramatic for a language release, it is, and it should be. This is not a plugin bug or a framework edge case. It is the runtime itself.

## Why this breaks the grading system

I grade controls on this blog in levels: what a control sees, who wrote it, what it survives. A Level 1 control is visible and bypassable; the quiz-hook post was one. The level below that is the ground the levels stand on: **the runtime**. Your WAF rules, your input validation, your hardening checklist, every one of them is PHP executing your defense. An unauthenticated RCE in PHP is an attack on the level that decides what "executing" means.

Monday I wrote about [Rust's memory-safety proof](https://dev.to/slabb/the-11-year-old-premise-inside-rusts-memory-safety-proof-4804), an 11-year-old hole exposing the premise the proof rests on. Here is the mirror image: the most-deployed server language on the web, whose security model predates the modern threat model entirely, calling an emergency patch window while an EU agency briefs the offline switch. Two runtimes, two philosophies, same week, and both stories are the same story: **the premise is part of the proof.**

## Run it yourself: the audit, the watch, the switch

The details of the vulnerability are withheld until the patch lands, so the receipts that matter right now are the ones on *your* side. Three pipelines:

**1. The inventory, find every PHP on the machines you control:**

```sh
# what's installed (Debian/Ubuntu and RHEL families)
dpkg -l | grep -E "php[0-9.]*-" | awk '{print $2, $3}'
rpm -qa | grep -E "^php" | sort

# what actually executes, and since when
php -v 2>/dev/null; php-fpm -v 2>/dev/null

# every PHP binary on disk, including the ones a panel installed years ago
sudo find / -name "php*" -type f -perm -111 2>/dev/null | grep -vE "/proc|/sys" | head -20
```

That last command is the one that finds the forgotten PHP 5.6 sitting in a panel directory that nobody has touched since 2019, the exact asset CERT-EU's advisory exists for.

**2. The exposure, what faces the internet right now:**

```sh
# php-fpm sockets and pools
ss -tlnp | grep -E "php|9000"
# every vhost routing to PHP
grep -rE "php|fastcgi" /etc/nginx/sites-enabled/ /etc/apache2/sites-enabled/ 2>/dev/null | wc -l
```

**3. The watch, until the patch lands, the exploit probes are your tripwire.** You don't know the signature yet, so watch the volume and the weirdness:

```sh
# requests hitting PHP endpoints, last hour, with response codes
awk -v d="$(date -d '1 hour ago' '+%d/%b/%Y:%H:%M')" '$0 ~ d' /var/log/nginx/access.log \
  | grep -E "\.php" | awk '{print $1, $9}' | sort | uniq -c | sort -rn | head
```

Spikes of POSTs to `.php` paths on sites that have no PHP forms, or 200s from paths that should 404, that is your "currently not aware of active exploitation" turning into "aware."

**4. The switch, when the patch drops at 14:00 GMT:**

```sh
sudo apt update && sudo apt install --only-upgrade "php*"
sudo systemctl restart php8.3-fpm   # your version
php -v                                # confirm the new release
```

And the offline switch CERT-EU is briefing, for assets you cannot patch in the window:

```sh
sudo systemctl stop php8.3-fpm
# serve a static maintenance page with no PHP in the path:
# nginx: return 503 with a maintenance root; the runtime is out of the request path entirely.
```

Stopping `php-fpm` removes the runtime from the request path, no PHP executing, no PHP vulnerability executing. It is the crudest control in this post and the only one CERT-EU explicitly endorsed for the unpatchable.

## What you actually get

- **A deadline**: 14:00 GMT today. The details land with the patch; the audit above is everything you can do *before* reading them.
- **A decision tree**: can patch in the window → patch and verify the version. Can't patch → the offline switch, or take the asset off the internet edge. Don't know if you're exposed → the inventory commands exist for exactly that.
- **The honest limits**: nothing in this post tells you whether you're vulnerable to *these specific* flaws, PHP publishes that when the patch lands. What the audit tells you is where every PHP lives, which is the prerequisite for patching in minutes instead of days.

And the premise note, because it's the same week: memory safety in the runtime is not an academic property. Eleven years of a proof on one side, an EU offline advisory on the other. The language your server runs *is* your attack surface's foundation, everything above it is scaffolding.

The patch drops at 14:00 GMT. The audit takes ten minutes. Do the audit first.

---

*Sources: [Reuters, EU agency warns websites may need to be taken offline as PHP prepares patches](https://www.reuters.com/world/asia-pacific/eu-agency-warns-websites-may-need-be-taken-offline-php-prepares-patches-2026-10-21/) (Oct 21, 2026, quoting CERT-EU, ACSC, GoDaddy, Huntress, PHP security team). The runtime-as-premise framing follows [my Rust memory-safety post](https://dev.to/slabb/the-11-year-old-premise-inside-rusts-memory-safety-proof-4804). Watch this post's dev.to comments, I'll update with the CVE details and fixed versions after the 14:00 GMT release.*
