# ThePickLog — guide for coding agents

## Working rules

**What this repo is.** A public, honestly graded log of screened low-float stock picks (thepicklog.com). Static HTML pages at the root (`index.html`, `method.html`, `experiment-*.html` …) served by Vercel with `outputDirectory: "."`, Node serverless functions in `api/`, and Python 3.11 research/automation scripts at the root. GitHub Actions in `.github/workflows/` run the daily scan/grade, weekly report, watchdog, quote cache and paper trader, and commit data straight to `main`. The repo is public on purpose (anyone must be able to re-derive every claim) and stays public.

**Read first.** `PRINCIPLES.md` (the verifiability standard, operating rules P1–P5, and the one question in §5: does this change make the record more verifiable or less?) and `INTEGRITY.md` (the tamper-evident hash chain in `integrity_ledger.csv`, offsite artifacts, watchdog). `DOCS.md` maps every other doc. Don't restate or edit those files; follow them.

### Commands that exist
- Deps (as CI pins them): `pip install "yfinance==1.7.0" "pandas==3.0.6" "numpy==2.4.6"`; Node >= 18 for `api/` (`package.json`).
- Safe local checks: `python3 ignitionscan.py demo` (offline sample, writes nothing), `python market_time.py` (calendar selftest), `python log_integrity.py --verify` and `--verify-head` (recompute the hash chain).
- Assistant checks: `cd evals && npm run eval:offline` (no key, no cost). Real model runs (`npm run eval:models`) cost money and run on GitHub only via the `run-model-check` PR label; run them before changing `AGENT_MODEL` or the assistant's SYSTEM prompt (`evals/README.md`).
- Preview static pages: `python3 -m http.server` from the repo root. `vercel.json` rewrites and `api/` routes don't run that way.
- There is no lint config or unit-test suite. Don't invent one in an unrelated change.
- Don't run locally: `ignitionscan.py scan|grade|report`, `weekly_report.py`, `paper_trader.py`, or `log_integrity.py --event=...`; they write to the record, which only CI does. Don't run `node scripts/stamp-build.mjs` in your checkout: it rewrites footers and deletes root Markdown files (it's the Vercel build step).

### How to work
- **Think before coding.** State your assumptions. If a choice would change a number, a page's meaning or a public URL, ask first.
- **Simplicity first.** Make the smallest change that solves the ask. No speculative abstractions, no new dependencies without a stated reason.
- **Surgical changes.** Touch only what the task needs. Don't reformat, rename or "tidy" unrelated code or pages; match the style of the file you're in.
- **Goal-driven.** Decide up front how you'll verify (selftest, offline eval, demo run, page preview), run it, and report the result before calling the work done.
- **GitHub is the system of record.** Work on a branch and open a draft PR for the owner to review. Never push to `main`, never force-push, never merge. Expect bot data commits on `main`; rebase rather than overwrite them.
- **No secrets in the repo.** Never commit keys, tokens or `.env` files. Env vars and secrets are set by the owner in Vercel or GitHub settings; refer to them by name only.

### Record integrity (non-negotiable)
- Pre-registrations, ledgers and recorded results are never edited after the fact. That covers `picks.csv`, `outcomes.csv`, `paths.csv`, `integrity_ledger.csv`, `REGISTRATION-*.md`, registered entries in `HYPOTHESES.md`, `RESULT-*.md`, `experiments/` outputs, judge files and every other committed CSV/JSONL data file. A hand edit breaks the hash chain and the project's whole claim.
- Corrections go in new dated files beside the original, as the repo already does: `CORRECTION-ece-2026-10-08.md`, `corrections/*.csv`, `fix_*_2026_10_25.py`. Originals stay unchanged.
- Generated output (`reports/*.md`, `leaderboard.json`) is written by scripts; don't hand-edit it (`DOCS.md`).
- A new registration ships only as its own dated commit; calibration/judge work in progress stays local (`.gitignore`).
- Any new on-site number must be re-derivable from committed data, and an unproven model stays labelled "unvalidated" (`PRINCIPLES.md` P1–P5).

### Public links must not break
- Keep page filenames and the routes in `vercel.json` (`/r/:id`, `/r/:id/og.png`, `/u/:handle`, `/method`, `/trust`, `/scorecard`, `/guide`, `/about`, `/how-many-did-you-test` …) working. Update `sitemap.xml` and `feed.xml` if you add a page, and add a redirect rather than remove or rename one.
- Raw data URLs (`picks.csv`, `outcomes.csv` …) are part of the weekly audit (`PRINCIPLES.md` §3) and must stay at their paths.
- Vercel publishes everything committed. Root `*.md` files are pruned at build unless listed in `PUBLIC_DOCS` in `scripts/stamp-build.mjs`; don't remove a listed doc, and don't commit anything that shouldn't be public.

### UI changes
- Follow `DESIGN.md`. Colour tokens live in each page's own `:root` block and in the `THEME` objects in `api/receipt.js`, `api/profile.js` and `api/og.js`; there is no shared stylesheet. Use the existing variables, not one-off hex values.
- There is no Tailwind or other CSS framework here; styles are inline `<style>` blocks per page. If a utility-class framework is ever added, every file that holds class names must be in its scanned paths (a real bug elsewhere: classes in `lib/` were never generated).
- Keep the `__BUILDSTAMP__` footer token in `index.html`, `guide.html` and `trust.html`, and the per-page a11y baseline (skip link, `:focus-visible` ring).
- Tier colours are a single teal heat ramp on purpose; never style tiers or scores as green = good (comment in `index.html`).

### Repo-specific rules found in the docs
- `README.md`: `picks.csv` "is the track record; never edit it by hand."
- `ROADMAP.md`: Alpaca is pinned to paper trading; going live needs two deliberate env flags and is the owner's call. Don't change that.
- `ROADMAP.md` guardrails: the forward log is the only judge, backtests are variable selection only, every new rule is pre-registered in `HYPOTHESES.md` and judged out-of-sample.
- `AI-ASSISTANT-SETUP.md` / `evals/README.md`: the assistant is educational only and built on already-verifiable data; no buy/sell calls.
