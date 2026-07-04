# Accountability wedge — "grade the calls, not just our own"

**Status:** DESIGN ONLY — nothing published, nothing about named third parties is live.
**Drafted:** 2026-06-22 · **Gate:** requires Josh + legal review before ANY publication (see §4).
**Source:** STRATEGY-advancing.md §2.1 (turn the grader outward) — the category-level wedge.

The moat isn't the watchlist; it's a machine that grades calls **honestly and
immutably**. §2.1 says point that same machine at *other people's public calls*. This
doc specifies how to do that without tripping the legal posture or the verifiability
standard — and why it must stay staged until you're back.

## 1. The idea, precisely

Take a *public, attributable, time-stamped* stock call ("X said buy $TICK on DATE"),
run the **exact same immutable grading** the site uses on its own picks (entry = stated
date's open, MAE/return over the same window, same cost haircut, win = positive net),
and publish the graded outcome with a link to the original source. Same method, same
math, applied evenhandedly — including to ourselves.

Why it's strong: it's product (a feature), moat (no competitor can copy it without
exposing their own record), and marketing (social proof + authority) at once. It aims
the "help me not get burned" job at the whole category.

## 2. The hard part is NOT engineering — it's sourcing + liability

The grading engine already exists (`ignitionscan.py` grade logic + `backtest.py`
window). The genuinely hard/sensitive parts:

- **Attribution must be airtight.** Every graded call needs a permanent, public,
  timestamped source (a dated post/video/article URL). No screenshots, no hearsay,
  no paraphrase. If a stranger can't click through and confirm "they said this, on
  this date," it doesn't get graded. (This IS the verifiability standard applied to
  others.)
- **Method must be identical and pre-stated.** Same entry rule, window, haircut, and
  win definition as our own picks — published openly — so it can't be framed as
  cherry-picking. Grade our own calls in the same table.
- **Tone must be neutral and factual.** Report the math ("called $TICK on 6/2; 5-day
  net −18% after costs"), never editorialize, never imply fraud/intent. "Hall of
  Shame" framing from the blueprint is a LIABILITY in public form — keep it internal;
  publish as a neutral "Public Calls Scoreboard."
- **Legal exposure is real.** Grading named individuals/firms invites defamation and
  publicity complaints even when accurate. This needs the same securities-counsel pass
  as the billing question (gate G4) BEFORE going public.

## 3. Safe build plan (what can be built vs. published)

**Can build now (internal, unpublished):**
1. `calls.csv` schema — `call_id, source_name, source_url, published_date, ticker,
   direction, stated_date, captured_by, captured_at`. Immutable, append-only, like picks.csv.
2. A grader that reuses the existing window/haircut to produce `call_outcomes.csv`.
3. A *self-only* proof: grade ThePickLog's OWN past public statements with it, to
   prove the method works and is fair — zero third-party risk.

**Must NOT do without review:**
- Populate `calls.csv` with named third parties and publish it.
- Link or surface any third-party scoreboard on the live site.
- Any framing that implies wrongdoing.

## 4. Why this stays staged until Josh is back

Publishing graded claims about named people is exactly the kind of public, legally
sensitive, hard-to-reverse action that the verifiability + legal posture rules say
needs human + counsel sign-off. Autonomously shipping it would violate the project's
own north star. So during the away month this wedge advances only as **design + the
self-only proof**; the third-party scoreboard waits for:

1. Josh's explicit go-ahead on the concept + framing.
2. A securities/defamation counsel pass (folds into the existing G4 legal review).
3. A written, public methodology page (so the method is verifiable before any verdict).

## 5. First move when greenlit

Build the self-only proof (§3.3) first — it de-risks the engine and becomes the
"we grade ourselves the same way" credibility anchor that makes the third-party
scoreboard defensible. Then, only after §4 clears, seed a *small* set of
well-documented public calls and publish behind the methodology page.

---
*Design note, not legal or financial advice. No third-party content is collected or
published by this document. Obtain counsel before publishing graded claims about named
parties (gate G4).*
