# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-09-03

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W36**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 258

- score -> |MAE| (drawdown depth): rho=+0.053 CI[-0.103,+0.219] n=258 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.261 CI[+0.141,+0.346] n=258 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.001 CI[-0.115,+0.101] n=258 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.078 CI[-0.108,+0.222] n=258 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **4** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 190

- score -> |MAE| (drawdown depth): rho=+0.265 CI[+0.118,+0.399] n=190 tickers=163 SIG
- score -> range (MFE-MAE): rho=+0.343 CI[+0.198,+0.479] n=190 tickers=163 SIG
- score -> same-day return *(must stay ns)*: rho=+0.095 CI[-0.055,+0.242] n=190 tickers=163 ns
- score -> 5-day return *(must stay ns)*: rho=-0.206 CI[-0.358,-0.044] n=190 tickers=163 SIG
- consecutive weekly snapshots with positive |MAE| rho: **4** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1790** vs no-skill baseline **0.1794** -> BEATS baseline
- realised P(MAE <= -20%): Q1 19.0% vs Q5 33.3%
- Q5-Q1 gap: 14.4% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 19.0% · predicted 20.2% · n=58
  - Q2: realised 16.0% · predicted 39.6% · n=50
  - Q3: realised 12.7% · predicted 34.9% · n=55
  - Q4: realised 13.8% · predicted 38.2% · n=65
  - Q5: realised 33.3% · predicted 48.3% · n=30

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
