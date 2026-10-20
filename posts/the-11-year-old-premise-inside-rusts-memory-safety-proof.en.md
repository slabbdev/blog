---
titre: "The 11-year-old premise inside Rust's memory-safety proof"
date: 2026-10-14
themes: dev
resume: "\"If it compiles, the memory is safe\" — a machine-checked proof, Level 2 enforced by the compiler itself. Yesterday an 11-year-old hole appeared in it, and the team's severity call exposed the premise the proof rests on: Drop impls are honest. Verified live on stable and nightly."
source: https://dev.to/slabb/the-11-year-old-premise-inside-rusts-memory-safety-proof-4804
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fcf1av1q8d2ylt8ra4pc9.png
image_alt: "The 11-year-old premise inside Rust's memory-safety proof"
---

"If it compiles, the memory is safe."

That is Rust's brand — not a slogan, a machine-checked proof: the borrow checker refuses unsafe lifetimes at compile time, host-enforced, the strongest rung any language has claimed. Yesterday, [issue #164250](https://github.com/rust-lang/rust/issues/164250) landed on the rust-lang tracker: an unsoundness in the borrow checker, reproducing on current stable, with variants compiling since **1.18.0 (2017)** — and one version traced back to **1.4**. Eleven years inside the proof.

I ran the reproduction tonight on the official playground — stable channel. The output, verbatim:

```text
read after scope: hello world, this is long enough
the stack slot is freed. the string still printed.
```

A short-lived reference escaped a `T: 'static` bound through field assignment after construction, survived a `Drop` that assumed the bound held, and was read after its stack slot was freed. On stable. Same result on nightly. The receipts are one click away — [the ASAN run in the issue](https://rust.godbolt.org/z/83MvfbKde) shows it in seconds.

## The mechanics, in three sentences

`struct Q<T: 'static + Send>` demands its payload outlive the program. Assigning a field *after* construction (`q.0 = Some(&l)`, where `l` is stack-local) unifies the types covariantly — and that unification does **not** re-check the `'static` bound. A `Drop` impl that pushes the value into a static list assumes the bound held; it leaks the reference out; a `downcast_ref::<&'static String>()` reads freed stack memory. With AddressSanitizer, [per the issue](https://github.com/rust-lang/rust/issues/164250), the same program crashes with `stack-use-after-scope`.

## The number that matters is not 11

It is the severity call: **P-high, downgraded from P-critical.** The pinned note from lcnr is explicit — it would have been P-critical regardless of whether anyone encountered it in the wild, and it is P-high only because it has been latent for eleven years with "very likely that this unsoundness has not caused memory unsafety by accident." The exploit requires, per the issue, "an intentionally malicious Drop implementation."

Read that as an auditor, because it is a premise confession, and it is not Rust-specific. The compiler's proof descends a ladder: borrow check → variance rules → trait bounds → and at the floor, an assumption nobody executes — **`Drop` implementations respect the bounds they inherit.** The type system verified everything it could check and rested on the one thing it could not: the honesty of every `Drop` impl ever written by every hand that touched every crate. Eleven years, that premise held by accident of nobody aiming at it. This week someone aimed.

Sound familiar? It is [the QGIS conscience test](https://github.com/qgis/QGIS-Enhancement-Proposals/pull/387) — "did you in good conscience write the code yourself" — inside a compiler. It is [the authority ladder](https://dev.to/slabb/the-authority-ladder-five-rungs-down-four-premises-standing-4p5f) — rung 0, "the caller's argument": a claim the impl author makes, unverifiable by the checker below. Every soundness proof, every security certification, every "guaranteed" has a floor like this. The floor is not a scandal. **An unlabeled floor is.**

![diagram](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/pxd3nop2fpft574w3zbs.png)

## Credits, because the finder's method is the receipts

- **jsnell** filed it October 13, with the reproduction that compiles and prints freed memory.
- **theemathas** added the I-unsound label, a minimal core repro, and traced a variant compiling "ever since 1.18.0 (2017)" — and asked the question in the thread: "How on earth was this not found before this???"
- **maxdexh** contributed a version going back to **1.4**, and the generalization: "unification just generally doesn't check lifetime bounds of the type" — including via `mem::swap`, no field assignment needed.
- **lcnr** pinned the severity reasoning and the linkage to the next-gen trait solver and Project Zero rework. PR [#164277](https://github.com/rust-lang/rust/pull/164277) is the fix in motion.

Four people, four contributions, each with its own denominator. That is what a healthy process looks like from the outside — and it is also, per the issue, a thread that was briefly **locked as too heated** before being unlocked and re-locked to collaborators. Soundness conversations run hot.

## What to steal

- **Audit the premises under your proofs.** Every guarantee you rely on — a type system, a SOC 2 report, a DCO sign-off, a "tested and measured" claim — rests on unlabeled assumptions the guarantee cannot check. Name one. The table is the audit.
- **Label your severity calls with their reasons.** P-high *because* eleven years latent *because* it needs a malicious Drop — that reasoning is the difference between a decision and an assertion. Rust's team did this in the pinned note; copy the format.
- **Permalinks for reproductions.** The playground link makes my claim one click from being your claim. If your repro needs setup, ship the setup.

## Two honest limits

**The exploit requires a malicious `Drop` by design, and the team's downgrade is defensible.** Eleven years without an accidental hit is evidence of something — either the premise held because nobody aimed, or because honest Drops overwhelmingly dominate. Both readings favor the team's call. My point is narrower: the premise existed, was unlabeled, and now is labeled — by the issue, in public.

**And my run is a playground snapshot, not a forensic audit.** Stable and nightly, debug profile, no AddressSanitizer in my harness — the `stack-use-after-scope` confirmation cited in the issue comes from their ASAN run, not mine. One compiler family, one evening. The issue's own denominators are better than mine; use theirs.

## Your turn

The reproduction is twenty lines, the playground is free, and here is the whole thing — paste it into [a fresh playground](https://play.rust-lang.org/?version=stable&mode=debug&edition=2021), hit Run, and compare your output to mine:

```rust
static KEPT: std::sync::Mutex<Vec<Box<dyn std::any::Any + Send>>> =
    std::sync::Mutex::new(Vec::new());

struct Q<T: 'static + Send>(Option<T>);

impl<T: 'static + Send> Drop for Q<T> {
    fn drop(&mut self) {
        if let Some(v) = self.0.take() {
            KEPT.lock().unwrap().push(Box::new(v));
        }
    }
}

fn main() {
    let l = String::from("hello world, this is long enough");
    {
        let mut q = Q(None);
        q.0 = Some(&l);
    } // <- Drop here: the short-lived reference escapes as if 'static

    let kept = KEPT.lock().unwrap();
    let s = kept[0].downcast_ref::<&'static String>().unwrap();
    println!("read after scope: {}", s);
    println!("the stack slot is freed. the string still printed.");
}
```

Run it on your rustc, your channels, your edition, and post your output — the issue's variants reach back to 1.4, and every data point sharpens the map. Then pick one guarantee you ship or rely on, and write down the premise under it that nobody executes. That list is where the next eleven-year bugs live.
