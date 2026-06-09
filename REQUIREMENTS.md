# IgnitionScan — Requirements Document (for developer hand-off)

**Owner:** Josh
**Date:** June 3, 2026
**Status:** Prototype complete; seeking developer for production build + long-term maintenance
**Companion files:** `prototype/index.html` (working prototype), `prefire-style-scanner-blueprint.md` (cost/architecture/legal background)

---

## 0. How to read this

The prototype in `prototype/index.html` already works out the **features, UI, scoring logic, and data flow**. Open it in any browser — it runs on bundled sample data, and pulls live quotes if you paste a free Financial Modeling Prep (FMP) API key on the Watchlist tab.

The developer's job is **not** to invent the product. It is to take this validated prototype and turn it into a maintainable, production-grade service: real data pipeline, persistence, scheduled jobs, auth/billing, and ongoing upkeep. This document defines what "production-grade" means and where the prototype intentionally stubs things.

The product is positioned as **educational** (an impersonal, objectively-screened watchlist published on a schedule). That framing drives several hard requirements below — they are not optional polish.

---

## 1. Product summary

A daily pre-market screener that ranks low-float, high-volatility US equities by a transparent published score and delivers an educational watchlist to subscribers at 7:30am ET. It logs every pick before the open and grades all of them (wins and losses) after 5 trading days, publicly.

**Surfaces (all built in the prototype):**

1. **Overview / landing** — value prop, pricing tiers ($0 / $99 early / $199 public), waitlist CTA, disclaimer.
2. **Watchlist** — today's ranked screen; click a row for the per-ticker scoring breakdown ("why it screened").
3. **How scoring works** — the published formula and component weights.
4. **Track record** — blended win rate, win rate by tier, and every logged pick with WIN/MISS.

---

## 2. Scope of this engagement

**In scope (production build):**

- Replace the in-browser data fetch with a server-side ingest pipeline + database.
- Full-universe screening (not just the seed list of 16 tickers).
- Real public-float and short-interest data (not shares-outstanding as a proxy).
- Two scheduled jobs: morning scan (~6:45am ET) and evening grader (~5pm ET).
- Subscriber auth + Stripe billing + paywall gating.
- Email + Discord delivery at 7:30am ET.
- Hosting, monitoring, and a maintenance retainer.

**Out of scope (for now):** trade execution, brokerage integration, personalized/portfolio-aware features (these would change the regulatory posture — see §7).

---

## 3. Functional requirements

### 3.1 Universe & screening
- **FR-1** Each trading morning, screen the full US small-/micro-cap universe, filtering to: price within `[$0.50, $10]` (configurable) and public float `< 50M shares` (configurable).
- **FR-2** Compute the four scoring inputs per ticker: float, RVOL (today/pre-market volume ÷ average volume), gap % (vs prior close), price-band fit.
- **FR-3** Compute the 0–100 IgnitionScan score and tier (A≥75, B≥60, C≥45, D<45) using the exact formula in the prototype (`scoreQuote()` in `index.html`). Weights are config-driven and must sum to 1.
- **FR-4** Assign each pick a **watch level** = screen price × (1 + 0.20), configurable.
- **FR-5** Persist every pick at scan time with: date, ticker, score, tier, all four raw inputs, all four component sub-scores, screen price, watch level. **Picks are immutable once written** (see FR-12).

### 3.2 Scoring transparency
- **FR-6** The published formula and weights shown on "How scoring works" must be generated from the same config that drives scoring (single source of truth — no hand-maintained copy that can drift).
- **FR-7** The per-ticker "why it screened" breakdown must show each input, its sub-score, and the weighted result.

### 3.3 Performance grader
- **FR-8** A daily job grades picks that are exactly 5 trading days old: record max gain over the window and WIN (reached watch level) / MISS.
- **FR-9** The track-record page shows the **blended win rate across all picks including misses**, plus win rate broken out by tier and by score band. No "top 5 only" view without the blended number alongside.
- **FR-10** Show best calls and worst misses side by side.

### 3.4 Delivery & access
- **FR-11** 7:30am ET push to subscribers via email and Discord. Content is **identical for every subscriber** (no per-user tailoring — see §7).
- **FR-12** Live watchlist is gated to paying subscribers (Stripe). The track-record and methodology pages are **public** (marketing + trust).
- **FR-13** Free tier sees the prior day's screen + full public track record.

### 3.5 Compliance surface
- **FR-14** The educational disclaimer (text in prototype) renders on every page, every email, and every Discord post.
- **FR-15** No feature anywhere offers personalized or portfolio-aware advice, and no "DM us for picks" style CTA.

---

## 4. Prototype: live vs. stubbed (read carefully)

| Element | Prototype behavior | Production requirement |
|---|---|---|
| Quotes (price, gap, volume, avg volume) | **Live** via FMP `/quote` (free tier) for 16 seed tickers, with sample fallback | Server-side pull for the **full** universe; cache; handle rate limits |
| Float | **Approximated** from `sharesOutstanding` in the FMP quote | Use **true public float** (paid data source) + FINRA short interest. Shares outstanding ≠ float and will mis-score. |
| Universe | Hard-coded 16-ticker seed list | Full-market screen |
| Performance data | **Worked sample** (30 graded picks) so the grading logic is visible | Generated by the live grader job from real logged picks |
| Persistence | None (in-browser only) | Postgres (or equiv.); immutable picks table |
| Auth / billing | None | Stripe + auth provider |
| Scheduling | None (runs on page load) | Cron jobs (morning scan, evening grader) |

**Key correctness note:** the single biggest data-quality risk is float. The prototype uses shares-outstanding as a stand-in so the UI is demoable; production must source real float or the screen will surface wrong names. Validate any float feed against a few known low-float tickers before trusting it.

---

## 5. Non-functional requirements

- **NFR-1 Reliability:** morning scan must complete and deliver before 7:30am ET; alert on failure. Grader must be idempotent (safe to re-run).
- **NFR-2 Data integrity:** picks table append-only/immutable; grading writes outcomes but never edits the original pick row.
- **NFR-3 Cost:** keep pre-revenue infra under ~$100/mo (see blueprint §11 stack: FMP + Polygon + FINRA + Supabase/Render + Vercel + GitHub Actions). Real-time intraday data is explicitly deferred.
- **NFR-4 Secrets:** API keys server-side only — never shipped to the browser (the prototype embeds a key for demo convenience; production must not).
- **NFR-5 Maintainability:** config-driven scoring/filters; documented data adapters so a data vendor can be swapped without touching UI.
- **NFR-6 Observability:** logging + uptime monitoring on both jobs and the API; basic admin view of today's run.

---

## 6. Suggested tech (from blueprint — developer may propose alternatives)

Python (pandas) for jobs · Next.js on Vercel for web · Postgres/Supabase · Stripe · GitHub Actions or Render cron · Resend (email) · Discord webhook. Data: Polygon Starter ($29/mo) for consolidated quotes, FMP (~$19/mo) for fundamentals/float, FINRA (free) for short interest.

---

## 7. Regulatory constraints the build must respect

The product relies on the **publisher's exclusion** to the Investment Advisers Act (*Lowe v. SEC*, 1985; reaffirmed for online publications in 2024). To stay inside it, the implementation must keep the publication:

1. **Impersonal** — identical content to all subscribers; no personalization, portfolio awareness, or per-user advice (FR-11, FR-15).
2. **Regular** — fixed daily schedule.
3. **Bona fide / disinterested** — genuine screening, not promotion; disclose operator positions; never accept payment to feature a ticker.
4. **Non-advisory in tone** — "screened on these objective criteria," never "buy this."

These are wired into the requirements above. **A securities attorney must review site copy, disclaimers, and Terms before charging subscribers** — this is a gating item in the launch plan, not a nicety. Adding execution, personalization, or "contact us for individual guidance" can void the exclusion.

---

## 8. Acceptance criteria

1. Morning job screens the full universe, scores it with the published formula, and writes an immutable pick set before 7:30am ET.
2. Evening grader grades 5-day-old picks automatically and never mutates original rows.
3. Track-record page shows blended all-picks win rate (incl. misses) plus by-tier and by-score-band breakdowns, matching the prototype's layout.
4. Float and short interest come from real sources, validated against known tickers.
5. Stripe paywall gates the live watchlist; methodology + track record remain public.
6. Disclaimer renders on every page, email, and Discord post; no personalized-advice surface exists.
7. API keys are server-side only.
8. Both jobs have failure alerting and basic monitoring.

---

## 9. Recommended launch sequencing (important)

Build and run the **performance tracker on real data for 6–8 weeks before turning on billing.** The single worst position to launch from is a paywall over an empty/all-"Pending" track record (the incumbent's current problem). Accumulate a genuine, public record first; then sell against it.

---

*This requirements document and the prototype are technical/strategic artifacts, not legal or financial advice. Obtain securities-law counsel before charging subscribers.*
