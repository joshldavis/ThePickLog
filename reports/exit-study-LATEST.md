# ThePickLog — exit-rule study · 2026-08-15

Daily-resolution replay of **448** graded picks (of 500). Conservative same-day tie (stop fills first); 2% cost haircut; fills at level. **In-sample / exploratory** — a chosen rule must be pre-registered and validated forward.

_Bar provenance: every bar comes from the append-only grade-time record (paths.csv); 52 excluded for having no grade-time path (predate path capture). **No bar is ever re-fetched live.** A re-fetch returns split-adjusted prices while `entry_open` was recorded unadjusted at grade time, so one reverse split can inject a four-figure return and inflate the mean of every rule that exits at a bar price. Fixed 2026-07-29; the previous revision of this file reported the same-day-close baseline as +8.0% for that reason. Every pick below is additionally reconciled: `bars[0]` must reproduce the stored `ret_open_close_net` to within 0.05pp, so the same-day-close row equals outcomes.csv by construction and a stranger can check it._

| exit rule | n | win% | avg net/trade | median |
|---|---|---|---|---|
| Same-day close (current) | 448 | 30% | -3.1% | -2.6% |
| Hold to 5d close | 448 | 25% | -8.9% | -8.1% |
| Target +10% | 448 | 47% | -4.9% | -2.7% |
| Target +15% | 448 | 37% | -5.9% | -6.6% |
| Target +20% | 448 | 33% | -6.2% | -7.1% |
| Target +30% | 448 | 29% | -6.4% | -7.2% |
| Stop -10% | 448 | 20% | -6.7% | -12.0% |
| Stop -15% | 448 | 22% | -8.0% | -11.5% |
| H-EX2 +10% target / -20% stop [registered 2026-06-24] | 448 | 44% | -5.0% | -4.8% |
| Target +20% / Stop -10% | 448 | 25% | -5.0% | -12.0% |
| Target +15% / Stop -10% | 448 | 29% | -4.6% | -12.0% |
| Target +20% / Stop -15% | 448 | 28% | -6.2% | -10.2% |
| Trailing 15% | 448 | 24% | -4.6% | -8.2% |
| Trailing 20% | 448 | 25% | -6.3% | -9.0% |
| H-EX3 Target +5% [registered 2026-07-02] | 448 | 68% | -3.8% | +3.0% |
| H-EX4 +10% target / day-2 time stop [registered 2026-07-02] | 448 | 41% | -3.7% | -2.6% |
| H-EX5a Day-1 close [registered 2026-07-02] | 448 | 28% | -4.4% | -3.8% |
| H-EX5b Day-2 close [registered 2026-07-02] | 448 | 27% | -5.8% | -5.0% |
| H-EX6 half at +10%, half to 5d close [registered 2026-07-02] | 448 | 35% | -6.9% | -5.2% |
| H-EX7 trail 15% after +10% touch [registered 2026-07-02] | 448 | 28% | -5.2% | -5.9% |
| H-EX8 tier target A/B +20%, C/D +10% [registered 2026-07-02] | 448 | 46% | -5.0% | -3.4% |
| H-EX9a +10% target / -10% stop [registered 2026-07-02] | 448 | 38% | -3.8% | -12.0% |
| H-EX9b +10% target / -30% stop [registered 2026-07-02] | 448 | 47% | -4.7% | -3.0% |

⭐ = avg net/trade at least +2pp better than the current same-day-close exit.

**Read the median, not just the mean.** When a rule's avg net is far above its median (e.g. trailing stops), the average is carried by a few outlier runners — the *typical* trade is the median, which may still be negative. Such rules are high-variance and unreliable at this N.

**Slippage caveat:** target/stop/trailing fills are assumed exactly at the level. On thin low-float names, gaps blow through stops and you rarely fill a target cleanly, so real-world results for stop/trailing rules would be **worse** than shown here. The 2% haircut does not capture gap-through slippage.

_Not investment advice. In-sample/exploratory; a rule must be pre-registered (HYPOTHESES.md) and validated on post-registration picks before it means anything._
