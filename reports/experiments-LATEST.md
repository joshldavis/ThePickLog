# ThePickLog — experiments under test · 2026-11-27

Every experiment below is forward-only from its registration date, scored as an **excess over a day-matched control** (the equal-weight return of its own frozen universe over the identical window), net of a declared cost. Mean, median and a ticker-clustered 95% CI are reported together, because a mean on financial data can be a single lucky trade. **Win rate is reported but is never a pass criterion.**

> **Amended 2026-08-07 — one experiment, one look.** The verdict used to be recomputed on every run from n>=30 onward, so across a year of snapshots a claim with no real effect had roughly a 1-in-5 chance of printing a pass at least once. Each experiment now also needs **>=20 distinct names** (repeated bets on one ticker are not independent evidence) and has **one pre-declared verdict date**, shown below. The verdict is computed at the first run on or after that date at which both floors are met, written once to an append-only verdicts file, and thereafter displayed from that file and **never recomputed**. Before that date this report shows running numbers and no verdict language of any kind. This changed REPORTING ONLY — no stored signal or outcome row was altered — and the dates were set from the batch's already-planned continue/kill read, without inspecting any current result. Full detail in HYPOTHESES.md.

## EXP03-MACD — The MACD bullish crossover

- status: **registered**, registered 2026-07-31, universe 40 names, hold 5 sessions, cost 0.1% round trip
- graded signals: **65** (need 30) over **30** distinct names (need 20); single pre-declared verdict date **2026-11-02**
- day-matched excess, 1 session: mean **-0.031%**, median **-0.068%**, 10% trimmed **-0.031%**, clustered 95% CI [-0.336, +0.247] over 30 names
- same, date-clustered 95% CI [-0.372, +0.310] over 40 dates *(reported beside the registered interval; no verdict reads it)*
- day-matched excess, 5 sessions: mean **-0.017%**, median **-0.287%**
- win rate 46% *(reported only — not a pass criterion)*
- **read: **NO EDGE DETECTED — the excess is indistinguishable from zero** *(locked 2026-11-02 at n=58 over 30 names — computed once, at the pre-declared verdict date, and never recomputed)***

> Registered prior: The most widely taught indicator signal in retail trading — on every platform, in every beginner course. Published, universally known, and therefore the least likely thing in the world to still contain an edge. Registered expectation: the day-matched excess is indistinguishable from zero. Estimated probability it clears the bar: ~1 in 6. Being widely believed is not evidence, which is the point of testing it.

## EXP06-SUPERTREND — The Supertrend flip

- status: **registered**, registered 2026-08-06, universe 40 names, hold 5 sessions, cost 0.1% round trip
- graded signals: **34** (need 30) over **30** distinct names (need 20); single pre-declared verdict date **2026-11-02**
- day-matched excess, 1 session: mean **-0.268%**, median **-0.054%**, 10% trimmed **-0.154%**, clustered 95% CI [-0.718, +0.144] over 30 names
- same, date-clustered 95% CI [-0.723, +0.187] over 21 dates *(reported beside the registered interval; no verdict reads it)*
- day-matched excess, 5 sessions: mean **-1.199%**, median **-0.867%**
- win rate 41% *(reported only — not a pass criterion)*
- **read: **NO EDGE DETECTED — the excess is indistinguishable from zero** *(locked 2026-11-11 at n=30 over 27 names — computed once, at the pre-declared verdict date, and never recomputed)***

> Registered prior: Currently the most heavily marketed single indicator in retail video content, almost always at exactly these default settings (10, 3). It is a mechanically sane ATR trailing band, which is why it demos well — and why, on forty of the most liquid names on earth, it should already be arbitraged flat. Deliberately tested with NO trend filter because the claim as sold has none. Registered expectation: excess indistinguishable from zero; ~1 in 6 it clears.

## EXP07-SMAPULL — The moving-average pullback (buy the dip in an uptrend)

- status: **registered**, registered 2026-08-06, universe 40 names, hold 5 sessions, cost 0.1% round trip
- graded signals: **180** (need 30) over **33** distinct names (need 20); single pre-declared verdict date **2026-11-02**
- day-matched excess, 1 session: mean **-0.010%**, median **+0.067%**, 10% trimmed **+0.028%**, clustered 95% CI [-0.235, +0.208] over 33 names
- same, date-clustered 95% CI [-0.237, +0.217] over 59 dates *(reported beside the registered interval; no verdict reads it)*
- day-matched excess, 5 sessions: mean **+0.583%**, median **+0.674%**
- win rate 48% *(reported only — not a pass criterion)*
- **read: **NO EDGE DETECTED — the excess is indistinguishable from zero** *(locked 2026-11-02 at n=138 over 31 names — computed once, at the pre-declared verdict date, and never recomputed)***

> Registered prior: The most widely taught swing entry in existence — nearly every course teaches some form of buying the pullback to the 20-day in an uptrend. The mechanism (short-term reversion inside medium-term momentum) is at least coherent, which earns it a slightly better prior than a raw indicator flip: call it ~1 in 5. Registered expectation is still that the day-matched excess is indistinguishable from zero — textbook status is exactly what arbitrages an edge away.

## EXP08-BOLLREVERT — Bollinger Band mean reversion

- status: **registered**, registered 2026-08-06, universe 40 names, hold 5 sessions, cost 0.1% round trip
- graded signals: **49** (need 30) over **21** distinct names (need 20); single pre-declared verdict date **2026-11-02**
- day-matched excess, 1 session: mean **-0.238%**, median **-0.043%**, 10% trimmed **-0.144%**, clustered 95% CI [-0.675, +0.207] over 21 names
- same, date-clustered 95% CI [-0.755, +0.279] over 28 dates *(reported beside the registered interval; no verdict reads it)*
- day-matched excess, 5 sessions: mean **-0.717%**, median **-0.553%**
- win rate 37% *(reported only — not a pass criterion)*
- **read: **NO EDGE DETECTED — the excess is indistinguishable from zero** *(locked 2026-11-17 at n=47 over 20 names — computed once, at the pre-declared verdict date, and never recomputed)***

> Registered prior: The same high-win-rate sales pitch as Experiment 02's RSI(2), through a different mechanism: the band adapts to volatility. Win-rate-flattering by construction — many small reverts punctuated by occasional large losses — which is precisely the shape the mean/median/clustered-CI reporting exists to expose. Registered expectation: excess indistinguishable from zero; ~1 in 6 it clears.

## EXP09-NR7 — Volatility contraction (NR7) in an uptrend

- status: **registered**, registered 2026-08-06, universe 40 names, hold 5 sessions, cost 0.1% round trip
- graded signals: **194** (need 30) over **35** distinct names (need 20); single pre-declared verdict date **2026-11-02**
- day-matched excess, 1 session: mean **-0.064%**, median **-0.018%**, 10% trimmed **-0.020%**, clustered 95% CI [-0.254, +0.114] over 35 names
- same, date-clustered 95% CI [-0.262, +0.134] over 58 dates *(reported beside the registered interval; no verdict reads it)*
- day-matched excess, 5 sessions: mean **+0.417%**, median **+0.429%**
- win rate 43% *(reported only — not a pass criterion)*
- **read: **NO EDGE DETECTED — the excess is indistinguishable from zero** *(locked 2026-11-02 at n=140 over 33 names — computed once, at the pre-declared verdict date, and never recomputed)***

> Registered prior: That contraction precedes expansion (Crabel's NR7) is well documented; what is SOLD is the direction, and direction is the part with no documented edge. This is also the honest daily-bar version of an intraday claim: entry is the next open, not a break of the range, because our pre-open logging gate forbids acting on the open print. That deviation is disclosed wherever this experiment is published. Registered expectation: excess indistinguishable from zero; ~1 in 6.

## EXP13A-MACD — Relaunch: the MACD bullish crossover (S&P 500)

- status: **registered**, registered 2026-11-27, universe 503 names (frozen S&P 500 list), primary = 5-session excess, cost 0.1% on the trade only, control excludes the traded name, SESOI ±0.75 pp
- floors: **0**/1000 graded trades, **0**/100 names, **0**/150 signal sessions. *Design v2 shows counts only until the floors are met — no running mean or interval is published, so no one watches the number.*
- **read: accruing — 0/1000 graded trades, 0/100 names, 0/150 signal sessions. No verdict is computed until all three floors are met.**

> Registered prior: Re-run of a rule that ended INCONCLUSIVE on 40 names. Registered expectation: equivalent to zero at the ±0.75 pp bound; no arm is expected to clear the bar.

## EXP13B-RSI2 — Relaunch: the 2-period RSI trade (S&P 500)

- status: **registered**, registered 2026-11-27, universe 503 names (frozen S&P 500 list), primary = 5-session excess, cost 0.1% on the trade only, control excludes the traded name, SESOI ±0.75 pp
- floors: **0**/1000 graded trades, **0**/100 names, **0**/150 signal sessions. *Design v2 shows counts only until the floors are met — no running mean or interval is published, so no one watches the number.*
- **read: accruing — 0/1000 graded trades, 0/100 names, 0/150 signal sessions. No verdict is computed until all three floors are met.**

> Registered prior: Re-run of a rule that ended INCONCLUSIVE on 40 names. Registered expectation: equivalent to zero at the ±0.75 pp bound; no arm is expected to clear the bar.

## EXP13C-SUPERTREND — Relaunch: the Supertrend flip (S&P 500)

- status: **registered**, registered 2026-11-27, universe 503 names (frozen S&P 500 list), primary = 5-session excess, cost 0.1% on the trade only, control excludes the traded name, SESOI ±0.75 pp
- floors: **0**/1000 graded trades, **0**/100 names, **0**/150 signal sessions. *Design v2 shows counts only until the floors are met — no running mean or interval is published, so no one watches the number.*
- **read: accruing — 0/1000 graded trades, 0/100 names, 0/150 signal sessions. No verdict is computed until all three floors are met.**

> Registered prior: Re-run of a rule that ended INCONCLUSIVE on 40 names. Registered expectation: equivalent to zero at the ±0.75 pp bound; no arm is expected to clear the bar.

## EXP13D-SMAPULL — Relaunch: the moving-average pullback (S&P 500)

- status: **registered**, registered 2026-11-27, universe 503 names (frozen S&P 500 list), primary = 5-session excess, cost 0.1% on the trade only, control excludes the traded name, SESOI ±0.75 pp
- floors: **0**/1000 graded trades, **0**/100 names, **0**/150 signal sessions. *Design v2 shows counts only until the floors are met — no running mean or interval is published, so no one watches the number.*
- **read: accruing — 0/1000 graded trades, 0/100 names, 0/150 signal sessions. No verdict is computed until all three floors are met.**

> Registered prior: Re-run of a rule that ended INCONCLUSIVE on 40 names. Registered expectation: equivalent to zero at the ±0.75 pp bound; no arm is expected to clear the bar.

## EXP13E-BOLLREVERT — Relaunch: the Bollinger reversion (S&P 500)

- status: **registered**, registered 2026-11-27, universe 503 names (frozen S&P 500 list), primary = 5-session excess, cost 0.1% on the trade only, control excludes the traded name, SESOI ±0.75 pp
- floors: **0**/1000 graded trades, **0**/100 names, **0**/150 signal sessions. *Design v2 shows counts only until the floors are met — no running mean or interval is published, so no one watches the number.*
- **read: accruing — 0/1000 graded trades, 0/100 names, 0/150 signal sessions. No verdict is computed until all three floors are met.**

> Registered prior: Re-run of a rule that ended INCONCLUSIVE on 40 names. Registered expectation: equivalent to zero at the ±0.75 pp bound; no arm is expected to clear the bar.

## EXP13F-NR7 — Relaunch: the NR7 uptrend squeeze (S&P 500)

- status: **registered**, registered 2026-11-27, universe 503 names (frozen S&P 500 list), primary = 5-session excess, cost 0.1% on the trade only, control excludes the traded name, SESOI ±0.75 pp
- floors: **0**/1000 graded trades, **0**/100 names, **0**/150 signal sessions. *Design v2 shows counts only until the floors are met — no running mean or interval is published, so no one watches the number.*
- **read: accruing — 0/1000 graded trades, 0/100 names, 0/150 signal sessions. No verdict is computed until all three floors are met.**

> Registered prior: Re-run of a rule that ended INCONCLUSIVE on 40 names. Registered expectation: equivalent to zero at the ±0.75 pp bound; no arm is expected to clear the bar.

---

Rules are frozen in `experiment_harness.py`; changing any constant voids that experiment and requires a new registration with a new window. Signals and outcomes are append-only under `experiments/`. Not investment advice.
