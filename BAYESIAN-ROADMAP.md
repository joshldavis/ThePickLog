# Bayesian roadmap — ThePickLog

**Written 2026-07-02.** R1 shipped this date; R2–R5 are planned, in priority order.
The motivation for all of it: the project's core problem is drawing honest conclusions
from a small forward log, and Bayesian machinery is built for exactly that — posteriors
say *how much the log has learned so far* instead of waiting for a fixed-n verdict, and
sequential updating stays valid under daily checking (no peeking problem).

Standing rules, inherited from the project's discipline:

- **Priors are frozen with a date before looking at the answer.** Tuning a prior after
  seeing the posterior is the Bayesian version of p-hacking.
- **Prior-sensitivity is reported, not hidden.** If flat/Jeffreys/skeptical disagree
  materially, the honest statement is "the data don't decide yet."
- **Read-outs, not judges.** Registered pass/fail criteria in HYPOTHESES.md stay the
  judges. Bayesian panels quantify certainty; they don't replace the registered tests.
- **Verifiability standard applies.** Every shipped number must be recomputable by a
  stranger from the committed CSVs. Prefer conjugate/deterministic math in the pipeline;
  anything needing MCMC runs as an offline study whose code + seed are committed.
- **Slippage caveat attaches to everything.** Posteriors inherit the proxy-fill
  assumption; they measure the *proxy's* edge, not real fills.

---

## R1 — SHIPPED 2026-07-02: Beta-Binomial posterior on H-EX1's touch rate

`bayes_h_ex1.py` → `reports/bayes-h-ex1-LATEST.md` + dashboard panel (independent JS
recompute, parity-tested cell-for-cell on the real log). Posterior on p = P(mfe_5d ≥
+10%), flat/Jeffreys/skeptical priors frozen 2026-07-02, P(p > breakeven) for both the
beat-baseline and absolute-profit lines, plus the pick-by-pick posterior evolution chart.
Runs in the weekly report workflow (stdlib-only, selftests abort on failure).

Known limitation (by design, honest about it): the breakeven lines use plug-in point
estimates of m (mean miss return) and the baseline EV. Their sampling noise is not
propagated. Fixing that properly is R3.

## R2 — Hierarchical partial pooling for the bucket cuts

**Problem it solves:** every conditional read (tier A/B vs C/D, regime, catalyst_type,
the H-F filter subsets) chops ~150 graded picks into cells of 5–30. Raw cell means
produce "tier A looks amazing, n=7" false positives — exactly what the pre-registration
discipline exists to prevent.

**Plan:** hierarchical Beta-Binomial (touch rate) and hierarchical normal (net return)
across buckets: cell estimates shrink toward the grand mean in proportion to how little
data they carry. Report shrunken vs raw side by side on the dashboard — the *gap*
between them is itself the "don't trust this cell yet" signal.

**Mechanics:** PyMC (or numpyro) offline study, committed as `studies/r2_hierarchical/`
with pinned seed + environment; outputs a static markdown/JSON snapshot the dashboard
can render. Not a pipeline step.

**Trigger:** worth building once ≥ ~30 OOS graded picks exist (per the HYPOTHESES.md
evaluate threshold), so the pooled model has something to pool. Est. late July 2026.

## R3 — Full two-part Bayesian model of H-EX1 economics

**Problem it solves:** R1's breakeven lines are plug-in. The honest object is the
posterior of *expectancy delta* (H-EX1 minus baseline), with all inputs uncertain.

**Plan:** joint model — p ~ Beta (touch rate); miss returns ~ Student-t (fat left tail;
normal would understate rugs); baseline returns ~ Student-t. Posterior of
Δ = [p·8 + (1−p)·E(miss)] − E(baseline), reported as P(Δ > 0) and a credible interval
on Δ in pp/trade. This subsumes R1's translation columns and directly answers "what is
the probability H-EX1 beats the baseline," which the registered §4d criterion can then
confirm frequentist-style.

**Mechanics:** conjugate-ish but not closed-form → offline PyMC study in
`studies/r3_two_part/`, same commit-the-seed rules. Refresh weekly by hand or via a
monthly workflow if it proves stable. Extends naturally to every exit-batch arm
(H-EX3..H-EX9) — one model, arms as indexed variants — with the family-wise honesty
note attached (the batch is a ranked screen, not seven independent claims).

**Trigger:** after R2 (shares the PyMC scaffolding). Also gated on ~30 OOS picks.

## R4 — Posterior over Finding A's effect size

**Problem it solves:** Finding A (hotter momentum → deeper drawdown) is currently a
table comparison. A Bayesian regression (mae_5d ~ tier group, Student-t errors) gives a
credible interval on the effect size in pp of drawdown. If the 90% interval excludes
zero on OOS picks, the dashboard claim upgrades from "holds so far" to a quantified
one; if it straddles zero, the chip honestly says so.

**Mechanics:** small enough to be near-conjugate; offline study `studies/r4_finding_a/`,
snapshot rendered on the dashboard next to the existing Finding A table.

**Trigger:** any time; more informative after the OOS sample matures. Low urgency
because Finding A already has a registered OOS filter expression (H-F4).

## R5 — Decision layer: posterior-predictive exit comparison + Kelly sizing

**Problem it solves:** two decisions eventually have to be made from the posteriors —
*which exit rule* to adopt, and *how big to trade it* if any survive.

**Plan, part A (exit choice):** posterior-predictive expected net per trade for each
exit-batch arm from the R3 model, ranked with credible intervals. This is the Bayesian
companion to the §4f ranked screen: prefer the simplest rule whose posterior-predictive
advantage is credible, per the registered family-wise rule.

**Plan, part B (sizing):** fractional Kelly under parameter uncertainty — compute the
Kelly fraction against draws from the posterior (not the point estimate) and take a
conservative quantile (e.g. 25th percentile of the per-draw Kelly), then halve it.
Small-n uncertainty automatically forces small size, which is the correct behavior.
Paper-trade sizes via the existing Alpaca PAPER wiring before any real capital.

**Trigger:** strictly after R3, and only for arms that pass their registered OOS
criteria. This is the last step before "act on survivors" in ROADMAP.md — the
posterior is the bridge from validation to position size.

---

## Explicitly rejected / deferred

- **Bayes factors for filter comparison:** considered; deferred in favor of R3's
  decision-relevant posteriors. Bayes factors are sensitive to prior width in ways that
  are hard to make stranger-verifiable, and the family-wise ranked-screen rule already
  handles multiplicity honestly.
- **Bayesian updating of the scoring model weights (v0.2 score):** out of scope while
  the product question is exits, not selection (SYNTHESIS.md: the bankable read is
  inverse momentum; selection edge is unsupported so far).
- **Any pipeline-embedded MCMC:** rejected on verifiability grounds — sampler
  nondeterminism across environments makes "recompute it yourself" fragile. Offline
  studies with committed seeds only.
