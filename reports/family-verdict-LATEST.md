# ThePickLog — family verdict (EXP02–EXP09) · 2026-11-11

Read date 2026-11-02. Benjamini–Hochberg at q = 0.05 across the declared family of **m = 8** (EXP02–EXP09); experiments not yet locked count as p = 1. Each row below was computed once, at the run where that experiment's own verdict locked, and is never recomputed. Rules: `family_verdict.py` (frozen 2026-10-23, before the read).

**EXP02 (locked 2026-11-11):** NO EDGE DETECTED — the bar is not met — n=46 over 21 names; excess (1 session) mean -0.141%, median +0.094%, clustered 95% CI [-0.43068, 0.20984]; weekly snapshots 0/3 (2026-10-24,2026-10-31,2026-11-07). Secondary exits (cannot rescue a fail): 5-session mean 0.2875, RSI-exit mean 0.17117.

| experiment | own verdict | p (two-sided) | BH-adjusted p | family status | decided |
|---|---|---|---|---|---|
| EXP02-RSI2 | NO EDGE DETECTED — the bar is not met | 0.39667 | 1.0 | **no discovery to correct** | 2026-11-11 |
| EXP03-MACD | NO EDGE DETECTED — the excess is indistinguishable from zero | 0.88667 | 1.0 | **no discovery to correct** | 2026-11-02 |
| EXP04-CAL | not locked yet | — | — | counts as p = 1 | — |
| EXP05-CAL | not locked yet | — | — | counts as p = 1 | — |
| EXP06-SUPERTREND | NO EDGE DETECTED — the excess is indistinguishable from zero | 0.564 | 1.0 | **no discovery to correct** | 2026-11-11 |
| EXP07-SMAPULL | NO EDGE DETECTED — the excess is indistinguishable from zero | 0.73333 | 1.0 | **no discovery to correct** | 2026-11-02 |
| EXP08-BOLLREVERT | not locked yet | — | — | counts as p = 1 | — |
| EXP09-NR7 | NO EDGE DETECTED — the excess is indistinguishable from zero | 0.65067 | 1.0 | **no discovery to correct** | 2026-11-02 |

A single pass that does not survive the correction is reported as *consistent with chance* until it survives a fresh forward window. EXP06–EXP09 share one universe, so they are correlated tests, not independent replications. Not investment advice.
