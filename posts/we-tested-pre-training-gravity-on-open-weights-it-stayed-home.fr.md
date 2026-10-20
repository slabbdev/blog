---
titre: "On a testé la gravité du pré-entraînement sur des poids ouverts. Elle est restée au sol."
date: 2026-10-11
themes: ia
resume: "Le pré-entraînement rend-il les modèles sûrs par défaut ? Testé sur poids ouverts : non."
source: https://dev.to/slabb/we-tested-pre-training-gravity-on-open-weights-it-stayed-home-243i
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fnnzyu2hfbxdoxf0blpyk.png
image_alt: "On a testé la gravité du pré-entraînement sur des poids ouverts. Elle est restée au sol."
---


> 🇬🇧 **Cet article n'est pas encore traduit** — la version originale en anglais suit. La traduction arrive.

Tuesday, in the thread under Part 3.8, I pre-registered an experiment in public: Randal's gate-attack catalog replayed against a reconciliation layer as the witness, on open weights — to separate "works because it's Unix" from "works because it's frontier". [The pre-registration is the comment in that thread](https://dev.to/slabb/comment/3hb36); [Humam Moin's question](https://dev.to/humam_moin/comment/3hb4n) is what suggested it. Yesterday the run completed, the results are committed, and this post is the read. Receipts first, adjectives after.

## The rig

One orchestrator race, replayed per model. The judge is asked to produce a review of a diff; the planted canary is a specific numbered section heading — "4. Blast Radius" — that no honest pass should invent. **Condition A** hands the model prose only: the system prompt can come from priors and nothing else. **Condition B** loads the canonical source into context first — the `waitpid()` discipline: read the sealed spec before you rule. The grader is not my opinion: it is NoireBox's shipped witness layer — `seal_spec` + `reconcile_spec` — the same instrument the product runs. A produced prompt without the planted canary is the `spec_not_canonical` trip. The instrument is the product; the benchmark cannot drift from the tool.

## The table — as committed

[The measured table lives in the repo](https://github.com/noirebox/noirebox/blob/main/docs/SCAR-BENCH.md) and the post cites it rather than restating it from memory. Three local open-weights models, per-trial seeds, denominators in every cell:

| Model | A prose: trips/n | B primitive: trips/n | strict canonical |
|---|---|---|---|
| qwen2.5-coder:3b | 18/18 (100%) | 15/20 (75%) | 0 |
| qwen2.5:0.5b | 19/19 (100%) | 15/19 (79%) | 0 |
| llama-guard3:1b (classifier — cannot play the role at all) | 20/20 (100%) | 20/20 (100%) | 0 |

## The read

**Condition A is a ceiling, and the prediction's first half holds hard.** Not one model ever guessed "4. Blast Radius" from priors — 100% trips across the board. On the frontier, Randal's matrix shows models hallucinating canonical Unix structure *without it in context* — that pull is the gravity. On these open weights, the pull is absent: there is no floor of learned convention to stand on, so the canary cannot even be wrong in the interesting way.

**Condition B is where it gets more interesting than predicted.** With the canonical bytecode loaded first, trips drop to 75–79% — Level 1 (a high-mass primitive in context) *reduces* the hallucination but does not fix it. One model in five still paraphrases past the very source it was given. That is the measured argument for Level 2: the host must load the spec from the sealed store and grade the receipt against what was actually loaded — never trust the model's retelling of what it read.

**Strict canonical is 0 everywhere — and that is why the receipt carries `spec_hash`.** No model, in any condition, ever reproduced the exact bytes. Even the outputs the witness accepted as canonical were loose. If your audit binds to what the model *claims* it read, you are binding to a paraphrase. Bind to the hash of what was loaded.

**And llama-guard3:1b is the instrument checking itself.** It is a safety classifier, not a code judge — it cannot play the role at all, and it trips 20/20 in both conditions. A witness that let a classifier pass as a reviewer would be a witness worth nothing. This one caught total role non-compliance on every trial.

![barres A/B par modèle : A au plafond 100 % partout, B à 75-79 %, strict canonical à 0](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/sc997c04emd1m1xdhz8y.png)

## The stranger part

Here is the line the numbers wrote that nobody predicted. On the frontier, the question was "does the primitive in context pull the output toward canonical?" — and gravity said yes, hard (61.4% → 96.2% on Randal's matrix). On open weights, the question dissolves: **the models never even reach the suite where the frontier models played.** They do not produce a worse outline, or a partial one — they produce something else entirely, and the canary sees it anyway. "Trips harder" was the prediction; "trips at ceiling, everywhere, in both conditions" is the data. Gravity did not get weaker at the open end of the distribution. It was never there to begin with — and the pre-registered instrument could tell the difference, because it grades bytes, not vibes.

## Credits

- **[Randal L. Schwartz](https://dev.to/randalschwartz)** — the prediction, the canary corpus, SCAR-114 itself, and the SCAR-BENCH claims format this post obeys (Part 3.8).
- **[howcani](https://dev.to/howcani)** — the audit thread that closed the seam at the schema (receipt v0.2.2) and pushed `judged_by` to required (v0.2.3). The witness layer grading these trials is that receipt schema.
- **[Humam Moin](https://dev.to/humam_moin)** — the open-weights question that triggered the run.

## Disclosures, verbatim

Single machine, local Ollama, temperature 0.7, per-trial seeds (42+i, recorded per trial), prompts in `bench/scar114_canary.py`, 4 timeouts excluded with denominators shown. **The frontier leg is open** — same harness, one API key.

## Reproduce

```bash
git clone https://github.com/noirebox/noirebox && cd noirebox
make scar-bench          # the run, the witness, the table
```

The results file carries every trial with its seed. The witness is the shipped product, not a harness built for the benchmark — grade us with the same code you run.

## Two honest limits

**These are small local models, and the frontier leg is not run.** 0.5B to 3B parameters on one machine is the cheapest open end of the distribution, chosen because it is reproducible by anyone with a laptop and an evening. Whatever gravity the frontier shows, this table does not measure it — same harness, one API key, and the differential completes.

**And llama-guard3 is a witness check, not a failed arm.** 20/20 trips looks like a model failing; it is a classifier succeeding at being a classifier — total role non-compliance, caught. Counting it in the averages would flatter the trip rate; it is in the table because a witness that cannot flag an impossible judge is decoration.

## Your turn

The pre-registration is public, the run is committed, the frontier leg is one API key wide. If you run the harness on a model we did not — open or frontier — bring the table back in the SCAR-BENCH format and it joins the registry. The differential only stays honest if the scores travel.
