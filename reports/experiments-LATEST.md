# ThePickLog — experiments under test · 2026-09-18

Every experiment below is forward-only from its registration date, scored as an **excess over a day-matched control** (the equal-weight return of its own frozen universe over the identical window), net of a declared cost. Mean, median and a ticker-clustered 95% CI are reported together, because a mean on financial data can be a single lucky trade. **Win rate is reported but is never a pass criterion.**

> **Amended 2026-08-07 — one experiment, one look.** The verdict used to be recomputed on every run from n>=30 onward, so across a year of snapshots a claim with no real effect had roughly a 1-in-5 chance of printing a pass at least once. Each experiment now also needs **>=20 distinct names** (repeated bets on one ticker are not independent evidence) and has **one pre-declared verdict date**, shown below. The verdict is computed at the first run on or after that date at which both floors are met, written once to an append-only verdicts file, and thereafter displayed from that file and **never recomputed**. Before that date this report shows running numbers and no verdict language of any kind. This changed REPORTING ONLY — no stored signal or outcome row was altered — and the dates were set from the batch's already-planned continue/kill read, without inspecting any current result. Full detail in HYPOTHESES.md.

## EXP03-MACD — The MACD bullish crossover

- status: **registered**, registered 2026-07-31, universe 40 names, hold 5 sessions, cost 0.1% round trip
- graded signals: **30** (need 30) over **21** distinct names (need 20); single pre-declared verdict date **2026-11-02**
- day-matched excess, 1 session: mean **-0.092%**, median **+0.024%**, 10% trimmed **-0.117%**, clustered 95% CI [-0.506, +0.350] over 21 names
- day-matched excess, 5 sessions: mean **-1.136%**, median **-2.450%**
- win rate 43% *(reported only — not a pass criterion)*
- **read: accruing — 30/30 graded signals over 21/20 distinct names. **No verdict is computed before the single pre-declared verdict date of 2026-11-02**, and none is computed then unless both floors are met.**

> Registered prior: The most widely taught indicator signal in retail trading — on every platform, in every beginner course. Published, universally known, and therefore the least likely thing in the world to still contain an edge. Registered expectation: the day-matched excess is indistinguishable from zero. Estimated probability it clears the bar: ~1 in 6. Being widely believed is not evidence, which is the point of testing it.

## EXP06-SUPERTREND — The Supertrend flip

- status: **registered**, registered 2026-08-06, universe 40 names, hold 5 sessions, cost 0.1% round trip
- graded signals: **6** (need 30) over **6** distinct names (need 20); single pre-declared verdict date **2026-11-02**
- day-matched excess, 1 session: mean **-0.624%**, median **-0.566%**, 10% trimmed **-0.624%**, clustered 95% CI n/a
- day-matched excess, 5 sessions: mean **-0.556%**, median **-1.872%**
- win rate 33% *(reported only — not a pass criterion)*
- **read: accruing — 6/30 graded signals over 6/20 distinct names. **No verdict is computed before the single pre-declared verdict date of 2026-11-02**, and none is computed then unless both floors are met.**

> Registered prior: Currently the most heavily marketed single indicator in retail video content, almost always at exactly these default settings (10, 3). It is a mechanically sane ATR trailing band, which is why it demos well — and why, on forty of the most liquid names on earth, it should already be arbitraged flat. Deliberately tested with NO trend filter because the claim as sold has none. Registered expectation: excess indistinguishable from zero; ~1 in 6 it clears.

## EXP07-SMAPULL — The moving-average pullback (buy the dip in an uptrend)

- status: **registered**, registered 2026-08-06, universe 40 names, hold 5 sessions, cost 0.1% round trip
- graded signals: **49** (need 30) over **22** distinct names (need 20); single pre-declared verdict date **2026-11-02**
- day-matched excess, 1 session: mean **+0.179%**, median **+0.039%**, 10% trimmed **+0.104%**, clustered 95% CI [-0.117, +0.604] over 22 names
- day-matched excess, 5 sessions: mean **+0.137%**, median **-0.150%**
- win rate 45% *(reported only — not a pass criterion)*
- **read: accruing — 49/30 graded signals over 22/20 distinct names. **No verdict is computed before the single pre-declared verdict date of 2026-11-02**, and none is computed then unless both floors are met.**

> Registered prior: The most widely taught swing entry in existence — nearly every course teaches some form of buying the pullback to the 20-day in an uptrend. The mechanism (short-term reversion inside medium-term momentum) is at least coherent, which earns it a slightly better prior than a raw indicator flip: call it ~1 in 5. Registered expectation is still that the day-matched excess is indistinguishable from zero — textbook status is exactly what arbitrages an edge away.

## EXP08-BOLLREVERT — Bollinger Band mean reversion

- status: **registered**, registered 2026-08-06, universe 40 names, hold 5 sessions, cost 0.1% round trip
- graded signals: **2** (need 30) over **1** distinct names (need 20); single pre-declared verdict date **2026-11-02**
- day-matched excess, 1 session: mean **-0.728%**, median **-0.728%**, 10% trimmed **-0.728%**, clustered 95% CI n/a
- day-matched excess, 5 sessions: mean **-1.977%**, median **-1.977%**
- win rate 0% *(reported only — not a pass criterion)*
- **read: accruing — 2/30 graded signals over 1/20 distinct names. **No verdict is computed before the single pre-declared verdict date of 2026-11-02**, and none is computed then unless both floors are met.**

> Registered prior: The same high-win-rate sales pitch as Experiment 02's RSI(2), through a different mechanism: the band adapts to volatility. Win-rate-flattering by construction — many small reverts punctuated by occasional large losses — which is precisely the shape the mean/median/clustered-CI reporting exists to expose. Registered expectation: excess indistinguishable from zero; ~1 in 6 it clears.

## EXP09-NR7 — Volatility contraction (NR7) in an uptrend

- status: **registered**, registered 2026-08-06, universe 40 names, hold 5 sessions, cost 0.1% round trip
- graded signals: **55** (need 30) over **26** distinct names (need 20); single pre-declared verdict date **2026-11-02**
- day-matched excess, 1 session: mean **+0.097%**, median **+0.074%**, 10% trimmed **+0.077%**, clustered 95% CI [-0.192, +0.421] over 26 names
- day-matched excess, 5 sessions: mean **+0.493%**, median **+0.570%**
- win rate 44% *(reported only — not a pass criterion)*
- **read: accruing — 55/30 graded signals over 26/20 distinct names. **No verdict is computed before the single pre-declared verdict date of 2026-11-02**, and none is computed then unless both floors are met.**

> Registered prior: That contraction precedes expansion (Crabel's NR7) is well documented; what is SOLD is the direction, and direction is the part with no documented edge. This is also the honest daily-bar version of an intraday claim: entry is the next open, not a break of the range, because our pre-open logging gate forbids acting on the open print. That deviation is disclosed wherever this experiment is published. Registered expectation: excess indistinguishable from zero; ~1 in 6.

---

Rules are frozen in `experiment_harness.py`; changing any constant voids that experiment and requires a new registration with a new window. Signals and outcomes are append-only under `experiments/`. Not investment advice.
