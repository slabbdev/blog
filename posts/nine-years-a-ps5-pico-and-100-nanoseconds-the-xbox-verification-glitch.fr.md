---
titre: "Neuf ans, un Pico à 5 £ et 100 nanosecondes, le bug de vérification de la Xbox"
date: 2026-10-15
themes: securite
resume: "L'histoire d'un contrôle déplacé de trois instructions, resté neuf ans dans une console vendue à des millions d'exemplaires."
source: https://dev.to/slabb/nine-years-a-ps5-pico-and-100-nanoseconds-the-xbox-verification-glitch-15oi
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fobc7b4vh868w571pvkph.png
image_alt: "Neuf ans, un Pico à 5 £ et 100 nanosecondes, le bug de vérification de la Xbox"
---


> 🇬🇧 **Cet article n'est pas encore traduit**, la version originale en anglais suit. La traduction arrive.

Somewhere in an Xbox 360, a signature verification runs. One instruction in that process, a `mr`, a register move, decides whether the check passes. Deliver a pulse of energy about **100 nanoseconds** wide at exactly the right moment, and that `mr` moves 0 instead of the value it was carrying. The check compares against 0. The check passes.

That is the Reset Glitch Hack, RGH to everyone who has spent time in that corner of hardware, and [a writeup published this week](https://kennedn.com/blog/posts/glitching/) tells it better than the wiki ever has: the wiring, the timing, the photos, and a nine-year arc that ends with the punchline I can't stop thinking about. **The author finished the hack with a £5 Raspberry Pi Pico, days after a software-only exploit shipped that made the whole hardware path obsolete.**

## The nine years, measured

2017: the author buys a Matrix CoolRunner Rev D, the glitcher chip, and fails. Not at the glitching. At the boring part: building a DIY LPT-port NAND/JTAG programmer, where a single dump takes thirty-plus minutes. The project is shelved with the knowledge intact and the tools unusable.

2026: revisited with a £5 Raspberry Pi Pico. PicoFlasher dumps the NAND in seconds. pico-dirtyJTAG programs the CoolRunner with Octal450's timing files through urjtag. The glitcher that defeated the 2017 setup is programmed in an evening.

Same console. Same chip. Same knowledge. The difference is nine years of tooling getting cheaper, a programmer that cost an evening of frustration replaced by one that costs less than lunch. The 2017 failure was not a knowledge failure. It was a tooling failure, and tooling is the half of the equation that compounds.

There is a bitter coda, and the writeup lands it without cruelty: a software-only exploit, Xbox360PeerPressure, shipped just before the hardware hack was finished. Nine years, and the market made the bespoke path obsolete in a patch cycle. The shelved project was beaten to the finish line by the shelf itself.

## The glitch, as a physics problem

The Xbox 360's boot chain starts in the 1BL, the first-stage bootloader, per the writeup, "physically baked into the silicon." Microsoft's signature verification runs over everything that boots after it. The verification is real cryptography. The weakness is not in the crypto, it is in the assumption underneath it: **the comparison runs on logic an attacker can physically disturb.**

The glitch delivers ~100 nanoseconds of energy to the CPU during the reset window. The CPU executes the verification instruction incorrectly, the `mr` moves 0 instead of the comparison result, and a check built to compare against a signature now compares against zero. Zero passes. The console boots code Microsoft never signed.

The tooling precision involved is the part that deserves respect: the PIO on a Raspberry Pi Pico, clocked at 133 MHz, delivers timing at roughly **7.5 nanoseconds** of granularity. The attack window is measured in single clock ticks of the console, and a £5 microcontroller walks into that window reliably enough to boot homebrew. This is not hammering a lock. This is a stopwatch race against a silicon state machine, won with a clock that costs less than the pizza eaten during the soldering.

## The verification lesson, the physical edition of a software post

Here is why this belongs on a software blog. Every verification you run, a signature check, a license check, a client-side entitlement, a browser-side price, makes the same assumption the Xbox made: **the verification logic runs undisturbed, on hardware the attacker does not control.** The Xbox 360 is the cleanest counterexample in consumer hardware: the crypto was never broken. The *premises under the crypto* were, one instruction, one pulse, one register moved to zero.

This series has been circling that sentence from the software side: [a premise, not a cipher](https://dev.to/slabb/the-authority-ladder-five-rungs-down-four-premises-standing-4p5f), howcani's phrase for the registrar pin whose key file an agent could still read. The Xbox is the physical edition: the signature comparison is a premise, and a 100-nanosecond pulse re-prices it to zero. The lesson generalizes in one line, and it predates all of us: **verification that runs where the adversary stands is a preference, not a proof.** Server-side checks, hardware roots, sealed enclaves, every real control is an answer to the question the glitch asks: *who controls the ground the check stands on?*

## The same glitch, software edition, run it

The hardware version needs a Pico, a CoolRunner, and a soldering iron. The lesson needs none of that: the glitch is a **race**, and races run in software too. Twenty lines of C, a "signature check" reading a register, and a glitcher thread flipping it in a tight loop, hoping to land inside the comparison:

```c
/* glitch.c, a signature check, glitched by a racing thread
   build locally: cc -O2 -pthread glitch.c -o glitch && ./glitch */
#include <pthread.h>
#include <stdio.h>
#include <stdatomic.h>

atomic_int running = 1;
atomic_int reg = 1;   /* the value the mr is supposed to move: nonzero passes */

static void *glitcher(void *arg) {
    /* the pulse, software edition: flip the register in a tight loop */
    while (atomic_load_explicit(&running, memory_order_relaxed)) {
        atomic_store_explicit(&reg, 0, memory_order_relaxed);
        atomic_store_explicit(&reg, 1, memory_order_relaxed);
    }
    return NULL;
}

int main(void) {
    pthread_t t;
    pthread_create(&t, NULL, glitcher, NULL);
    int glitched = 0, rounds = 0;
    while (rounds < 1000000) {
        rounds++;
        int check = atomic_load_explicit(&reg, memory_order_relaxed);
        if (check == 0) {   /* the comparison the glitch defeated */
            printf("GLITCHED: the check passed against zero (round %d)\n", rounds);
            glitched = 1;
            break;
        }
    }
    atomic_store(&running, 0);
    pthread_join(t, NULL);
    if (!glitched) printf("no glitch in 1,000,000 rounds, rerun, the race is timing\n");
    return glitched ? 0 : 1;
}
```

[OnlineGDB](https://www.onlinegdb.com/) runs it with zero install, select C, paste, Run. My runs tonight, three consecutive executions on this laptop, verbatim:

```text
GLITCHED: the check passed against zero (round 29463)
GLITCHED: the check passed against zero (round 24007)
GLITCHED: the check passed against zero (round 139258)
```

Note the variance: 24k, 29k, 139k rounds. That spread **is** the lesson, software glitching wins by volume, hardware glitching wins by precision, and the PIO walking its 7.5-nanosecond steps lands every single boot where the thread needs a hundred thousand tries. Same race, different clocks. The reader who sees GLITCHED print has now personally experienced why a verification check is only as good as the ground it stands on, and why the hardware version is the one that pays the bills.

## Two honest limits

**I did not build this.** The receipts in this post are the writeup's photographs, its timing numbers, and the linked toolchain, PicoFlasher, pico-dirtyJTAG, Octal450's timing files, urjtag, plus the Free60 project's public documentation. My contribution is the anatomy and the audit of the nine-year arc. The soldering belongs to someone else, and that limit applies to every hardware story I will ever write from a desk: the bench is the receipt I cannot fake.

**And the threat model is physical, which changes what the lesson is worth.** The glitch needs hands on the console, open it, wire the chip, own the reset line. Nobody is doing this to your Xbox remotely. Where the lesson transfers is to verification that runs on hardware the *user* controls: license checks, client-side entitlements, DRM, every one of them a signature verification standing on glitchable logic, exactly the ones the industry re-learning cycle keeps repricing. For remote-attack scenarios the premise runs elsewhere, and the ladder keeps its rungs.

## Your turn

The parts list is short: a Pi Pico, a CoolRunner, the console, and the community docs. If you have a 360 in the attic and a weekend, the writeup links everything, and the RGH family tree on the Free60 wiki maps which boards glitch easiest. Or skip the hardware entirely: paste the demo from the section above into [the OnlineGDB C compiler](https://www.onlinegdb.com/online_c_compiler) and hit Run. But the question I want answered in the comments is the other one: **what is in your parts drawer, waiting for the tooling to catch up?** Every hacker has a 2017 shelf, the project abandoned not because it was impossible but because the programmer took thirty minutes per dump. Post yours. The next £5 Pico might be pointed at it.
