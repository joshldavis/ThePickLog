# IgnitionScan — Documentation Map

Where everything lives and what it's for. **Start here**, then follow the arrow.

> **New to the repo?** Read [`PRINCIPLES.md`](PRINCIPLES.md) first (the rules that govern
> every claim), then [`README.md`](README.md) (how it runs), then [`ROADMAP.md`](ROADMAP.md)
> (what's next). Everything else is reference.

---

## Start here

| Doc | What it is |
|---|---|
| [`PRINCIPLES.md`](PRINCIPLES.md) | **The validity principles — canonical.** The verifiability standard and the five operating rules every change must pass. Read first. |
| [`README.md`](README.md) | How the tool runs: automated GitHub Actions, local commands, what it writes, the honest grading metric. |
| [`ROADMAP.md`](ROADMAP.md) | Current plan and guardrails. What's done, what's next in priority order, what's parked pending a Josh decision. |

## Validity & integrity (how claims are kept honest)

| Doc | What it is | Relationship |
|---|---|---|
| [`SYNTHESIS.md`](SYNTHESIS.md) | The three lenses behind the standard — Jobs to be Done × Influence × Messick construct validity. | The *why* under `PRINCIPLES.md` §4. |
| [`VALIDATION-PLAN.md`](VALIDATION-PLAN.md) | The pick-log column spec, the realizable grading rule, and the validation tables + go/no-go gates. | Operationalizes P3/P5; the data spec `PRINCIPLES.md` enforces. |
| [`HYPOTHESES.md`](HYPOTHESES.md) | Pre-registered rules, frozen with dates (filters H-F1–F4, H-SI, exit rule H-EX1). | Implements P2; the judge is the forward log. |
| [`AUDIT_LOG.md`](AUDIT_LOG.md) | Dated results of the weekly verifiability audit (claims == data). | Implements `PRINCIPLES.md` §3. |
| [`QA_REPORT.md`](QA_REPORT.md) | Code QA pass over the analysis/automation — the parts "don't fool yourself" depends on. Findings + fixes. | Guards P1/P4 against silent bugs. |

## Strategy & planning

| Doc | What it is | Relationship |
|---|---|---|
| [`STRATEGY-advancing.md`](STRATEGY-advancing.md) | The strategic layer: how the bet itself should change across model/product/marketing, each move named to a framework. | Sits above `IMPROVEMENTS-v0.3.md`; draws on `SYNTHESIS.md`. |
| [`IMPROVEMENTS-v0.3.md`](IMPROVEMENTS-v0.3.md) | Concrete v0.3 product moves (trust, brief, scoring validity, growth). | Turns `SYNTHESIS.md` into a build list. |
| [`TEST-PLAN-quality-downside.md`](TEST-PLAN-quality-downside.md) | Pre-registration draft: does the Quality Lens predict shallower drawdown? (Finding B). | Settles `STRATEGY-advancing.md` §6; feeds `VALIDATION-PLAN.md` Part 3. |
| [`PHASE2-SCOPE.md`](PHASE2-SCOPE.md) | Scope for the full-market, point-in-time test of Finding B (gated on a paid feed). | Follow-on to `TEST-PLAN-quality-downside.md`. Needs a spend + go/no-go. |
| [`WEDGE-accountability.md`](WEDGE-accountability.md) | Design-only accountability wedge. **Parked** — mostly moot under the personal-tool framing. | From `STRATEGY-advancing.md` §2.1. Needs legal review before any publication. |

## Reference & setup

| Doc | What it is |
|---|---|
| [`REQUIREMENTS.md`](REQUIREMENTS.md) | Original developer hand-off requirements (June 3 — historical product framing). |
| [`prefire-style-scanner-blueprint.md`](prefire-style-scanner-blueprint.md) | Build-ready spec / cost / architecture / legal background for a Prefire-style scanner. |
| [`ALPACA-TRADING-SETUP.md`](ALPACA-TRADING-SETUP.md) | How in-app Buy/Sell is wired to Alpaca **paper** trading via a server-side proxy. |
| [`AI-ASSISTANT-SETUP.md`](AI-ASSISTANT-SETUP.md) | Setup for the assistant backend + ticker drawer, built only on already-verifiable data. |

## Generated output (auto-written — don't hand-edit)

| Path | What it is |
|---|---|
| [`reports/LATEST.md`](reports/LATEST.md) | Weekly forward-log report (tiers, filters, integrity checks). From `weekly_report.py`. |
| [`reports/brief-LATEST.md`](reports/brief-LATEST.md) | Morning brief — impersonal, educational watchlist. |
| [`reports/exit-study-LATEST.md`](reports/exit-study-LATEST.md) | Exit-rule study (daily-resolution replay). From `exit_sim.py`. |
| `reports/forward-YYYY-MM-DD.md` | Dated report snapshots. |

## Key data & code (the canonical record)

| Path | What it is |
|---|---|
| `picks.csv` | **The track record.** Append-only, one row per pick, written before the outcome. Never edit by hand. |
| `outcomes.csv` | Grading results, keyed to each `pick_id`. |
| `paths.csv` | Grade-time daily OHLC path per pick (forward-only) so the exit study is reproducible from committed data. |
| `ignitionscan.py` | The scanner/logger/grader (`scan` / `grade` / `report` / `demo`). |
| `weekly_report.py` · `exit_sim.py` | Report + exit-study generators. |
| `.github/workflows/` | `ignitionscan.yml` (daily scan/grade) · `report.yml` (weekly report). |

---

## A note on framing drift

This project began as a **subscription product** spec and is now a **personal research
instrument** (no subscribers, no billing — see `ROADMAP.md`). Older docs — `REQUIREMENTS.md`,
`SYNTHESIS.md`, `VALIDATION-PLAN.md`, `IMPROVEMENTS-v0.3.md`, `prefire-style-scanner-blueprint.md`
— retain the product/subscriber language from that era and are kept as-is for the reasoning
they contain. The **validity principles in `PRINCIPLES.md` are framing-independent** and are
the current source of truth wherever an older doc's product framing conflicts with it.

*Personal research tool, not investment advice.*
