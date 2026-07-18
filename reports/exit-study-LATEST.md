# ThePickLog — exit-rule study · 2026-07-18

Daily-resolution replay of **319** graded picks (of 319). Conservative same-day tie (stop fills first); 2% cost haircut; fills at level. **In-sample / exploratory** — a chosen rule must be pre-registered and validated forward.

_Bar provenance: 254 from the immutable grade-time record (paths.csv), 65 re-fetched (picks that predate path capture). Grade-time paths are reproducible from committed data; re-fetched bars can drift if Yahoo revises history, so they converge to the immutable source as the record matures._

| exit rule | n | win% | avg net/trade | median |
|---|---|---|---|---|
| Same-day close (current) | 319 | 34% | +10.7% | -2.3% |
| Hold to 5d close | 319 | 25% | +0.4% | -8.1% |
| Target +10% | 319 | 51% | -4.3% | +2.0% |
| Target +15% | 319 | 42% | -4.5% | -4.7% |
| Target +20% | 319 | 37% | -4.6% | -5.8% |
| Target +30% | 319 | 33% | -4.3% | -6.7% |
| Stop -10% | 319 | 17% | +1.9% | -12.0% |
| Stop -15% | 319 | 21% | +1.2% | -13.2% |
| H-EX2 +10% target / -20% stop [registered 2026-06-24] | 319 | 47% | -4.6% | -2.7% |
| Target +20% / Stop -10% | 319 | 24% | -4.6% | -12.0% |
| Target +15% / Stop -10% | 319 | 28% | -4.4% | -12.0% |
| Target +20% / Stop -15% | 319 | 30% | -4.9% | -8.8% |
| Trailing 15% ⭐ | 319 | 24% | +15.0% | -7.6% |
| Trailing 20% | 319 | 26% | +12.3% | -7.9% |
| H-EX3 Target +5% [registered 2026-07-02] | 319 | 71% | -3.3% | +3.0% |
| H-EX4 +10% target / day-2 time stop [registered 2026-07-02] | 319 | 46% | -2.9% | -1.7% |
| H-EX5a Day-1 close [registered 2026-07-02] | 319 | 30% | +8.9% | -3.6% |
| H-EX5b Day-2 close [registered 2026-07-02] | 319 | 29% | +6.4% | -4.5% |
| H-EX6 half at +10%, half to 5d close [registered 2026-07-02] | 319 | 35% | -2.0% | -4.8% |
| H-EX7 trail 15% after +10% touch [registered 2026-07-02] ⭐ | 319 | 31% | +16.6% | -5.5% |
| H-EX8 tier target A/B +20%, C/D +10% [registered 2026-07-02] | 319 | 50% | -3.9% | +0.1% |
| H-EX9a +10% target / -10% stop [registered 2026-07-02] | 319 | 37% | -4.0% | -12.0% |
| H-EX9b +10% target / -30% stop [registered 2026-07-02] | 319 | 50% | -4.5% | +0.1% |

⭐ = avg net/trade at least +2pp better than the current same-day-close exit.

**Read the median, not just the mean.** When a rule's avg net is far above its median (e.g. trailing stops), the average is carried by a few outlier runners — the *typical* trade is the median, which may still be negative. Such rules are high-variance and unreliable at this N.

**Slippage caveat:** target/stop/trailing fills are assumed exactly at the level. On thin low-float names, gaps blow through stops and you rarely fill a target cleanly, so real-world results for stop/trailing rules would be **worse** than shown here. The 2% haircut does not capture gap-through slippage.

_Not investment advice. In-sample/exploratory; a rule must be pre-registered (HYPOTHESES.md) and validated on post-registration picks before it means anything._
