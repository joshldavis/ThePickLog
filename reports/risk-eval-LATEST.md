# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-11-10

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W46**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 680

- score -> |MAE| (drawdown depth): rho=+0.219 CI[+0.082,+0.339] n=680 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.314 CI[+0.175,+0.429] n=680 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.033 CI[-0.141,+0.067] n=680 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.107 CI[-0.225,+0.002] n=680 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **14** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 563

- score -> |MAE| (drawdown depth): rho=+0.229 CI[+0.153,+0.306] n=563 tickers=392 SIG
- score -> range (MFE-MAE): rho=+0.283 CI[+0.202,+0.360] n=563 tickers=392 SIG
- score -> same-day return *(must stay ns)*: rho=+0.031 CI[-0.055,+0.114] n=563 tickers=392 ns
- score -> 5-day return *(must stay ns)*: rho=-0.203 CI[-0.280,-0.123] n=563 tickers=392 SIG
- consecutive weekly snapshots with positive |MAE| rho: **14** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.203), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1978** vs no-skill baseline **0.2054** -> BEATS baseline
- realised P(MAE <= -20%): Q1 18.9% vs Q5 52.5%
- Q5-Q1 gap: 33.6% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 18.9% · predicted 20.2% · n=143
  - Q2: realised 19.5% · predicted 39.6% · n=123
  - Q3: realised 22.8% · predicted 34.9% · n=149
  - Q4: realised 27.4% · predicted 38.2% · n=164
  - Q5: realised 52.5% · predicted 48.3% · n=101

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
