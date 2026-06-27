# IgnitionScan — exit-rule study · 2026-06-27

Daily-resolution replay of **106** graded picks (of 106). Conservative same-day tie (stop fills first); 2% cost haircut; fills at level. **In-sample / exploratory** — a chosen rule must be pre-registered and validated forward.

_Bar provenance: 41 from the immutable grade-time record (paths.csv), 65 re-fetched (picks that predate path capture). Grade-time paths are reproducible from committed data; re-fetched bars can drift if Yahoo revises history, so they converge to the immutable source as the record matures._

| exit rule | n | win% | avg net/trade | median |
|---|---|---|---|---|
| Same-day close (current) | 106 | 37% | -2.8% | -3.0% |
| Hold to 5d close | 106 | 26% | -6.2% | -9.5% |
| Target +10% | 106 | 62% | -2.8% | +8.0% |
| Target +15% | 106 | 50% | -3.3% | +1.3% |
| Target +20% | 106 | 44% | -2.7% | -5.8% |
| Target +30% | 106 | 36% | -3.2% | -7.2% |
| Stop -10% | 106 | 17% | -5.3% | -12.0% |
| Stop -15% | 106 | 21% | -6.5% | -17.0% |
| H-EX2 +10% target / -20% stop [registered 2026-06-24] | 106 | 56% | -4.0% | +8.0% |
| Target +20% / Stop -10% | 106 | 28% | -3.3% | -12.0% |
| Target +15% / Stop -10% | 106 | 33% | -3.6% | -12.0% |
| Target +20% / Stop -15% | 106 | 34% | -4.0% | -16.6% |
| Trailing 15% ⭐ | 106 | 30% | +12.2% | -7.8% |
| Trailing 20% ⭐ | 106 | 29% | +9.0% | -10.1% |

⭐ = avg net/trade at least +2pp better than the current same-day-close exit.

**Read the median, not just the mean.** When a rule's avg net is far above its median (e.g. trailing stops), the average is carried by a few outlier runners — the *typical* trade is the median, which may still be negative. Such rules are high-variance and unreliable at this N.

**Slippage caveat:** target/stop/trailing fills are assumed exactly at the level. On thin low-float names, gaps blow through stops and you rarely fill a target cleanly, so real-world results for stop/trailing rules would be **worse** than shown here. The 2% haircut does not capture gap-through slippage.

_Not investment advice. In-sample/exploratory; a rule must be pre-registered (HYPOTHESES.md) and validated on post-registration picks before it means anything._
