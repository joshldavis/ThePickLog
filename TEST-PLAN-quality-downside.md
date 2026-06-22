# Test Plan — Does the Quality Lens predict shallower drawdown?

**Owner:** Josh · **Drafted:** 2026-06-16 · **Status:** pre-registration draft (not yet run)
**Settles:** STRATEGY-advancing.md §6 Finding B · **Feeds:** VALIDATION-PLAN.md Part 3
**Companion code:** `quality_lens.py`, `backtest_quality.py`, `fundamentals_cache.json`

The 2026-06-16 first run could not settle §1.1: the grade was constant per ticker (effective
N=14), the universe was the 16-ticker hand-picked seed, and fundamentals were point-in-time
*current* (look-ahead). This plan removes all three threats so the result actually means
something. **Pre-register the hypothesis and the success bar before running** — that is the
whole point of the verifiability standard; a claim chosen after seeing the data is not evidence.

---

## 1. The hypothesis (pre-registered, falsifiable)

> **H1 (downside filter).** Higher Quality-Lens grades have *shallower* drawdown.
> Median MAE(Green+Yellow) is less negative than median MAE(Red+Black).
>
> **H2 (rug protection).** Higher grades rug less often.
> P(MAE < −30% | Green+Yellow) < P(MAE < −30% | Red+Black).

Pre-registered **null** to beat: no difference, or the inverse (what the thin first run showed).
We also pre-commit to reporting **H0-consistent and inverse results equally** — no quiet redefinition
of "win," no post-hoc subgroup hunting. State the headline metric (median MAE) before the run.

### Success bar (decides whether the headline claim changes)
The claim *"we tell you which movers won't gut you"* is **earned only if all four hold:**

1. Direction: H1 **and** H2 both hold in the hypothesized direction.
2. Magnitude: median-MAE gap ≥ **5 percentage points** (Green+Yellow vs Red+Black).
3. Power: **≥ 200 graded picks**, **≥ 30 per grade bucket**, and — the fix that matters —
   **≥ 25 distinct tickers per bucket** (so the result isn't 2 names pseudo-replicated).
4. Robustness: holds on a **held-out time split** (train on first half of the window, confirm
   on the second) — Messick external validity, not just in-sample fit.

Miss any one → the quality→drawdown claim stays **out of user-facing copy**; quality remains a
"is this a real business?" descriptor only, and messaging leans on Finding A (inverse momentum).

---

## 2. The three fixes

| Threat (first run) | Fix |
|---|---|
| **Selection bias** — 16 hand-picked seeds (`CONFIG["UNIVERSE"]`) | Screen the **full low-float universe** historically (FR-1), not a curated list. |
| **Look-ahead** — current FMP/EDGAR filings applied to past dates | **As-of-pick-date fundamentals**: grade off the latest 10-K/10-Q **filed strictly before** the pick date. |
| **Effective N = 14** — grade constant within a ticker | Wider universe → many distinct tickers per bucket; **cluster stats by ticker** so within-ticker picks aren't counted as independent. |

---

## 3. Data pipeline

Builds on `backtest.py` (same scoring engine, same MAE/return window, same 2% haircut — single
source of truth). Three new pieces:

**3a. Historical universe (replaces the seed list).**
Reconstruct the screen over a broad universe of US sub-$10, low-float names using daily bars
(`yfinance`, already the backtest's source). For each trading day, apply the live FILTERS
(`price 0.50–10`, `float ≤ 50M`) and the same RVOL-proxy (prior-day volume / 20-day avg, known
at the open — no look-ahead). Start from a liquidity-filtered small-cap list (e.g. all NASDAQ/
AMEX common stock under the price/float ceilings) rather than 16 names.
*Known residual limit:* historical **float** is not freely point-in-time; flag it the same way
`backtest.py` already flags current-float reuse, and treat float as the weakest input.

**3b. As-of-date Quality grade (the core new work — the long pole).**
Today `/api/edgar` returns the *current* parsed statements. For point-in-time:
- Pull the company's filing index from SEC EDGAR submissions JSON
  (`https://data.sec.gov/submissions/CIK##########.json`, free, no key).
- For a pick on date *D*, select the **most recent 10-K/10-Q with `filingDate ≤ D`**, and the
  prior years available as of *D* (for CAGR/dilution/consistency, which need history).
- Parse those filings into the same statement shape `quality_lens.assemble_fundamentals`
  already expects (revenue, OCF/FCF, shares, debt, equity, current A/L), then
  `compute_quality` → grade. The port is already faithful (JS-style rounding verified), so the
  as-of grade matches what the site *would have shown that day*.
- Sector/industry are quasi-static → current profile is acceptable; **marketCap must be
  as-of-date** (as-of shares × historical close) for the valuation sub-score.

**3c. Outcomes.** Unchanged from `backtest.py`: entry = pick-day open, MAE/MFE over the same
5-trading-day window, return net of the 2% haircut, WIN = positive net.

Output: extend `backtest_quality.csv` with an `as_of_grade` column; keep it **gitignored**
(regenerable, not a track record — same rule as `backtest_results.csv`).

---

## 4. Statistics (respect the clustering)

The first run's headline error was treating 2,124 correlated rows as independent.

- **Unit-aware reporting:** report both per-pick and **per-ticker** (collapse each ticker to its
  median MAE, then compare buckets — the honest unit when grades cluster).
- **Significance:** bootstrap **resampling tickers, not rows** (cluster bootstrap), for a CI on
  the median-MAE gap and the rug-rate gap. A gap whose 95% CI crosses zero fails bar #1.
- **Confounder check:** quality correlates with sector and size. Re-test within sector buckets
  (e.g. biotech-only, where "Too Hard" concentrates) so we're not just re-discovering
  "biotech rugs harder." Report the gap **conditional on momentum tier** too, so quality earns
  credit only beyond what Finding A already explains.

---

## 5. Phased build (tractable first, full later)

- **Phase 1 — kill look-ahead on a widened universe (≈ the high-value, achievable step).**
  Keep `yfinance` outcomes; add the as-of-date EDGAR grader (3b) to ~150–300 names. This alone
  fixes the look-ahead threat and lifts distinct-ticker N enough to test bar #3. Likely 1–2
  focused sessions; the EDGAR submissions parser is the bulk of it.
- **Phase 2 — true full-market screen (3a at scale).** Point-in-time float is the blocker;
  needs a paid fundamentals/float history feed (revisit the FMP-paid note in `ignitionscan.py`).
  Do only if Phase 1 is directionally promising.
- **Forward track stays sacred.** None of this touches `picks.csv`/`outcomes.csv`. The backtest
  is variable-selection only and stays labelled in-sample (SYNTHESIS §1.2). The public claim is
  still backed solely by the immutable forward log.

---

## 6. Decision rule (what each outcome does to the product)

- **All four bars clear (and hold out-of-sample):** reframe the headline to the downside-filter
  claim — *"we don't tell you what moons; we tell you which movers won't gut you"* — and surface
  the as-of grade × drawdown table as the proof. This is the §1.1 upgrade.
- **Direction holds but underpowered / fails the held-out split:** keep building the forward log;
  re-run when N grows; **do not ship the claim yet.**
- **Null or inverse on valid data:** drop quality-as-downside-protection entirely; keep the
  Quality Lens as a "real business?" descriptor, and make **Finding A (inverse momentum)** the
  spine of the messaging instead.

---

*Pre-registration draft — strategic/technical plan, not legal or financial advice. The model
stays unvalidated until VALIDATION-PLAN Part 3 clears; obtain securities counsel before charging
(gate G4). Backtest results are in-sample and never a performance claim.*
