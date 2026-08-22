# ThePickLog — exit-rule study · 2026-08-22

Daily-resolution replay of **526** graded picks (of 578). Conservative same-day tie (stop fills first); 2% cost haircut; fills at level. **In-sample / exploratory** — a chosen rule must be pre-registered and validated forward.

_Bar provenance: every bar comes from the append-only grade-time record (paths.csv); 52 excluded for having no grade-time path (predate path capture). **No bar is ever re-fetched live.** A re-fetch returns split-adjusted prices while `entry_open` was recorded unadjusted at grade time, so one reverse split can inject a four-figure return and inflate the mean of every rule that exits at a bar price. Fixed 2026-07-29; the previous revision of this file reported the same-day-close baseline as +8.0% for that reason. Every pick below is additionally reconciled: `bars[0]` must reproduce the stored `ret_open_close_net` to within 0.05pp, so the same-day-close row equals outcomes.csv by construction and a stranger can check it._

| exit rule | n | win% | avg net/trade | median |
|---|---|---|---|---|
| Same-day close (current) | 526 | 29% | -2.9% | -2.5% |
| Hold to 5d close | 526 | 26% | -8.2% | -7.6% |
| Target +10% | 526 | 48% | -4.5% | -2.3% |
| Target +15% | 526 | 36% | -5.4% | -5.9% |
| Target +20% | 526 | 33% | -5.6% | -6.6% |
| Target +30% | 526 | 30% | -5.7% | -6.8% |
| Stop -10% | 526 | 21% | -6.1% | -12.0% |
| Stop -15% | 526 | 23% | -7.2% | -10.2% |
| H-EX2 +10% target / -20% stop [registered 2026-06-24] | 526 | 45% | -4.5% | -3.8% |
| Target +20% / Stop -10% | 526 | 25% | -4.6% | -12.0% |
| Target +15% / Stop -10% | 526 | 29% | -4.2% | -12.0% |
| Target +20% / Stop -15% | 526 | 29% | -5.4% | -8.8% |
| Trailing 15% | 526 | 25% | -4.3% | -7.6% |
| Trailing 20% | 526 | 26% | -5.6% | -8.3% |
| H-EX3 Target +5% [registered 2026-07-02] | 526 | 67% | -3.5% | +3.0% |
| H-EX4 +10% target / day-2 time stop [registered 2026-07-02] | 526 | 42% | -3.3% | -2.2% |
| H-EX5a Day-1 close [registered 2026-07-02] | 526 | 29% | -4.1% | -3.4% |
| H-EX5b Day-2 close [registered 2026-07-02] | 526 | 28% | -5.3% | -4.3% |
| H-EX6 half at +10%, half to 5d close [registered 2026-07-02] | 526 | 36% | -6.3% | -4.7% |
| H-EX7 trail 15% after +10% touch [registered 2026-07-02] | 526 | 29% | -4.9% | -5.9% |
| H-EX8 tier target A/B +20%, C/D +10% [registered 2026-07-02] | 526 | 46% | -4.6% | -3.1% |
| H-EX9a +10% target / -10% stop [registered 2026-07-02] | 526 | 39% | -3.5% | -12.0% |
| H-EX9b +10% target / -30% stop [registered 2026-07-02] | 526 | 47% | -4.3% | -2.5% |

⭐ = avg net/trade at least +2pp better than the current same-day-close exit.

**Read the median, not just the mean.** When a rule's avg net is far above its median (e.g. trailing stops), the average is carried by a few outlier runners — the *typical* trade is the median, which may still be negative. Such rules are high-variance and unreliable at this N.

**Slippage caveat:** target/stop/trailing fills are assumed exactly at the level. On thin low-float names, gaps blow through stops and you rarely fill a target cleanly, so real-world results for stop/trailing rules would be **worse** than shown here. The 2% haircut does not capture gap-through slippage.

_Not investment advice. In-sample/exploratory; a rule must be pre-registered (HYPOTHESES.md) and validated on post-registration picks before it means anything._
