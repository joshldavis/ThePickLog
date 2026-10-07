# ThePickLog — exit-rule study · 2026-10-07

Daily-resolution replay of **810** graded picks (of 862). Conservative same-day tie (stop fills first); 2% cost haircut; fills at level. **In-sample / exploratory** — a chosen rule must be pre-registered and validated forward.

_Bar provenance: every bar comes from the append-only grade-time record (paths.csv); 52 excluded for having no grade-time path (predate path capture). **No bar is ever re-fetched live.** A re-fetch returns split-adjusted prices while `entry_open` was recorded unadjusted at grade time, so one reverse split can inject a four-figure return and inflate the mean of every rule that exits at a bar price. Fixed 2026-07-29; the previous revision of this file reported the same-day-close baseline as +8.0% for that reason. Every pick below is additionally reconciled: `bars[0]` must reproduce the stored `ret_open_close_net` to within 0.05pp, so the same-day-close row equals outcomes.csv by construction and a stranger can check it._

| exit rule | n | win% | avg net/trade | median |
|---|---|---|---|---|
| Same-day close (current) | 810 | 31% | -1.5% | -2.4% |
| Hold to 5d close | 810 | 27% | +nan% | -8.1% |
| Target +10% | 810 | 49% | -4.2% | -1.4% |
| Target +15% | 810 | 37% | -5.3% | -4.9% |
| Target +20% | 810 | 33% | +nan% | -5.6% |
| Target +30% | 810 | 31% | +nan% | -5.8% |
| Stop -10% | 810 | 22% | -5.5% | -12.0% |
| Stop -15% | 810 | 24% | -6.2% | -8.5% |
| H-EX2 +10% target / -20% stop [registered 2026-06-24] | 810 | 46% | -3.9% | -2.9% |
| Target +20% / Stop -10% | 810 | 27% | -3.9% | -12.0% |
| Target +15% / Stop -10% | 810 | 30% | -3.7% | -11.9% |
| Target +20% / Stop -15% | 810 | 30% | -4.7% | -7.3% |
| Trailing 15% | 810 | 26% | -0.9% | -6.6% |
| Trailing 20% | 810 | 28% | -2.2% | -7.1% |
| H-EX3 Target +5% [registered 2026-07-02] | 810 | 68% | -3.4% | +3.0% |
| H-EX4 +10% target / day-2 time stop [registered 2026-07-02] | 810 | 42% | -3.1% | -2.0% |
| H-EX5a Day-1 close [registered 2026-07-02] | 810 | 29% | -2.5% | -3.2% |
| H-EX5b Day-2 close [registered 2026-07-02] | 810 | 29% | -3.5% | -4.0% |
| H-EX6 half at +10%, half to 5d close [registered 2026-07-02] | 810 | 37% | +nan% | -5.8% |
| H-EX7 trail 15% after +10% touch [registered 2026-07-02] | 810 | 29% | -1.6% | -5.4% |
| H-EX8 tier target A/B +20%, C/D +10% [registered 2026-07-02] | 810 | 47% | -4.3% | -2.1% |
| H-EX9a +10% target / -10% stop [registered 2026-07-02] | 810 | 41% | -2.9% | -6.4% |
| H-EX9b +10% target / -30% stop [registered 2026-07-02] | 810 | 48% | -3.8% | -2.0% |

⭐ = avg net/trade at least +2pp better than the current same-day-close exit.

**Read the median, not just the mean.** When a rule's avg net is far above its median (e.g. trailing stops), the average is carried by a few outlier runners — the *typical* trade is the median, which may still be negative. Such rules are high-variance and unreliable at this N.

**Slippage caveat:** target/stop/trailing fills are assumed exactly at the level. On thin low-float names, gaps blow through stops and you rarely fill a target cleanly, so real-world results for stop/trailing rules would be **worse** than shown here. The 2% haircut does not capture gap-through slippage.

_Not investment advice. In-sample/exploratory; a rule must be pre-registered (HYPOTHESES.md) and validated on post-registration picks before it means anything._
