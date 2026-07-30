# ThePickLog — Validity Dossier (Uniform Guidelines §15 structure)

**Closing gap-register row 10 — the single, indexed validity record**
Date: 2026-07-07 · The capstone that ties the validity argument together

This dossier consolidates ThePickLog's validity evidence into the documentation structure the Uniform Guidelines on Employee Selection Procedures require of a validation study (29 CFR §1607.15). The Guidelines don't legally bind a security screener — but their §15 template is the most complete "what a validation record must contain" checklist available, and organizing to it makes the record a stranger can audit end-to-end. Each section states the standard, the current status, and the artifact that carries the evidence.

---

## 15A — General information & problem statement

- **What is "selected":** microcap tickers, by a momentum score (tiers A–D) and a separate Quality Lens grade. The construct: forward, tradeable favorable-move potential ("edge").
- **Setting:** a personal research lab, published in the open; no subscribers, no monetization. Family/friends Compete launch not live until ~2026-07-23.
- **Dates:** log opened 2026-06-09; this dossier covers data through 2026-07-07 (180 graded of 269 logged).
- **Governing documents:** `PRINCIPLES.md` (North Star + five operating principles), `HYPOTHESES.md` (pre-registration), `MONETIZATION-GATE.md` (decision gates), and the standing validity argument `ThePickLog-Validity-Framework-Messick-2026-07-06.md`.

## 15B — Criterion-related validity (the primary route)

*Standard:* a statistically significant relationship (p < .05) between selection score and job performance, on a representative sample, with a relevant, unbiased criterion; attention to sample size and cross-validation.

- **Criterion:** forward open→close return net of a 2% haircut (`outcomes.csv`), with 5-day return, MFE, and MAE recorded alongside.
- **Design:** pre-registration with frozen dates (`HYPOTHESES.md`); all-time vs post-registration windows tracked separately (`weekly_report.py`); 95% CIs by bootstrap; sample gates (~200 graded / ~30 per tier / ~25% hold-out).
- **Status — UNSUPPORTED to date (an honest null).** 0 of 6 pre-registered rules clear the 95% CI; best is H-EX1 (+10% exit) at Δ +1.7pp, CI [−3.2, +5.8], n=30; Bayesian P(beats baseline) ≈ 83% (suggestive, not decisive). The whole screened population is reliably negative on open→close (−2.85%, CI [−4.11, −1.58]). **Under a §15B standard the score could not currently justify selection.** The pre-registered **Gate-1 verdict fires 2026-07-27** (owned by the scheduled task `thepicklog-gate1-external-validity-verdict`) and will be published either way.
- **Artifacts:** `leaderboard.json`, `reports/LATEST.md`, `reports/bayes-h-ex1-LATEST.md`, `ThePickLog-Empirical-Validity-Studies-2026-07-07.md`.

## 15C — Content validity

*Standard:* the procedure representatively samples the construct domain without irrelevant contamination; not appropriate as the *sole* route for an inferred construct like "edge."

- **Status — Partial.** Written domain + coverage matrix exists: the score samples **4 of ~15 domain drivers, from 2 of 7 families**; the fade's likely causes (catalyst, liquidity/borrow, regime) are unscored. Momentum-only underrepresentation is labelled openly. A construct-irrelevant-variance flag is documented (`gap_score` uses |gap|, so down-gaps score like up-gaps).
- **Artifact:** `ThePickLog-Domain-Coverage-Spec-2026-07-06.md`.

## 15D — Construct validity (the full argument)

*Standard:* define the construct, show it matters, show the procedure measures it, link it to performance — Messick's program in regulatory clothing.

- **Status — one hard structural failure, the rest Partial/Absent, all labelled.** The standing framework grades all six Messick aspects. Headline: the momentum **tiers rank intensity/drawdown, not return** (top tier A has the worst mean net −4.59% and deepest MAE −24.68%); the nominal 0.35 rvol weight is **rarely activated** (85% of picks score <10). **Corrected 2026-07-29:** the earlier reading of this — "the composite is effectively float-dominated" — was wrong. On the v0.2 cohort `float_score` (sd 0.26) and `price_score` (sd 0.00) are effectively constants, so **40% of the nominal weight contributes 0.0% of score variance and cannot affect the ranking**; the ordering is **gap-dominated** (ρ +0.925 gap vs +0.576 rvol vs +0.081 float). On the v0.3 market-wide cohort the decomposition inverts (rvol 66.0% / float 26.4% / gap 7.6% of variance), so the A–D scale is **not comparable across cohorts** — registered forward as H-STR3. Tiers have been re-labelled as a heat scale (shipped 2026-07-06).
- **Artifacts:** `ThePickLog-Validity-Framework-Messick-2026-07-06.md`, `ThePickLog-Structural-Justification-2026-07-06.md`, `ThePickLog-Empirical-Validity-Studies-2026-07-07.md`.

## 15 (fairness / adverse-impact analog) — subgroup robustness

*Standard (adapted):* no procedure should "work" only by concentrating in a single subgroup; check differential validity across subgroups.

- **Status — the edge is regime-dependent and single-regime fragile.** By `market_regime`: risk-on −5.49% (win 22%), neutral −1.74%, risk-off −1.70% — no regime positive, risk-on materially worst. A **regime hold-out promotion gate** (edge must hold in ≥2 of 3 regimes) is now codified. Float/price-bucket subgroup analysis and the planned R2 hierarchical (partial-pooling) model are the next subgroup tools.
- **Artifact:** `ThePickLog-Generalizability-and-Consequential-2026-07-07.md`.

## 15 (cutoff scores)

*Standard:* cutoffs must be reasonable and consistent with acceptable proficiency, not arbitrary.

- **Status — unjustified, and documented as such.** The 75/60/45 tier cuts show no supporting outcome break in the calibration curve; they are presented as arbitrary **intensity** bands, not proficiency thresholds. A re-derivation is registered (H-STR2) for out-of-sample judgement — never fit in-sample.

## 15 (records & reproducibility)

*Standard:* detailed, retained records; a third party can follow the study.

- **Status — Established (this is the North Star).** Immutable append-only `picks.csv` / `outcomes.csv` / `paths.csv`; one deterministic evaluator (`hypo_eval.py`) with a build-aborting parity self-test; weekly verifiability audit (`AUDIT_LOG.md`) now including a six-aspect validity check; every claim recomputes from the two public CSVs. The validity argument is linked publicly from `method.html §9`.

---

## Consolidated status

| §15 section | Standard | Status | Owner artifact |
|---|---|---|---|
| 15B Criterion-related | significant score↔return | **Null to date**; verdict 7/27 | Empirical Studies; leaderboard |
| 15C Content | representative domain sample | Partial (underrep. labelled) | Domain/Coverage Spec |
| 15D Construct | full Messick argument | Structural FAIL + Partial | Framework; Structural Justification |
| Fairness analog | subgroup robustness | Regime-fragile; gate added | Generalizability & Consequential |
| Cutoff scores | non-arbitrary cuts | Unjustified; re-derivation registered | Structural Justification |
| Records | reproducible by a stranger | Established | PRINCIPLES; AUDIT_LOG; CSVs |

**The dossier's honest bottom line:** the *documentation and process* around this record are strong (records, pre-registration, published nulls); the *substantive validity* is unproven and, on the structural aspect, partly failing — and every line above says so in a way a stranger can check. That is the state of the evidence on 2026-07-07, and the 7/27 criterion verdict is the next thing that moves it.
