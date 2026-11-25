# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-11-25

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W48**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 776

- score -> |MAE| (drawdown depth): rho=+0.180 CI[+0.056,+0.288] n=776 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.281 CI[+0.157,+0.391] n=776 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.038 CI[-0.160,+0.082] n=776 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.066 CI[-0.176,+0.039] n=776 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **16** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 671

- score -> |MAE| (drawdown depth): rho=+0.248 CI[+0.175,+0.320] n=671 tickers=463 SIG
- score -> range (MFE-MAE): rho=+0.294 CI[+0.220,+0.365] n=671 tickers=463 SIG
- score -> same-day return *(must stay ns)*: rho=+0.010 CI[-0.072,+0.087] n=671 tickers=463 ns
- score -> 5-day return *(must stay ns)*: rho=-0.227 CI[-0.299,-0.154] n=671 tickers=463 SIG
- consecutive weekly snapshots with positive |MAE| rho: **16** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.227), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.2060** vs no-skill baseline **0.2097** -> BEATS baseline
- realised P(MAE <= -20%): Q1 24.7% vs Q5 53.0%
- Q5-Q1 gap: 28.3% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 24.7% · predicted 20.2% · n=162
  - Q2: realised 19.0% · predicted 39.6% · n=142
  - Q3: realised 24.1% · predicted 34.9% · n=166
  - Q4: realised 27.5% · predicted 38.2% · n=189
  - Q5: realised 53.0% · predicted 48.3% · n=117

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
