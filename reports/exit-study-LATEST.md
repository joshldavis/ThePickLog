# ThePickLog — exit-rule study · 2026-07-25

Daily-resolution replay of **399** graded picks (of 399). Conservative same-day tie (stop fills first); 2% cost haircut; fills at level. **In-sample / exploratory** — a chosen rule must be pre-registered and validated forward.

_Bar provenance: 334 from the append-only grade-time record (paths.csv), 65 re-fetched (picks that predate path capture). Grade-time paths are reproducible from committed data; re-fetched bars can drift if Yahoo revises history, so they converge to the append-only source as the record matures._

| exit rule | n | win% | avg net/trade | median |
|---|---|---|---|---|
| Same-day close (current) | 399 | 33% | +8.0% | -2.3% |
| Hold to 5d close | 399 | 23% | -2.4% | -8.3% |
| Target +10% | 399 | 49% | -4.9% | -1.3% |
| Target +15% | 399 | 39% | -5.4% | -5.8% |
| Target +20% | 399 | 34% | -5.7% | -6.7% |
| Target +30% | 399 | 30% | -5.5% | -7.3% |
| Stop -10% | 399 | 16% | -0.2% | -12.0% |
| Stop -15% | 399 | 19% | -1.3% | -16.2% |
| H-EX2 +10% target / -20% stop [registered 2026-06-24] | 399 | 45% | -5.1% | -4.7% |
| Target +20% / Stop -10% | 399 | 23% | -5.0% | -12.0% |
| Target +15% / Stop -10% | 399 | 27% | -4.7% | -12.0% |
| Target +20% / Stop -15% | 399 | 28% | -5.7% | -10.4% |
| Trailing 15% ⭐ | 399 | 23% | +10.9% | -7.9% |
| Trailing 20% | 399 | 25% | +8.2% | -8.7% |
| H-EX3 Target +5% [registered 2026-07-02] | 399 | 71% | -3.5% | +3.0% |
| H-EX4 +10% target / day-2 time stop [registered 2026-07-02] | 399 | 44% | -3.3% | -2.1% |
| H-EX5a Day-1 close [registered 2026-07-02] | 399 | 29% | +6.1% | -3.6% |
| H-EX5b Day-2 close [registered 2026-07-02] | 399 | 27% | +3.7% | -4.8% |
| H-EX6 half at +10%, half to 5d close [registered 2026-07-02] | 399 | 32% | -3.6% | -5.5% |
| H-EX7 trail 15% after +10% touch [registered 2026-07-02] ⭐ | 399 | 30% | +11.8% | -5.6% |
| H-EX8 tier target A/B +20%, C/D +10% [registered 2026-07-02] | 399 | 47% | -4.8% | -2.5% |
| H-EX9a +10% target / -10% stop [registered 2026-07-02] | 399 | 35% | -4.2% | -12.0% |
| H-EX9b +10% target / -30% stop [registered 2026-07-02] | 399 | 48% | -4.9% | -2.0% |

⭐ = avg net/trade at least +2pp better than the current same-day-close exit.

**Read the median, not just the mean.** When a rule's avg net is far above its median (e.g. trailing stops), the average is carried by a few outlier runners — the *typical* trade is the median, which may still be negative. Such rules are high-variance and unreliable at this N.

**Slippage caveat:** target/stop/trailing fills are assumed exactly at the level. On thin low-float names, gaps blow through stops and you rarely fill a target cleanly, so real-world results for stop/trailing rules would be **worse** than shown here. The 2% haircut does not capture gap-through slippage.

_Not investment advice. In-sample/exploratory; a rule must be pre-registered (HYPOTHESES.md) and validated on post-registration picks before it means anything._
