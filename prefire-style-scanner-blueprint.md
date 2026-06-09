# Low-Float Scanner — Developer Hand-off Blueprint

**Prepared for:** Josh
**Date:** June 3, 2026
**Purpose:** A build-ready spec for a subscription stock-scanner product in the mold of Prefire (prefirescan.com), designed around three constraints you set: (1) hand to a developer to build, (2) under $100/mo data + hosting before you have subscribers, (3) framed as **educational** — data and screens, not personalized buy/sell recommendations.

> This is a technical and business blueprint, not legal advice. The regulatory section flags where a securities lawyer is required before you charge anyone.

---

## 1. What the product is

A daily, pre-market stock **screener** that ranks low-float, high-volatility tickers by a set of transparent, published criteria and delivers the ranked list to subscribers as an educational watchlist. It is explicitly **not** a signal service telling people what to buy.

The defensible version of this product competes on **honesty and a real, auditable track record** — precisely the thing Prefire's own performance page lacks (as of launch, every one of their 60 logged setups reads "Pending," and the two tickers they advertise as wins, $BJDX and $MASK, scored low on their own model and show "Pending" results). If you log every pick before the move and grade it transparently after, you have the one thing the incumbents fake.

---

## 2. Positioning & the honest differentiator

The "ML trained on 830 explosions" claim is marketing. Predicting which sub-$5 low-float stock explodes is dominated by noise and manipulation; backtests on it overfit badly. **Do not build the business on a promise of predictive accuracy you can't keep.** Build it on:

- **Transparency** — publish the exact screen criteria. "We rank by relative volume, float size, and gap, here's the formula" beats "proprietary AI" for trust and for staying on the right side of the educational framing.
- **A real track record** — every pick timestamped before market open, outcome graded automatically after N days, *all* picks shown (winners and losers), blended hit-rate visible. This is the actual moat and it's cheap to build.
- **Education** — explain *why* a setup screened (e.g., "float 3.2M, RVOL 8x, gapped 18% pre-market") so subscribers learn the pattern rather than blindly follow.

---

## 3. Legal framing — the constraint that shapes the whole product

You chose the **educational / no specific buy-sell** framing. That aligns with the **publisher's exclusion** to the Investment Advisers Act of 1940, established in *Lowe v. SEC* (1985) and recently reaffirmed for online publications (a 2024 ruling found Seeking Alpha protected, and held that email alerts and news-driven updates still count as "regular" circulation).

To stay inside the exclusion, the product must be:

1. **Impersonal** — the same content goes to every subscriber. No tailoring to an individual's portfolio, risk tolerance, or account. No "what should *I* buy" responses.
2. **Bona fide and disinterested** — genuine analysis, not promotional. Do **not** publish a pick while holding a position you're trying to pump, and disclose any positions. Don't take payment to feature tickers.
3. **Regular** — published on a fixed schedule (your 7:30am ET daily cadence satisfies this).
4. **No calls to personal guidance** — avoid "DM me for personalized picks," which can break the exclusion.

Design implications baked into the spec below: framing is "screened on these objective criteria," every output carries a disclaimer, there is no per-user customization, and there is no chat feature offering individualized advice. **Even with all this, get a securities lawyer to review the site copy and Terms before charging** — the exclusion is fact-specific and the words you use matter. Budget a one-time legal review (typically a few hundred to low-thousand dollars for a focused engagement).

---

## 4. System architecture

```
                 ┌─────────────────────────────────────────────┐
                 │  SCHEDULER (cron, ~6:45am ET daily)          │
                 └───────────────┬─────────────────────────────┘
                                 │ triggers
                                 ▼
   ┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
   │ Market data  │────▶│  INGEST + SCORE   │────▶│  DATABASE         │
   │ APIs         │     │  (Python job)     │     │  (picks, scores,  │
   │ (prices,     │     │  - pull universe  │     │   outcomes)       │
   │  float, SI)  │     │  - filter         │     └────────┬─────────┘
   └──────────────┘     │  - score & rank   │              │
                        │  - write watchlist│              │
                        └──────────────────┘              │
                                 │                         │
              ┌──────────────────┼─────────────────────────┤
              ▼                  ▼                          ▼
      ┌──────────────┐   ┌──────────────┐          ┌──────────────────┐
      │ Web dashboard│   │ Email / Discord│        │ OUTCOME GRADER    │
      │ (watchlist + │   │ push (7:30am)  │        │ (cron, daily 5pm; │
      │  performance)│   └──────────────┘          │  grades picks     │
      └──────────────┘                             │  N days later)    │
                                                   └──────────────────┘
```

Two scheduled jobs (morning scan, evening grader), one database, one ingest/score service, one web app, one notifier. Deliberately small.

---

## 5. Data sources & the sub-$100/mo stack

The hard part of this budget is that **float and short-interest data are exactly the fields that are expensive or low-quality at the bottom tier.** Plan for "good enough for an educational screen," not institutional precision.

| Need | Recommended source | Cost | Notes |
|---|---|---|---|
| Prices, quotes, minute aggregates, pre-market | **Polygon.io Starter** | $29/mo | Unlimited calls, 15-min delayed. Fine for an educational pre-market screen. Free tier (5 calls/min) works for an MVP. |
| Float / shares outstanding / fundamentals | **Financial Modeling Prep** | ~$19–22/mo | Has a Company Share Float / All Shares Float endpoint. Quality is decent, not perfect — verify against a few known names. |
| Short interest | **FINRA bi-monthly short interest** | **Free** | Official, downloadable, but only published ~twice a month with a lag. Good enough for a slow-moving input. |
| Database | **Supabase** or **Postgres on Render** | Free–$7/mo | Free tier is ample at launch. |
| Hosting (web + jobs) | **Vercel** (web) + **GitHub Actions cron** (jobs) | Free–$7/mo | GitHub Actions free minutes cover two short daily jobs. |
| Email delivery | **Resend** or **Mailgun** free tier | Free to start | Few thousand emails/mo free. |
| Discord delivery | **Discord webhook** | Free | One HTTP POST per push. |

**Realistic pre-revenue total: ~$48–60/mo** (Polygon $29 + FMP ~$19 + hosting/DB near-free). Comfortably under $100.

**What you sacrifice at this tier:** true real-time (no-delay) quotes, intraday short-interest, and clean borrow/locate data all cost materially more (hundreds/mo). For an *educational pre-market watchlist* you don't need them. If you later sell real-time intraday alerts, data cost jumps and so does the regulatory scrutiny — note for v2, not launch.

---

## 6. The scoring engine (transparent, not "AI")

Build a documented, deterministic score from cheap inputs. Example components (tune the weights with historical data):

- **Float size** — smaller float scores higher (e.g., < 5M shares is the sweet spot).
- **Relative volume (RVOL)** — pre-market or recent volume vs. the stock's own average.
- **Gap %** — pre-market gap from prior close.
- **Price band** — typically $0.50–$10 for this strategy; weight or filter.
- **Recent volatility / ATR** — already-volatile names continue to move.
- **Catalyst flag (optional, v2)** — news/PR in the last 24h via a headlines endpoint.

Output a 0–100 score and a clear tier (A/B/C). **Publish the formula.** Transparency is both a trust feature and part of staying "educational" rather than "advisory." Resist the urge to add an opaque ML layer at launch — it adds cost, breaks transparency, and doesn't demonstrably improve results on this problem.

---

## 7. Performance tracking — your actual moat

This is the cheapest part to build and the most valuable. Spec:

- At scan time, **persist every pick** with: date, ticker, score, tier, the input values, and a defined "watch level" (e.g., the price that would count as the move triggering).
- An evening grader job, run daily, looks back at picks that are N trading days old (5 is a reasonable default) and records: max gain over the window, whether it hit the watch level (WIN/MISS), and the outcome.
- The public performance page shows the **blended, all-picks win rate** — not a cherry-picked top 5. Include the misses prominently. Show win rate by tier and by score band so subscribers can judge which signals actually work.
- Never retroactively edit a logged pick. Immutability is the whole point.

Done honestly, this page is your single best marketing asset and the thing no competitor in this space is willing to show.

---

## 8. Delivery

- **Web dashboard** — today's ranked watchlist (gated to subscribers), plus the public performance page (open, for marketing). Add a plain-language "why it screened" line per ticker.
- **7:30am ET push** — email and/or Discord. Keep it impersonal and identical for all subscribers (publisher-exclusion requirement).
- **Disclaimer on every surface** — site footer, every email, every Discord post: educational/informational only, not investment advice, not a recommendation to buy or sell, you may hold positions, past performance ≠ future results, trading penny stocks carries high risk of loss.

---

## 9. Recommended tech stack (for the developer)

- **Language for jobs:** Python (pandas for the screen; clean and hireable).
- **Web app:** Next.js (React) on Vercel — same stack Prefire uses; lots of devs know it.
- **DB:** Postgres (Supabase managed, free tier).
- **Auth + billing:** Stripe for subscriptions; Supabase Auth or Clerk for login. Stripe handles the paywall and gating.
- **Scheduling:** GitHub Actions cron (free) or Render cron jobs.
- **Notifications:** Resend (email) + Discord webhook.

All of this is mainstream and within a competent full-stack freelancer's wheelhouse.

---

## 10. Phased build plan

**Phase 0 — Legal & setup (before charging):** lawyer reviews framing/Terms/disclaimers; register data-API accounts; set up Stripe. *No code dependency; do this in parallel.*

**Phase 1 — MVP (the honest scanner), ~2–4 weeks freelance:**
- Ingest job pulls universe + float, applies filters, scores, writes to DB.
- Public web page shows today's watchlist + a performance page (even if early data is thin).
- Outcome grader job running daily.
- Manual/free access only — no paywall yet. Goal: accumulate a *real* track record for 4–8 weeks before charging a cent.

**Phase 2 — Productize, ~2–3 weeks:**
- Stripe paywall, subscriber auth, gated watchlist.
- 7:30am email + Discord push.
- Polished performance page with blended win rate by tier/score.

**Phase 3 — Optional v2 (only if traction):**
- News/catalyst input, intraday alerts (higher data cost + more regulatory care), backtesting tooling, weight-tuning.

**Critical sequencing note:** launch the performance tracker *before* you launch the paywall. Selling subscriptions on day one with zero track record is exactly the credibility hole Prefire is in. Your pitch should be "here's 8 weeks of every pick we made, graded — judge for yourself," then charge.

---

## 11. Cost summary

| Phase | Monthly cost | One-time |
|---|---|---|
| MVP / pre-revenue | **~$50–60/mo** (data + near-free hosting) | Legal review (few hundred–low thousands); freelance build (see below) |
| At ~100 subscribers | ~$70–120/mo (email volume, maybe DB tier) | — |
| v2 real-time intraday | $300+/mo (real-time data feed) | Additional legal review |

**Freelance build estimate (rough):** a competent full-stack freelancer could deliver Phase 1+2 in roughly 4–7 weeks. At typical US freelance rates that's a meaningful one-time cost — get fixed-bid quotes against this spec rather than hourly.

---

## 12. Risks & honest caveats

- **The edge may not exist.** Be prepared for the blended win rate to be mediocre. If it is, that's information — don't paper over it. A modest but *honest* hit rate with great education can still be a viable product; a fake one is a liability.
- **Data quality at this tier is the weak link.** Validate float numbers against a couple of known names before trusting them; bad float data produces embarrassing picks.
- **The category attracts scrutiny.** Penny-stock promotion is a known enforcement area. The educational framing + disclaimers + disinterested conduct (no pumping your own bags) are what keep you clean. Take it seriously.
- **Churn is brutal in trading products.** Most subscribers quit within months. The honest track record is also your best retention tool.
- **You are not, and this product does not make you, a registered investment adviser** under the publisher's exclusion *only if* you stay impersonal, regular, and disinterested. The moment you offer personalized advice, the exclusion can evaporate.

---

## 13. What to hand the developer

Give them: this document, the chosen data vendors (Polygon + FMP + FINRA), the scoring component list (section 6), the performance-tracking spec (section 7), and these acceptance criteria:

1. Morning job produces a ranked, filtered watchlist written to the DB with all input values persisted.
2. Every pick is immutable once written.
3. Evening grader job grades N-day-old picks automatically and never edits originals.
4. Public performance page shows blended all-picks win rate, including losers, broken out by tier and score band.
5. Disclaimer rendered on every page, email, and Discord post.
6. Stripe paywall gates the live watchlist; the performance page stays public.
7. No feature anywhere offers per-user personalized advice.

---

*Reminder: this blueprint is technical and strategic guidance, not legal or financial advice. Have a securities attorney review your specific copy and Terms before charging subscribers.*
