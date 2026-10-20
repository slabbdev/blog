---
titre: "Timestral de Mistral est n°1 avec 0,003 MASE d'avance. Je l'ai fait tourner — le modèle n'était pas la variable."
date: 2026-10-20
themes: ia, preuve
resume: "Mistral a sorti Timestral, quatre modèles de séries temporelles à poids ouverts qui dominent trois benchmarks — de 0,003 MASE sur leur propre table. J'ai fait tourner les trois tailles contre des baselines d'une ligne, sur un générateur connu et sur la météo parisienne fraîche. Avec un été de contexte, le 209M perd contre « répéter hier » ; avec trois ans, il bat tout d'un tiers — et le modèle de 20 Mo égale celui de 837 Mo."
source: https://dev.to/slabb/mistrals-timestral-is-1-by-0003-mase-i-ran-it-the-model-was-not-the-variable-1bf8
image: https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/p6yb6d3fwxmi9074beh4.png
image_alt: "Même modèle, mêmes quatorze jours, deux contextes — la vérité parisienne qui chute, la médiane 158 jours qui monte, la médiane 3 ans qui descend, leurs bandes à 80 %"
---

Même modèle, mêmes quatorze jours de météo parisienne, même holdout. La seule chose que j'ai changée entre ces deux lignes, c'est la quantité d'histoire que je lui ai donnée :

```text
Timestral-209M, context = one summer (158 days)   MAE 6.489   80% band covered the truth 43% of the time
Timestral-209M, context = three years (1,096 days) MAE 3.326   80% band covered the truth 64% of the time
"repeat yesterday", no model at all                MAE 5.636
```

Avec un été dans la fenêtre, le nouveau prévisionneur state-of-the-art de Mistral perdait contre une baseline qui répète la dernière valeur. Avec trois octobres dans la fenêtre, il battait toutes les baselines d'un tiers. Et le plus petit modèle de la famille — 20,8 Mo sur disque — terminait à 0,03 du fleuron de 837 Mo. La variable qui comptait, ce n'étaient pas les paramètres. C'était le contexte. Rien sur un leaderboard ne vous le dit ; un script de quatre-vingt-dix lignes le fait, et il est plus bas.

## La sortie, et le chiffre derrière la première place

Le 15 octobre, Mistral a publié [Timestral](https://mistral.ai/news/timestral), sa première famille de modèles de fondation pour séries temporelles : quatre checkpoints à poids ouverts de 5M, 28M, 123M et 209M paramètres, prévision zero-shot avec 21 quantiles, jusqu'à 32 768 pas de contexte, PyTorch sur CPU ou GPU, code sur [GitHub](https://github.com/mistralai/timestral) sous Apache-2.0. L'annonce est précise : il « ranks first on all three of the field's main public benchmarks, GIFT-Eval, TIME, and fev-bench » — premier sur les trois grands benchmarks publics du domaine — et « Among pre-trained, zero-shot models, it ranks first across all five metrics » — premier sur les cinq métriques parmi les modèles pré-entraînés zero-shot. Également : « These results come from a single checkpoint, without ensembling ». Le [fil Hacker News](https://news.ycombinator.com/item?id=50150434) a atteint 601 points.

Les marges sont sur la [model card](https://huggingface.co/mistralai/Timestral-209M), dans la propre table de Mistral. J'ai copié la colonne de première place et celle du second, et j'ai soustrait :

| Benchmark | Métrique | Timestral-209M | Second (t0-gamma) | Marge |
|---|---|---|---|---|
| GIFT-Eval | MASE ↓ | 0.658 | 0.661 | **0.003** |
| GIFT-Eval | CRPS ↓ | 0.446 | 0.452 | 0.006 |
| TIME | MASE ↓ | 0.626 | 0.637 | 0.011 |
| TIME | CRPS ↓ | 0.522 | 0.534 | 0.012 |
| fev-bench | SQL skill ↑ | 50.39 | 49.42 | 0.97 |
| fev-bench | MASE skill ↑ | 39.49 | 37.99 | 1.50 |

Chaque ligne est une première place, et l'annonce a raison sur chaque ligne. La première place sur le benchmark vedette vaut trois millièmes de point de MASE. Un commentateur HN l'a dit brutalement — « crazy how they make an improvement of 0.03 look like a 5x difference » — et le chiffre de la carte est plus petit que le sien. Un autre a noté que « the blog post features an imaginary customer rather than an actual reference » ; j'ai lu la page deux fois : aucun client n'est nommé, l'étude de cas s'ouvre sur « Consider an industrial plant with thousands of sensors across its equipment ».

Rien de tout cela ne rend le modèle mauvais. Cela rend la table à lire avant le graphique en barres. Et une ligne de l'annonce a décidé à quoi mon test devait ressembler : « The majority of the training data was synthetic ». Les modèles ont été pré-entraînés sur des processus générés — tendances, saisonnalité, bruit — puis post-entraînés sur un mélange de réel et de synthétique. Une série synthétique, c'est leur terrain maison.

## Le test que le fil demandait

Enfoui dans la discussion, il y avait un protocole, de la part d'un commentateur qui visiblement fait ça pour vivre : « To meaningfully test a forecasting model, use a data-generating process with a high signal-to-noise ratio where a classical method (empirical conditional distributions, i.e., counting) can capture most of the signal. Then check whether the model captures that signal too. If you only test on high-noise processes, any model looks » identique. C'est donc le Test A. Le Test B, c'est l'inverse : une série réelle qui n'existait pas au moment de la publication des modèles — la température maximale quotidienne de Paris via [open-meteo](https://open-meteo.com/), sans clé d'API, jusqu'à hier. Le Test C, c'est le Test B avec la fenêtre de contexte repoussée de trois ans.

Trois tailles (5M, 28M, 209M), CPU seulement, chaque prévision déterministe — j'ai lancé le script entier deux fois et comparé les sorties : identiques à l'octet près. Les baselines font une ligne chacune : répéter la dernière valeur, la moyenne des sept derniers jours, et pour la série saisonnière, répéter la semaine dernière. Métriques : MAE, MASE (la MAE normalisée par l'erreur naïve in-sample, la même famille de métrique que les leaderboards), et la fréquence à laquelle la bande 10 %–90 % du modèle contient réellement la vérité — ce qui devrait tourner autour de 80 % si l'incertitude est honnête.

```python
#!/usr/bin/env python3
"""timestral_test.py — three tests a reader can rerun in minutes, no API key.

Test A  a series with a KNOWN generator (trend + weekly pattern + small noise).
        A counting method (seasonal naive) captures most of the signal.
        Does the foundation model capture it too?  (protocol from the HN thread)
Test B  a REAL series nothing could have memorized: Paris daily max temperature,
        open-meteo archive, context May 1 -> Oct 5 2026, holdout Oct 6 -> Oct 19.
Test C  same series, same holdout, same models — three years of context instead
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

    # Test B: real, fresh — Paris daily max temperature (ERA5 via open-meteo, no key)
    url = ("https://archive-api.open-meteo.com/v1/archive?latitude=48.85&longitude=2.35"
           "&start_date=2023-10-06&end_date=2026-10-19&daily=temperature_2m_max&timezone=UTC")
    d = json.load(urllib.request.urlopen(url))["daily"]
    temps = np.array(d["temperature_2m_max"], dtype=float)
    cut = d["time"].index("2026-10-06")
    short = d["time"].index("2026-05-01")
    print(f"\nopen-meteo: {len(temps)} days, {d['time'][0]} -> {d['time'][-1]}, holdout from {d['time'][cut]}")
    report("TEST B  Paris daily max temp, 158-day context", temps[short:cut], temps[cut:], 1, models)
    # Test C: same series, same holdout, same models — three years of context instead of one summer
    report("TEST C  Paris daily max temp, 3-year context", temps[:cut], temps[cut:], 1, models)


if __name__ == "__main__":
    main()
```

La sortie, verbatim :

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

## Test A — le générateur connu

Un an de données quotidiennes : une tendance lente, un motif hebdomadaire à forme fixe, un bruit gaussien large d'une unité. La méthode de comptage — répéter la semaine dernière — fait MASE 0,849, et le plancher de bruit de cette série est autour de 0,76, il ne reste donc pas beaucoup de marge à prendre. Timestral-5M égalise la monoligne (0,855). Le 209M prend 0,812, soit environ quatre pour cent de mieux, en refermant à peu près un tiers de l'écart restant jusqu'au plancher. Le modèle capture le signal qu'un humain avec un tableur capturerait. Il ne le transcende pas.

Le chiffre le plus discret, c'est la colonne de couverture. La bande 10 %–90 % devrait contenir la vérité huit fois sur dix ; elle l'a contenue 64 % à 68 % du temps. Sur son propre terrain synthétique, avec un bruit littéralement gaussien, l'incertitude du modèle est trop étroite. Ce n'est pas un procès fait à la prévision ponctuelle. C'est le chiffre que vous voudriez connaître avant de câbler la bande dans une alerte.

## Test B — un été de Paris

Maintenant la série réelle : 158 jours de contexte, du 1er mai au 5 octobre, prévoir les quatorze jours suivants. Ces quatorze jours se sont trouvés être le moment où Paris bascule : 24,3 °C le premier jour du holdout, 12,4 °C le dernier. Les trois Timestral ont produit des médianes qui partaient dans l'autre sens — la trajectoire du 209M est montée de 23,7 à 24,9 °C sur les deux semaines, extrapolant vers le haut l'épisode doux de début octobre. Toutes les tailles ont perdu contre « répéter hier ». La bande 80 % contenait la vérité 6 jours sur 14. Son bord inférieur n'est jamais descendu sous 18 °C ; le réel terminait à 12.

Ce n'est pas un modèle qui serait bête. Avec 158 jours de contexte, la série contient un seul été — montée puis plateau — et aucun automne précédent. Rien dans la fenêtre ne dit qu'octobre fait tomber les températures. Un prévisionneur univarié ne peut que continuer ce que la fenêtre lui montre — et la fenêtre montrait une semaine douce.

## Test C — trois octobres

J'ai donc changé une seule chose : le contexte démarre maintenant en octobre 2023 — 1 096 jours, deux automnes complets dans la fenêtre — même holdout, mêmes modèles, mêmes baselines, même chemin de code. La médiane du 209M descend maintenant de 22,3 à 17,6 °C. La MAE passe de 6,489 à 3,326 — un tiers de mieux que la meilleure baseline, qui n'a pas progressé parce que les baselines ne regardent de toute façon que les dernières valeurs. La couverture monte de 43 % à 64 % ; toujours sous les 80 % qu'elle devrait faire, mais le bord inférieur de la bande atteint enfin 14 °C.

Et la famille converge : 5M à 3,354, 28M à 3,341, 209M à 3,326. Le checkpoint quarante fois plus petit sur disque prévoit cette série aussi bien que le fleuron, dès que tous deux voient les saisons. Sur le leaderboard, l'écart entre ces deux modèles est de 0,047 MASE sur GIFT-Eval ; sur quatorze jours de météo avec la bonne histoire, c'est du bruit.

![Même modèle, mêmes quatorze jours, deux contextes — la vérité parisienne qui chute de 24 à 12 °C, la médiane 158 jours qui monte, la médiane 3 ans qui descend, les deux bandes à 80 %](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/9hwqbd8v3vx4dofbnor5.png)

## La ligne de licence qui n'est pas dans l'annonce

L'annonce donne la licence comme « Modified MIT ». La modification est dans le fichier LICENSE sur Hugging Face, clause 2, et c'est une phrase : « You are not authorized to exercise any rights under this license if the global consolidated monthly revenue of your company (or that of your employer) exceeds $20 million (or its equivalent in another currency) for the preceding month ». La phrase suivante renvoie à « This restriction in (b) » — il n'y a pas de (b) dans la licence ; les clauses sont numérotées 1 et 2. Le dépôt de code est Apache-2.0 ; les poids, non. Un lecteur HN a cité la clause dans les heures qui ont suivi ; elle n'apparaît nulle part sur la page d'annonce.

Un test de revenu que personne ne peut vérifier de l'extérieur, c'est le même contrôle que [cette série a gradué sur QGIS](https://dev.to/slabb/every-no-ai-contributions-policy-is-a-level-0-control-1a99) : une règle appliquée par l'honnêteté de la personne qu'elle restreint. Ce n'est pas une plainte — la plupart des licences open-weight sont construites ainsi — c'est le barreau. L'adresse commerciale est dans la même clause.

## Ce qu'il faut voler

- **Lancez d'abord la baseline d'une ligne.** Le seasonal naive a pris une ligne et a marqué 0,849 ; le modèle state-of-the-art a pris 837 Mo et a marqué 0,812. Si votre série est saisonnière et propre, l'écart que vous payez est de quatre pour cent.
- **Lisez la colonne des marges, pas les barres.** Chaque claim de la carte est vrai. La marge vedette est de 0,003. Soustrayez le second vous-même ; ça prend une minute.
- **Vérifiez la couverture avant de livrer la bande.** Une prévision ponctuelle 4 % meilleure et un intervalle à 80 % juste 64 % du temps, ce sont deux produits différents.
- **Le contexte, c'est le modèle.** Un été : le fleuron perdait contre la température d'hier. Trois ans : le modèle de 20 Mo battait toutes les baselines d'un tiers. Avant de faire le magasinage des paramètres, regardez ce que vous donnez à la fenêtre.

## Deux limites honnêtes

**Deux séries, une ville, un holdout de quatorze jours, c'est un instrument, pas un benchmark.** GIFT-Eval agrège des centaines de séries ; rien ici ne contredit la table de Mistral, et rien ici ne le pourrait. Ce que les tests montrent, c'est ce qu'un agrégat cache — l'écart entre un été et trois ans sur le même modèle — et le script est là pour que vous y glissiez votre propre série et voyiez dans quel cas vous êtes.

**J'ai utilisé Timestral comme prévisionneur univarié, passé seul — le mode le plus simple qu'il supporte.** La model card liste les covariables connues du futur et les entrées multivariées ; je n'en ai donné aucune, parce que la question était de savoir ce que fait le modèle zero-shot avec la série seule, et parce que c'est ainsi que la plupart des premiers utilisateurs le lanceront. Un lecteur qui lui donne une prévision météo en covariable fait un autre test, et probablement un meilleur produit.

## À votre tour

Trois commandes : `pip install "git+https://github.com/mistralai/timestral.git"`, enregistrez le script, `python3 timestral_test.py`. Le 5M se télécharge en quelques secondes ; le 209M fait 837 Mo. Puis changez deux lignes — les coordonnées, ou l'URL d'une série qui vous importe vraiment — et postez trois chiffres : le MASE de la baseline d'une ligne, celui du modèle, et la fréquence à laquelle la bande 80 % a tenu. Si votre série ressemble à mon été, dites-le. Si elle ressemble à mes trois ans, dites-le aussi. C'est la revue de prévision que le leaderboard ne peut pas écrire pour vous.
