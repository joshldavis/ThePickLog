# IgnitionScan — exit-rule study · 2026-06-23

Daily-resolution replay of **65** graded picks (of 65). Conservative same-day tie (stop fills first); 2% cost haircut; fills at level. **In-sample / exploratory** — a chosen rule must be pre-registered and validated forward.

| exit rule | n | win% | avg net/trade | median |
|---|---|---|---|---|
| Same-day close (current) | 65 | 40% | -2.8% | -3.6% |
| Hold to 5d close | 65 | 28% | -3.2% | -9.3% |
| Target +10% | 65 | 63% | -1.8% | +8.0% |
| Target +15% | 65 | 54% | -1.2% | +13.0% |
| Target +20% ⭐ | 65 | 46% | -0.7% | -2.1% |
| Target +30% ⭐ | 65 | 42% | +0.1% | -5.8% |
| Stop -10% | 65 | 18% | -3.3% | -12.0% |
| Stop -15% | 65 | 23% | -4.0% | -17.0% |
| Target +20% / Stop -10% | 65 | 26% | -3.5% | -12.0% |
| Target +15% / Stop -10% | 65 | 32% | -3.6% | -12.0% |
| Target +20% / Stop -15% | 65 | 34% | -3.2% | -12.9% |
| Trailing 15% ⭐ | 65 | 32% | +20.5% | -10.0% |
| Trailing 20% ⭐ | 65 | 31% | +17.5% | -7.5% |

⭐ = avg net/trade at least +2pp better than the current same-day-close exit.

**Read the median, not just the mean.** When a rule's avg net is far above its median (e.g. trailing stops), the average is carried by a few outlier runners — the *typical* trade is the median, which may still be negative. Such rules are high-variance and unreliable at this N.

**Slippage caveat:** target/stop/trailing fills are assumed exactly at the level. On thin low-float names, gaps blow through stops and you rarely fill a target cleanly, so real-world results for stop/trailing rules would be **worse** than shown here. The 2% haircut does not capture gap-through slippage.

_Not investment advice. In-sample/exploratory; a rule must be pre-registered (HYPOTHESES.md) and validated on post-registration picks before it means anything._
