# IgnitionScan — exit-rule study · 2026-07-04

Daily-resolution replay of **165** graded picks (of 165). Conservative same-day tie (stop fills first); 2% cost haircut; fills at level. **In-sample / exploratory** — a chosen rule must be pre-registered and validated forward.

_Bar provenance: 100 from the immutable grade-time record (paths.csv), 65 re-fetched (picks that predate path capture). Grade-time paths are reproducible from committed data; re-fetched bars can drift if Yahoo revises history, so they converge to the immutable source as the record matures._

| exit rule | n | win% | avg net/trade | median |
|---|---|---|---|---|
| Same-day close (current) | 165 | 35% | -3.0% | -2.9% |
| Hold to 5d close | 165 | 28% | -7.4% | -8.5% |
| Target +10% | 165 | 57% | -4.3% | +8.0% |
| Target +15% | 165 | 47% | -4.3% | -2.7% |
| Target +20% | 165 | 42% | -4.1% | -5.9% |
| Target +30% | 165 | 36% | -4.3% | -7.2% |
| Stop -10% | 165 | 19% | -5.3% | -12.0% |
| Stop -15% | 165 | 23% | -6.4% | -17.0% |
| H-EX2 +10% target / -20% stop [registered 2026-06-24] | 165 | 52% | -4.3% | +8.0% |
| Target +20% / Stop -10% | 165 | 28% | -3.5% | -12.0% |
| Target +15% / Stop -10% | 165 | 33% | -3.4% | -12.0% |
| Target +20% / Stop -15% | 165 | 33% | -4.2% | -11.5% |
| Trailing 15% ⭐ | 165 | 29% | +6.5% | -7.4% |
| Trailing 20% ⭐ | 165 | 28% | +3.7% | -8.9% |
| H-EX3 Target +5% [registered 2026-07-02] | 165 | 74% | -3.1% | +3.0% |
| H-EX4 +10% target / day-2 time stop [registered 2026-07-02] | 165 | 49% | -3.1% | -1.0% |
| H-EX5a Day-1 close [registered 2026-07-02] | 165 | 28% | -2.9% | -4.4% |
| H-EX5b Day-2 close [registered 2026-07-02] | 165 | 27% | -3.7% | -5.9% |
| H-EX6 half at +10%, half to 5d close [registered 2026-07-02] | 165 | 39% | -5.9% | -3.8% |
| H-EX7 trail 15% after +10% touch [registered 2026-07-02] ⭐ | 165 | 37% | +9.0% | -5.4% |
| H-EX8 tier target A/B +20%, C/D +10% [registered 2026-07-02] | 165 | 55% | -4.0% | +8.0% |
| H-EX9a +10% target / -10% stop [registered 2026-07-02] | 165 | 42% | -3.4% | -12.0% |
| H-EX9b +10% target / -30% stop [registered 2026-07-02] | 165 | 55% | -4.0% | +8.0% |

⭐ = avg net/trade at least +2pp better than the current same-day-close exit.

**Read the median, not just the mean.** When a rule's avg net is far above its median (e.g. trailing stops), the average is carried by a few outlier runners — the *typical* trade is the median, which may still be negative. Such rules are high-variance and unreliable at this N.

**Slippage caveat:** target/stop/trailing fills are assumed exactly at the level. On thin low-float names, gaps blow through stops and you rarely fill a target cleanly, so real-world results for stop/trailing rules would be **worse** than shown here. The 2% haircut does not capture gap-through slippage.

_Not investment advice. In-sample/exploratory; a rule must be pre-registered (HYPOTHESES.md) and validated on post-registration picks before it means anything._
