# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-11-20

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W47**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 750

- score -> |MAE| (drawdown depth): rho=+0.193 CI[+0.067,+0.303] n=750 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.288 CI[+0.164,+0.397] n=750 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.049 CI[-0.168,+0.067] n=750 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.086 CI[-0.191,+0.013] n=750 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **15** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 643

- score -> |MAE| (drawdown depth): rho=+0.243 CI[+0.169,+0.315] n=643 tickers=446 SIG
- score -> range (MFE-MAE): rho=+0.284 CI[+0.210,+0.355] n=643 tickers=446 SIG
- score -> same-day return *(must stay ns)*: rho=+0.007 CI[-0.075,+0.087] n=643 tickers=446 ns
- score -> 5-day return *(must stay ns)*: rho=-0.230 CI[-0.305,-0.156] n=643 tickers=446 SIG
- consecutive weekly snapshots with positive |MAE| rho: **15** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.230), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.2032** vs no-skill baseline **0.2081** -> BEATS baseline
- realised P(MAE <= -20%): Q1 22.6% vs Q5 52.2%
- Q5-Q1 gap: 29.6% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 22.6% · predicted 20.2% · n=155
  - Q2: realised 19.1% · predicted 39.6% · n=136
  - Q3: realised 23.8% · predicted 34.9% · n=164
  - Q4: realised 27.5% · predicted 38.2% · n=182
  - Q5: realised 52.2% · predicted 48.3% · n=113

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
