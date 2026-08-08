# ThePickLog — exit-rule study · 2026-08-08

Daily-resolution replay of **400** graded picks (of 452). Conservative same-day tie (stop fills first); 2% cost haircut; fills at level. **In-sample / exploratory** — a chosen rule must be pre-registered and validated forward.

_Bar provenance: every bar comes from the append-only grade-time record (paths.csv); 52 excluded for having no grade-time path (predate path capture). **No bar is ever re-fetched live.** A re-fetch returns split-adjusted prices while `entry_open` was recorded unadjusted at grade time, so one reverse split can inject a four-figure return and inflate the mean of every rule that exits at a bar price. Fixed 2026-07-29; the previous revision of this file reported the same-day-close baseline as +8.0% for that reason. Every pick below is additionally reconciled: `bars[0]` must reproduce the stored `ret_open_close_net` to within 0.05pp, so the same-day-close row equals outcomes.csv by construction and a stranger can check it._

| exit rule | n | win% | avg net/trade | median |
|---|---|---|---|---|
| Same-day close (current) | 400 | 29% | -3.3% | -2.6% |
| Hold to 5d close | 400 | 23% | -9.5% | -8.5% |
| Target +10% | 400 | 45% | -5.7% | -4.2% |
| Target +15% | 400 | 34% | -6.7% | -7.1% |
| Target +20% | 400 | 31% | -6.8% | -7.6% |
| Target +30% | 400 | 28% | -6.8% | -8.1% |
| Stop -10% | 400 | 17% | -7.1% | -12.0% |
| Stop -15% | 400 | 20% | -8.5% | -12.5% |
| H-EX2 +10% target / -20% stop [registered 2026-06-24] | 400 | 42% | -5.6% | -6.1% |
| Target +20% / Stop -10% | 400 | 22% | -5.5% | -12.0% |
| Target +15% / Stop -10% | 400 | 26% | -5.2% | -12.0% |
| Target +20% / Stop -15% | 400 | 26% | -6.7% | -11.2% |
| Trailing 15% | 400 | 22% | -4.9% | -8.8% |
| Trailing 20% | 400 | 24% | -6.6% | -9.9% |
| H-EX3 Target +5% [registered 2026-07-02] | 400 | 66% | -4.2% | +3.0% |
| H-EX4 +10% target / day-2 time stop [registered 2026-07-02] | 400 | 39% | -4.2% | -3.0% |
| H-EX5a Day-1 close [registered 2026-07-02] | 400 | 25% | -4.8% | -4.0% |
| H-EX5b Day-2 close [registered 2026-07-02] | 400 | 25% | -6.3% | -5.4% |
| H-EX6 half at +10%, half to 5d close [registered 2026-07-02] | 400 | 32% | -7.6% | -5.9% |
| H-EX7 trail 15% after +10% touch [registered 2026-07-02] | 400 | 27% | -5.6% | -6.5% |
| H-EX8 tier target A/B +20%, C/D +10% [registered 2026-07-02] | 400 | 44% | -5.7% | -5.0% |
| H-EX9a +10% target / -10% stop [registered 2026-07-02] | 400 | 35% | -4.3% | -12.0% |
| H-EX9b +10% target / -30% stop [registered 2026-07-02] | 400 | 44% | -5.3% | -4.4% |

⭐ = avg net/trade at least +2pp better than the current same-day-close exit.

**Read the median, not just the mean.** When a rule's avg net is far above its median (e.g. trailing stops), the average is carried by a few outlier runners — the *typical* trade is the median, which may still be negative. Such rules are high-variance and unreliable at this N.

**Slippage caveat:** target/stop/trailing fills are assumed exactly at the level. On thin low-float names, gaps blow through stops and you rarely fill a target cleanly, so real-world results for stop/trailing rules would be **worse** than shown here. The 2% haircut does not capture gap-through slippage.

_Not investment advice. In-sample/exploratory; a rule must be pre-registered (HYPOTHESES.md) and validated on post-registration picks before it means anything._
