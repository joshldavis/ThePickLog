# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-08-07

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W32**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 14

- score -> |MAE| (drawdown depth): rho=-0.379 CI[-0.798,+0.262] n=14 tickers=14 ns
- score -> range (MFE-MAE): rho=+0.090 CI[-0.564,+0.636] n=14 tickers=14 ns
- score -> same-day return *(must stay ns)*: rho=-0.051 CI[-0.676,+0.585] n=14 tickers=14 ns
- score -> 5-day return *(must stay ns)*: rho=+0.335 CI[-0.266,+0.820] n=14 tickers=14 ns
- consecutive weekly snapshots with positive |MAE| rho: **0** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 10

- score -> |MAE| (drawdown depth): rho=-0.092 CI[-0.656,+0.827] n=10 tickers=10 ns
- score -> range (MFE-MAE): rho=+0.350 CI[-0.384,+0.829] n=10 tickers=10 ns
- score -> same-day return *(must stay ns)*: rho=+0.202 CI[-0.568,+0.804] n=10 tickers=10 ns
- score -> 5-day return *(must stay ns)*: rho=+0.509 CI[-0.250,+0.896] n=10 tickers=10 ns
- consecutive weekly snapshots with positive |MAE| rho: **0** (need >= 3)

**v0.3-yf verdict: not yet established**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

Not evaluable yet: 14 post-registration v0.2 picks with a drawdown (need 30).

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
