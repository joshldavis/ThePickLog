# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-08-11

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W33**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 27

- score -> |MAE| (drawdown depth): rho=+0.053 CI[-0.356,+0.456] n=27 tickers=14 ns
- score -> range (MFE-MAE): rho=+0.145 CI[-0.327,+0.529] n=27 tickers=14 ns
- score -> same-day return *(must stay ns)*: rho=-0.222 CI[-0.588,+0.247] n=27 tickers=14 ns
- score -> 5-day return *(must stay ns)*: rho=+0.057 CI[-0.375,+0.485] n=27 tickers=14 ns
- consecutive weekly snapshots with positive |MAE| rho: **1** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 20

- score -> |MAE| (drawdown depth): rho=+0.238 CI[-0.251,+0.705] n=20 tickers=20 ns
- score -> range (MFE-MAE): rho=+0.506 CI[+0.104,+0.784] n=20 tickers=20 SIG
- score -> same-day return *(must stay ns)*: rho=-0.086 CI[-0.564,+0.446] n=20 tickers=20 ns
- score -> 5-day return *(must stay ns)*: rho=+0.063 CI[-0.479,+0.511] n=20 tickers=20 ns
- consecutive weekly snapshots with positive |MAE| rho: **1** (need >= 3)

**v0.3-yf verdict: not yet established**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

Not evaluable yet: 27 post-registration v0.2 picks with a drawdown (need 30).

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
