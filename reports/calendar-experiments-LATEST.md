# ThePickLog — calendar experiments (EXP04, EXP05) · 2026-09-01

Both experiments are forward-only from **2026-08-06** and scored against **time-matched controls** (see the `calendar_eval.py` header for why the harness's cross-sectional control does not apply to timing claims). Mean, median and a clustered 95% CI are reported together. **Win rate is reported but is never a pass criterion.** SPY is a replication read only — QQQ decides.

> **Pass bar amended 2026-08-07**, before any row had ever been graded, after an adversarial review found the confidence interval was too narrow and the verdict was being re-tested at every look. Both experiments now require a minimum number of **clusters** (12 complete turn-of-month cycles for EXP04, 20 ISO weeks for EXP05) on top of the registered n>=30 sessions, and **no verdict of any kind is computed or displayed until those floors are met.** The registration date is unchanged. Full detail in HYPOTHESES.md and in the evaluator's header.

> **One experiment, one look.** Each experiment has a single pre-declared verdict date — **EXP05 2027-01-04, EXP04 2027-09-01**. The verdict is computed at the first run on or after that date at which the floors are met, written once to an append-only verdicts file, and thereafter displayed from that file and **never recomputed**. Re-running this script, on any later data, cannot turn a null into a pass. Before that date this report shows the running numbers and nothing else — a verdict re-tested at every weekly snapshot is a verdict with no alpha left to spend.

> **Known residual, measured not assumed.** Simulated under the null, the one-sided false-positive rate of this interval is **4.2% (+/-0.5) at the 12-cycle floor** against a nominal 2.5% — down from 12.1% as the code was originally written. A percentile cluster bootstrap stays modestly anti-conservative at any cluster count reachable in a sane window, and raising the floor further buys nothing measurable. So: read a bare "clears the bar" on EXP04 as about a 1-in-24 false-positive risk, not 1-in-40.

## QQQ  (PRIMARY — this decides)

### EXP04 — turn-of-month
- turn-of-month sessions graded: **4** (need 30); non-TOM control sessions: 13; complete cycles: **1** (need 12)
- TOM mean **+0.214%**/session, median +0.069% vs rest mean -0.039%, median -0.164%
- cycle-clustered 95% CI of the TOM-minus-rest difference: n/a — too few complete cycles
- TOM win rate 75% *(reported only)*
- **read: accruing — 4/30 turn-of-month sessions and 1/12 complete cycles. **No verdict is computed before the single pre-declared verdict date of 2027-09-01**, and none is computed then unless the floors are met.**

### EXP05 — overnight vs intraday (attribution claim)
- sessions graded: **17** (need 30); ISO weeks: **5** (need 20)
- overnight-minus-intraday: mean **+0.243%**/session, median +0.270%, week-clustered 95% CI [+0.033, +0.424] over 5 weeks
- overnight leg wins 65% of sessions *(reported only)*
- tradeability footnote: capturing the overnight leg costs one round trip per session; at 0.02%/RT the mean must exceed 0.02% just to break even. EXP05 passing does NOT make it tradeable — that is the registered scope.
- **read: accruing — 17/30 sessions and 5/20 ISO weeks. **No verdict is computed before the single pre-declared verdict date of 2027-01-04**, and none is computed then unless the floors are met.**

## SPY  (replication read only)

### EXP04 — turn-of-month
- turn-of-month sessions graded: **4** (need 30); non-TOM control sessions: 13; complete cycles: **1** (need 12)
- TOM mean **+0.038%**/session, median -0.102% vs rest mean -0.025%, median -0.030%
- cycle-clustered 95% CI of the TOM-minus-rest difference: n/a — too few complete cycles
- TOM win rate 50% *(reported only)*
- **read: accruing — 4/30 turn-of-month sessions and 1/12 complete cycles. **No verdict is computed before the single pre-declared verdict date of 2027-09-01**, and none is computed then unless the floors are met.**

### EXP05 — overnight vs intraday (attribution claim)
- sessions graded: **17** (need 30); ISO weeks: **5** (need 20)
- overnight-minus-intraday: mean **+0.183%**/session, median +0.049%, week-clustered 95% CI [+0.009, +0.285] over 5 weeks
- overnight leg wins 65% of sessions *(reported only)*
- tradeability footnote: capturing the overnight leg costs one round trip per session; at 0.02%/RT the mean must exceed 0.02% just to break even. EXP05 passing does NOT make it tradeable — that is the registered scope.
- **read: accruing — 17/30 sessions and 5/20 ISO weeks. **No verdict is computed before the single pre-declared verdict date of 2027-01-04**, and none is computed then unless the floors are met.**

---

Constants are frozen in `calendar_eval.py`; changing any voids the affected experiment and requires a new registration with a new window. Outcomes are append-only under `experiments/`. Not investment advice.
