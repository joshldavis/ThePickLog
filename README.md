# IgnitionScan logger/grader — how it runs

A personal, paper-trading tool. Logs picks before the open and grades them honestly after 5 trading days. **Data source: Yahoo Finance (`yfinance`) — no API key needed.** It covers low-float / small-cap names (FMP's free tier does not).

> **Governing standard:** *"Can a stranger pull the raw data and verify that every claim is true?"*
> Every number here is meant to be re-derivable from the committed CSVs. The rules behind that
> are in **[`PRINCIPLES.md`](PRINCIPLES.md)** (read first); a map of all docs is in
> **[`DOCS.md`](DOCS.md)**.

## You don't have to run anything — it's automated
This repo includes a GitHub Action (`.github/workflows/ignitionscan.yml`) that runs on GitHub's servers:
- **scan** every weekday morning (~7:30am ET)
- **grade** every weekday evening (~5pm ET)

It commits the results (`picks.csv`, `outcomes.csv`) straight back into the repo. Your computer doesn't need to be on, and there's no key or secret to manage.

You can also trigger a run by hand: repo → **Actions** tab → **IgnitionScan daily** → **Run workflow** (pick `scan` or `grade`).

## Running it locally (optional)
```bash
pip install yfinance
python3 ignitionscan.py scan      # log today's picks (immutable)
python3 ignitionscan.py grade     # grade picks that are 5 trading days old
python3 ignitionscan.py report    # tier table: do A's beat B's beat C's?
python3 ignitionscan.py demo      # offline sample run, writes nothing
```

## What it writes
- **picks.csv** — one append-only row per pick. This file *is* the track record; never edit it by hand.
- **outcomes.csv** — grading results, keyed to each pick_id.

## The honest grading metric
Entry assumed at the regular-session **open** of the pick day, exited same-day close (primary) or +5 close, every realized return **net of a 2% friction haircut** for the wide spreads on low-float names. `mfe_5d` (best-case intraday move) and `mae_5d` (worst drawdown) are recorded too — `mfe` is informative but NOT an achievable return, and `mae` is the risk side the prototype hides.

## Known v0 limitations (see VALIDATION-PLAN.md)
- **Universe** is a fixed 16-ticker seed list, not a full-market screen.
- **Short interest / catalyst / dilution** columns are captured-but-blank — instrument now, score later.
- Trading-day math ignores market holidays (fine for v0).
- **Yahoo is an unofficial source** and can occasionally throttle a cloud run, so a day may be skipped now and then. For a real product, move to a paid feed (FMP Starter / Polygon) — see the blueprint.

## Documentation
- **[`PRINCIPLES.md`](PRINCIPLES.md)** — the validity principles (canonical; read first).
- **[`DOCS.md`](DOCS.md)** — map of every doc and where it fits.
- **[`ROADMAP.md`](ROADMAP.md)** — what's done, next, and parked.
- **[`VALIDATION-PLAN.md`](VALIDATION-PLAN.md)** — pick-log spec, grading rule, validation bar.
- **[`HYPOTHESES.md`](HYPOTHESES.md)** — pre-registered, dated rules judged out-of-sample.
- **[`AUDIT_LOG.md`](AUDIT_LOG.md)** — dated weekly verifiability audits (claims == data).

This is a personal research tool, not investment advice. The model is unvalidated until `report` clears the bar in VALIDATION-PLAN.md.
