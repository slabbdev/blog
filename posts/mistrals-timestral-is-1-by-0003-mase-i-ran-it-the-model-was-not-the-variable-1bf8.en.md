---
titre: "Mistral's Timestral is #1 by 0.003 MASE. I ran it, the model was not the variable."
date: 2026-10-20
themes: ia, preuve
resume: "Mistral released Timestral, four open-weight time-series models that top three benchmarks, by 0.003 MASE on their own table. I ran all three sizes against one-line baselines, on a known generator and on fresh Paris weather. With one summer of context the 209M lost to "repeat yesterday"; with three years it beat everything by a third, and the 20 MB model matched the 837 MB one."
source: https://dev.to/slabb/mistrals-timestral-is-1-by-0003-mase-i-ran-it-the-model-was-not-the-variable-1bf8
image: https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/p6yb6d3fwxmi9074beh4.png
image_alt: "Mistral's Timestral is #1 by 0.003 MASE. I ran it, the model was not the variable."
---

Same model, same fourteen days of Paris weather, same holdout. The only thing I changed between these two rows was how much history I handed it:

```text
Timestral-209M, context = one summer (158 days)   MAE 6.489   80% band covered the truth 43% of the time
Timestral-209M, context = three years (1,096 days) MAE 3.326   80% band covered the truth 64% of the time
"repeat yesterday", no model at all                MAE 5.636
```

With one summer in the window, Mistral's new state-of-the-art forecaster lost to a baseline that repeats the last value. With three Octobers in the window, it beat every baseline by a third. And the smallest model in the family, 20.8 MB on disk, landed within 0.03 of the 837 MB flagship. The variable that mattered was not the parameters. It was the context. Nothing on a leaderboard tells you that; a ninety-line script does, and it is below.

## The release, and the number behind "first"

On October 15, Mistral shipped [Timestral](https://mistral.ai/news/timestral), its first family of time-series foundation models: four open-weight checkpoints at 5M, 28M, 123M, and 209M parameters, zero-shot forecasting with 21 quantiles, up to 32,768 steps of context, PyTorch on CPU or GPU, code on [GitHub](https://github.com/mistralai/timestral) under Apache-2.0. The announcement is specific: it "ranks first on all three of the field's main public benchmarks, GIFT-Eval, TIME, and fev-bench," and, "Among pre-trained, zero-shot models, it ranks first across all five metrics." Also: "These results come from a single checkpoint, without ensembling." The [Hacker News thread](https://news.ycombinator.com/item?id=50150434) hit 601 points.

The margins are on the [model card](https://huggingface.co/mistralai/Timestral-209M), in Mistral's own table. I copied the first-place column and the second-place column and subtracted:

| Benchmark | Metric | Timestral-209M | Runner-up (t0-gamma) | Margin |
|---|---|---|---|---|
| GIFT-Eval | MASE ↓ | 0.658 | 0.661 | **0.003** |
| GIFT-Eval | CRPS ↓ | 0.446 | 0.452 | 0.006 |
| TIME | MASE ↓ | 0.626 | 0.637 | 0.011 |
| TIME | CRPS ↓ | 0.522 | 0.534 | 0.012 |
| fev-bench | SQL skill ↑ | 50.39 | 49.42 | 0.97 |
| fev-bench | MASE skill ↑ | 39.49 | 37.99 | 1.50 |

Every row is a first place, and the announcement is right about every row. The first place on the headline benchmark is three thousandths of a MASE point. One HN commenter put it bluntly, "crazy how they make an improvement of 0.03 look like a 5x difference", and the card's number is smaller than his. Another noted that "the blog post features an imaginary customer rather than an actual reference"; I read the page twice: no customer is named, the case study opens with "Consider an industrial plant with thousands of sensors across its equipment."

None of this makes the model bad. It makes the table worth reading before the bar chart. And one line in the announcement decided what my test should look like: "The majority of the training data was synthetic." The models were pre-trained on generated processes, trends, seasonality, noise, then post-trained on a real-and-synthetic mix. A synthetic series is their home turf.

## The test the thread asked for

Buried in the discussion was a protocol, from a commenter who clearly does this for a living: "To meaningfully test a forecasting model, use a data-generating process with a high signal-to-noise ratio where a classical method (empirical conditional distributions, i.e., counting) can capture most of the signal. Then check whether the model captures that signal too. If you only test on high-noise processes, any model looks" the same. So that is Test A. Test B is the opposite: a real series that did not exist when the models were uploaded, Paris daily maximum temperature from [open-meteo](https://open-meteo.com/), no API key, through yesterday. Test C is Test B with the context window pushed back three years.

Three sizes (5M, 28M, 209M), CPU only, every forecast deterministic, I ran the whole script twice and diffed the outputs: byte-identical. Baselines are one line each: repeat the last value, the mean of the last seven, and for the seasonal series, repeat last week. Metrics: MAE, MASE (MAE scaled by the in-sample naive error, the same family of metric as the leaderboards), and how often the model's 10%–90% band actually contained the truth, which should be about 80% of the time if the uncertainty is honest.

```python
#!/usr/bin/env python3
"""timestral_test.py, three tests a reader can rerun in minutes, no API key.

Test A  a series with a KNOWN generator (trend + weekly pattern + small noise).
        A counting method (seasonal naive) captures most of the signal.
        Does the foundation model capture it too?  (protocol from the HN thread)
Test B  a REAL series nothing could have memorized: Paris daily max temperature,
        open-meteo archive, context May 1 -> Oct 5 2026, holdout Oct 6 -> Oct 19.
Test C  same series, same holdout, same models, three years of context instead
        of one summer. Only the history handed to the model changes.

Run it:
    pip install "git+https://github.com/mistralai/timestral.git"
    python3 timestral_test.py                 # 5M + 28M + 209M, CPU
"""
import json
import sys
import urllib.request

import numpy as np
from timestral import TimestralForecaster

MODELS = sys.argv[1:] or ["Timestral-5M", "Timestral-28M", "Timestral-209M"]
H = {"A": 28, "B": 14}


def mase(y, yhat, ctx, m):
    """MAE scaled by the in-sample seasonal-naive MAE (m = season length)."""
    return np.mean(np.abs(y - yhat)) / np.mean(np.abs(ctx[m:] - ctx[:-m]))


def baselines(ctx, h, m):
    last = np.repeat(ctx[-1], h)
    mean7 = np.repeat(ctx[-7:].mean(), h)
    out = {"naive-last": last, "mean of last 7": mean7}
    if m > 1:                                                # seasonal rows only when a season exists
        season = np.array([ctx[-m + (i % m)] for i in range(h)])
        drift = (ctx[-1] - ctx[-1 - m]) / m                  # mean step over the last season
        out[f"seasonal-naive(m={m})"] = season
        out["seasonal-naive + drift"] = season + drift * (np.arange(h) + 1)
    return out


def report(name, ctx, truth, m, models):
    h = len(truth)
    rows = {k: (v, None) for k, v in baselines(ctx, h, m).items()}
    for mdl in models:
        f = models[mdl].forecast(ctx, prediction_length=h)
        med = np.asarray(f.median).ravel()
        lo, hi = np.asarray(f.quantile(0.1)).ravel(), np.asarray(f.quantile(0.9)).ravel()
        rows[mdl] = (med, np.mean((truth >= lo) & (truth <= hi)))
    print(f"\n== {name}  (context {len(ctx)} pts, horizon {h}, season m={m}) ==")
    print(f"{'method':<26}{'MAE':>8}{'MASE':>8}{'cov80':>8}")
    for k, (yhat, cov) in rows.items():
        c = f"{cov:.2f}" if cov is not None else "   -"
        print(f"{k:<26}{np.mean(np.abs(truth - yhat)):>8.3f}{mase(truth, yhat, ctx, m):>8.3f}{c:>8}")


def main():
    models = {n: TimestralForecaster.from_pretrained(f"mistralai/{n}", device="cpu") for n in MODELS}

    # Test A: known generator, high signal-to-noise
    rng = np.random.default_rng(7)
    n = 364 + H["A"]
    t = np.arange(n)
    dow = np.array([0.0, 2.0, 4.0, 8.0, 6.0, -4.0, -8.0])
    y = 100 + 0.05 * t + dow[t % 7] + rng.normal(0, 1.0, n)
    report("TEST A  known generator", y[:364], y[364:], 7, models)

    # Test B: real, fresh, Paris daily max temperature (ERA5 via open-meteo, no key)
    url = ("https://archive-api.open-meteo.com/v1/archive?latitude=48.85&longitude=2.35"
           "&start_date=2023-10-06&end_date=2026-10-19&daily=temperature_2m_max&timezone=UTC")
    d = json.load(urllib.request.urlopen(url))["daily"]
    temps = np.array(d["temperature_2m_max"], dtype=float)
    cut = d["time"].index("2026-10-06")
    short = d["time"].index("2026-05-01")
    print(f"\nopen-meteo: {len(temps)} days, {d['time'][0]} -> {d['time'][-1]}, holdout from {d['time'][cut]}")
    report("TEST B  Paris daily max temp, 158-day context", temps[short:cut], temps[cut:], 1, models)
    # Test C: same series, same holdout, same models, three years of context instead of one summer
    report("TEST C  Paris daily max temp, 3-year context", temps[:cut], temps[cut:], 1, models)


if __name__ == "__main__":
    main()
```

The output, verbatim:

```text
== TEST A  known generator  (context 364 pts, horizon 28, season m=7) ==
method                         MAE    MASE   cov80
naive-last                   9.650   9.209       -
mean of last 7               4.626   4.415       -
seasonal-naive(m=7)          0.890   0.849       -
seasonal-naive + drift       1.244   1.188       -
Timestral-5M                 0.896   0.855    0.64
Timestral-28M                0.862   0.823    0.64
Timestral-209M               0.851   0.812    0.68

open-meteo: 1110 days, 2023-10-06 -> 2026-10-19, holdout from 2026-10-06

== TEST B  Paris daily max temp, 158-day context  (context 158 pts, horizon 14, season m=1) ==
method                         MAE    MASE   cov80
naive-last                   5.636   2.409       -
mean of last 7               4.987   2.132       -
Timestral-5M                 5.785   2.473    0.43
Timestral-28M                6.540   2.796    0.43
Timestral-209M               6.489   2.774    0.43

== TEST C  Paris daily max temp, 3-year context  (context 1096 pts, horizon 14, season m=1) ==
method                         MAE    MASE   cov80
naive-last                   5.636   2.678       -
mean of last 7               4.987   2.370       -
Timestral-5M                 3.354   1.594    0.71
Timestral-28M                3.341   1.587    0.71
Timestral-209M               3.326   1.580    0.64
```

## Test A, the known generator

A year of daily data: a slow trend, a weekly pattern with a fixed shape, Gaussian noise one unit wide. The counting method, repeat last week, scores MASE 0.849, and the noise floor for this series is around 0.76, so there is not much room left to win. Timestral-5M ties the one-liner (0.855). The 209M takes 0.812, about four percent better, closing roughly a third of the remaining gap to the floor. The model captures the signal a human with a spreadsheet would capture. It does not transcend it.

The quieter number is the coverage column. The 10%–90% band should contain the truth eight times in ten; it did so 64% to 68% of the time. On its own synthetic home turf, with noise that is literally Gaussian, the model's uncertainty is too narrow. That is not a knock on the point forecast. It is the number you would want before you wired the band into an alert.

## Test B, one summer of Paris

Now the real series: 158 days of context, May 1 to October 5, forecast the next fourteen. Those fourteen days happened to be the moment Paris turned: 24.3 °C on the first day of the holdout, 12.4 °C on the last. The three Timestrals produced medians that went the other way, the 209M's path climbed from 23.7 to 24.9 °C across the two weeks, extrapolating the warm early-October spell upward. Every size lost to "repeat yesterday." The 80% band contained the truth on 6 of 14 days. Its lower edge never dropped below 18 °C; reality finished at 12.

This is not a model being stupid. With 158 days of context, the series contains one rising-then-flat summer and no previous autumn. Nothing in the window says October falls. A univariate forecaster can only continue what the window shows it, and the window showed a warm week.

## Test C, three Octobers

So I changed one thing: the context now starts in October 2023, 1,096 days, two complete autumns inside the window, same holdout, same models, same baselines, same code path. The 209M's median now descends from 22.3 to 17.6 °C. MAE drops from 6.489 to 3.326, a third better than the best baseline, which did not improve because baselines only look at the last few values anyway. Coverage rises from 43% to 64%; still under the 80% it should be, but the band's lower edge finally reaches 14 °C.

And the family converges: 5M at 3.354, 28M at 3.341, 209M at 3.326. The checkpoint that is forty times smaller on disk forecasts this series as well as the flagship, once both see the seasons. On the leaderboard the gap between those two models is 0.047 MASE on GIFT-Eval; on fourteen days of weather with the right history, it is noise.

![Same model, same fourteen days, two contexts, Paris truth falling 24 → 12 °C, the 158-day median climbing, the 3-year median descending, both 80% bands](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/9hwqbd8v3vx4dofbnor5.png)

## The license line that is not in the announcement

The announcement lists the license as "Modified MIT." The modification is in the LICENSE file on Hugging Face, clause 2, and it is one sentence: "You are not authorized to exercise any rights under this license if the global consolidated monthly revenue of your company (or that of your employer) exceeds $20 million (or its equivalent in another currency) for the preceding month." The next sentence refers to "This restriction in (b)", there is no (b) in the license; the clauses are numbered 1 and 2. The code repository is Apache-2.0; the weights are not. One HN reader quoted the clause within hours; it does not appear anywhere on the announcement page.

A revenue test no one can verify from the outside is the same control [this series graded on QGIS](https://dev.to/slabb/every-no-ai-contributions-policy-is-a-level-0-control-1a99): a rule enforced by the honesty of the person it restricts. That is not a complaint, most open-weight licenses are built this way, it is the rung. The sales address is in the same clause.

## What to steal

- **Run the one-line baseline first.** Seasonal naive took one line and scored 0.849; the state-of-the-art model took 837 MB and scored 0.812. If your series is seasonal and clean, the gap you are paying for is four percent.
- **Read the margin column, not the bar.** Every claim on the card is true. The headline margin is 0.003. Subtract the runner-up yourself; it takes a minute.
- **Check coverage before you ship the band.** A point forecast that is 4% better and an 80% interval that is right 64% of the time are two different products.
- **The context is the model.** One summer: the flagship lost to yesterday's temperature. Three years: the 20 MB model beat every baseline by a third. Before you shop for parameters, look at what you are feeding the window.

## Two honest limits

**Two series, one city, one fourteen-day holdout is an instrument, not a benchmark.** GIFT-Eval aggregates hundreds of series; nothing here contradicts Mistral's table, and nothing here could. What the tests show is what an aggregate hides, the spread between one summer and three years on the same model, and the script is there so you can swap in your own series and see which case you are in.

**I used Timestral as a univariate, past-only forecaster, the simplest mode it supports.** The model card lists known-future covariates and multivariate inputs; I fed it none, because the question was what the zero-shot model does with the series alone, and because that is how most first-time users will run it. A reader who hands it a weather forecast as a covariate is running a different test, and probably a better product.

## Your turn

Three commands: `pip install "git+https://github.com/mistralai/timestral.git"`, save the script, `python3 timestral_test.py`. The 5M downloads in seconds; the 209M is 837 MB. Then change two lines, the coordinates, or the URL to a series you actually care about, and post three numbers: the one-line baseline's MASE, the model's, and how often the 80% band held. If your series is like my summer, say so. If it is like my three years, say that. That is the forecasting review the leaderboard cannot write for you.
