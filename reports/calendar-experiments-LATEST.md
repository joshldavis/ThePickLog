# ThePickLog — calendar experiments (EXP04, EXP05) · 2026-08-07

Both experiments are forward-only from **2026-08-06** and scored against **time-matched controls** (see the `calendar_eval.py` header for why the harness's cross-sectional control does not apply to timing claims). Mean, median and a clustered 95% CI are reported together. **Win rate is reported but is never a pass criterion.** SPY is a replication read only — QQQ decides.

> **Pass bar amended 2026-08-07**, before any row had ever been graded, after an adversarial review found the confidence interval was too narrow and the verdict was being re-tested at every look. Both experiments now require a minimum number of **clusters** (12 complete turn-of-month cycles for EXP04, 20 ISO weeks for EXP05) on top of the registered n>=30 sessions, and **no verdict of any kind is computed or displayed until those floors are met.** The registration date is unchanged. Full detail in HYPOTHESES.md and in the evaluator's header.

> **Known residual, measured not assumed.** Simulated under the null, the one-sided false-positive rate of this interval is **4.2% (+/-0.5) at the 12-cycle floor** against a nominal 2.5% — down from 12.1% as the code was originally written. A percentile cluster bootstrap stays modestly anti-conservative at any cluster count reachable in a sane window, and raising the floor further buys nothing measurable. So: read a bare "clears the bar" on EXP04 as about a 1-in-24 false-positive risk, not 1-in-40.

## QQQ  (PRIMARY — this decides)

### EXP04 — turn-of-month
- turn-of-month sessions graded: **0** (need 30); non-TOM control sessions: 0; complete cycles: **0** (need 12)
- **read: accruing — 0/30 turn-of-month sessions and 0/12 complete cycles; no verdict is computed until both floors are met**

### EXP05 — overnight vs intraday (attribution claim)
- sessions graded: **0** (need 30); ISO weeks: **0** (need 20)
- **read: accruing — 0/30 sessions and 0/20 ISO weeks; no verdict is computed until both floors are met**

## SPY  (replication read only)

### EXP04 — turn-of-month
- turn-of-month sessions graded: **0** (need 30); non-TOM control sessions: 0; complete cycles: **0** (need 12)
- **read: accruing — 0/30 turn-of-month sessions and 0/12 complete cycles; no verdict is computed until both floors are met**

### EXP05 — overnight vs intraday (attribution claim)
- sessions graded: **0** (need 30); ISO weeks: **0** (need 20)
- **read: accruing — 0/30 sessions and 0/20 ISO weeks; no verdict is computed until both floors are met**

---

Constants are frozen in `calendar_eval.py`; changing any voids the affected experiment and requires a new registration with a new window. Outcomes are append-only under `experiments/`. Not investment advice.
