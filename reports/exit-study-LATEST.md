# ThePickLog — exit-rule study · 2026-07-11

Daily-resolution replay of **239** graded picks (of 239). Conservative same-day tie (stop fills first); 2% cost haircut; fills at level. **In-sample / exploratory** — a chosen rule must be pre-registered and validated forward.

_Bar provenance: 174 from the immutable grade-time record (paths.csv), 65 re-fetched (picks that predate path capture). Grade-time paths are reproducible from committed data; re-fetched bars can drift if Yahoo revises history, so they converge to the immutable source as the record matures._

| exit rule | n | win% | avg net/trade | median |
|---|---|---|---|---|
| Same-day close (current) | 239 | 37% | -2.7% | -2.4% |
| Hold to 5d close | 239 | 28% | -6.9% | -7.6% |
| Target +10% | 239 | 56% | -3.7% | +8.0% |
| Target +15% | 239 | 46% | -3.9% | -2.5% |
| Target +20% | 239 | 41% | -3.7% | -4.9% |
| Target +30% | 239 | 36% | -3.6% | -6.1% |
| Stop -10% | 239 | 20% | -5.2% | -12.0% |
| Stop -15% | 239 | 24% | -6.0% | -13.2% |
| H-EX2 +10% target / -20% stop [registered 2026-06-24] | 239 | 52% | -3.6% | +8.0% |
| Target +20% / Stop -10% | 239 | 28% | -3.7% | -12.0% |
| Target +15% / Stop -10% | 239 | 33% | -3.4% | -12.0% |
| Target +20% / Stop -15% | 239 | 33% | -3.9% | -8.5% |
| Trailing 15% ⭐ | 239 | 28% | +4.0% | -6.5% |
| Trailing 20% ⭐ | 239 | 30% | +1.9% | -7.5% |
| H-EX3 Target +5% [registered 2026-07-02] | 239 | 74% | -2.9% | +3.0% |
| H-EX4 +10% target / day-2 time stop [registered 2026-07-02] | 239 | 50% | -2.7% | -0.0% |
| H-EX5a Day-1 close [registered 2026-07-02] | 239 | 31% | -2.9% | -3.4% |
| H-EX5b Day-2 close [registered 2026-07-02] | 239 | 31% | -3.6% | -4.2% |
| H-EX6 half at +10%, half to 5d close [registered 2026-07-02] | 239 | 39% | -5.3% | -3.3% |
| H-EX7 trail 15% after +10% touch [registered 2026-07-02] ⭐ | 239 | 36% | +6.0% | -4.4% |
| H-EX8 tier target A/B +20%, C/D +10% [registered 2026-07-02] | 239 | 55% | -3.4% | +8.0% |
| H-EX9a +10% target / -10% stop [registered 2026-07-02] | 239 | 41% | -3.2% | -12.0% |
| H-EX9b +10% target / -30% stop [registered 2026-07-02] | 239 | 55% | -3.6% | +8.0% |

⭐ = avg net/trade at least +2pp better than the current same-day-close exit.

**Read the median, not just the mean.** When a rule's avg net is far above its median (e.g. trailing stops), the average is carried by a few outlier runners — the *typical* trade is the median, which may still be negative. Such rules are high-variance and unreliable at this N.

**Slippage caveat:** target/stop/trailing fills are assumed exactly at the level. On thin low-float names, gaps blow through stops and you rarely fill a target cleanly, so real-world results for stop/trailing rules would be **worse** than shown here. The 2% haircut does not capture gap-through slippage.

_Not investment advice. In-sample/exploratory; a rule must be pre-registered (HYPOTHESES.md) and validated on post-registration picks before it means anything._
