# ThePickLog — Validity Framework & Gap Analysis

**Standing the project up to Messick's unified validity standard, with a Uniform Guidelines reach**

Date: 2026-07-06 · Owner: Josh · Status: v1 (framework + gap register)
Companion to: `PRINCIPLES.md` (North Star), `HYPOTHESES.md` (pre-registration), `MONETIZATION-GATE.md` (decision gates)

---

## 0. Why this document exists

`PRINCIPLES.md §4` already names Messick construct validity as one of three lenses behind the verifiability North Star, but it stops at a mention. This document does the rest: it stands the whole project up against Messick's **six aspects of construct validity** (Messick 1989, 1995) as a single unified standard, states what each aspect *demands*, grades where ThePickLog currently sits, and prescribes what to build to close each gap. A short **Uniform Guidelines** section runs the same material through employment-selection law as a stress test — not because it's binding (it isn't; picks aren't people), but because it forces sharper questions about robustness, fairness across subgroups, and documentation.

The one-line test everything still has to pass is the North Star:

> **"Can a stranger visit this site, pull the raw data, and verify that every claim is true?"**

Messick tells us *which* claims a validity argument must make. The North Star tells us they must be *reproducible*. This document unifies the two.

---

## 1. The construct under validation

You cannot validate a test without first saying what it's supposed to measure. Messick's whole framework is *construct* validity — every other kind of validity evidence is subsumed under it. So state the construct plainly:

> **The construct: the forward, tradeable favorable-move potential of a microcap at screen time — "edge."** A ThePickLog *score* (tier A–D) or *Quality Lens grade* (Green/Yellow/Red/Black) is a claim that names carrying that label have systematically different forward expectancy, net of realistic frictions, than names that don't.

The **observable score** is the tier/grade. The **criterion** is the forward return in `outcomes.csv` (open→exit, net of the 2% haircut). Validity is the degree to which the score's meaning — "this carries edge" — is warranted by evidence.

### 1.1 The two threats (the diagnostic spine)

Messick reduces all invalidity to two sources. Use them as the spine of every section below:

- **Construct underrepresentation** — the score is *too narrow*; it misses parts of the construct it claims. Here: a momentum-only composite (float, rvol, gap, price) may underrepresent the *fade* mechanism the project claims is the actual edge, and omits liquidity, catalyst, and regime as scored inputs.
- **Construct-irrelevant variance (CIV)** — the score reflects things *unrelated* to real edge that inflate or distort it. Here: data-snooping/multiple comparisons, look-ahead bias, thin-float price noise, survivorship in the screening frame, and a financial-specific one — **reflexivity** (publishing a thin-float pick can itself move the name and contaminate its own log).

Every gap in this document is ultimately one of these two. That is the point of using Messick rather than an ad-hoc checklist.

---

## 2. Messick's six aspects, mapped

Each aspect below follows the same structure: **Standard** (what Messick requires) → **Current evidence** (project artifacts) → **Verdict** → **Gaps** → **To meet the standard**. Maturity is graded **Established / Partial / Absent**.

### 2.1 Content — *does the score representatively sample the construct domain?*

**Standard.** Content relevance, representativeness, and technical quality: the inputs must sample the domain of drivers of the construct without irrelevant contamination, and be measured cleanly.

**Current evidence.** Four momentum factors (`float_score`, `rvol_score`, `gap_score`, `price_score`) plus a separate seven-component Quality Lens, all logged *at screen time*. EDGAR fundamentals captured point-in-time (`edgar_snapshot.csv`). Technical quality is strong — point-in-time capture in `paths.csv` defeats Yahoo revision drift.

**Verdict: Partial.** Technical quality is Established; domain representativeness is asserted, not demonstrated.

**Gaps.**
- No written **domain specification** — the universe of plausible spike-and-fade drivers, and which are sampled vs. deliberately excluded and why.
- **Underrepresentation risk:** the scored inputs are momentum-only, yet the claimed edge is the *fade*. Liquidity/spread appears only as a haircut, never as a feature; catalyst and dilution are captured but unscored.
- No expert/logic review documenting *why* these four factors, and not others, represent the domain.

**To meet.** Write a construct/domain definition and a **coverage matrix** (driver → represented? → how → if excluded, why). Explicitly flag momentum-only scoring as a known underrepresentation, with the fade mechanism carried by the exit rules rather than the score.

### 2.2 Substantive — *is there a theory of WHY, with evidence the mechanism operates?*

**Standard.** A theoretical rationale for the response process producing the scores, plus empirical evidence that the process actually operates as theorized (not merely that outputs correlate).

**Current evidence.** A stated thesis: screened names spike intraday (≈82% touch +5%, ≈63% touch +10%) then fade, so the edge is a disciplined exit, not selection. `exit_sim.py` path-walks touch order and fills against `paths.csv` — this is, in psychometric terms, a **response-process check**: it tests whether the scoring mechanism (order-of-touch, gap-through) behaves as the model assumes. `bayes_h_ex1.py` reports how much the log has actually learned.

**Verdict: Partial.** Rare strength for a retail tool — a process model *and* a process-fidelity check exist. But the mechanism isn't yet tested against rivals.

**Gaps.**
- The *causal* account of why thin-float + rvol spikes fade (microstructure exhaustion? promotional dynamics? mean reversion?) is asserted, not discriminated from alternatives.
- Thin response-process evidence beyond fills: no test of predictions *unique* to the fade thesis (e.g., fade depth should scale with float thinness).

**To meet.** Document the process model explicitly; test its unique predictions (Finding A + the planned R2 hierarchical bucket model give you the scaffolding — does fade/drawdown scale monotonically with float thinness and rvol?). Treat a passed unique-prediction test as substantive evidence; a failed one as evidence the mechanism is mislabeled.

### 2.3 Structural — *does the scoring structure mirror the construct's structure?*

**Standard.** Structural fidelity: the way scores are combined and thresholded should match how the construct is actually organized.

**Current evidence.** Score = weighted average of four factors (float .30 / rvol .35 / gap .25 / price .10) → tiers at **75/60/45** (per `ignitionscan.py tier_of()`; an earlier inventory's 90/75/50 was wrong and is corrected here). Quality Lens is deliberately kept **separate and unscored** ("capture now, don't score yet") — a genuinely good structural decision, because it refuses to impose an unvalidated structure.

**Verdict: Partial, with one red flag.** The restraint on Quality Lens is Established-grade discipline. But the momentum composite has an unresolved structural problem.

**Gaps.**
- **Weights (v0.2) and tier cutpoints (75/60/45) are asserted, not derived or justified.**
- **Compensatory vs. conjunctive structure untested:** a linear average lets a thin float "compensate" for weak volume — but the construct may be non-compensatory (no volume = no move regardless of float).
- **The Finding A red flag — now empirically confirmed:** the monotonicity check on 165 graded rows (companion `ThePickLog-Structural-Justification-2026-07-06.md`) shows tier ordering is **non-monotonic on return** (top tier A has the *worst* mean net, −4.59%; B is best) and **monotonic on drawdown the wrong way** (A −24.7% MAE deepest → C −16.2% shallowest). Higher score ≠ better outcome; the score orders *risk/heat*, not desirability. The ordinal structure does not match the construct's. This is the headline structural finding, not a footnote.

**To meet.** Justify or empirically derive weights and cutpoints (still open — the 75/60/45 cuts remain unjustified); run the compensatory-vs-conjunctive test (still open — the monotonicity check established the ordering problem but did not itself test combination form). Re-label tiers as an intensity/heat scale rather than a quality scale — a shippable, stranger-verifiable fix (shipped 2026-07-06). Any re-weighting is a new pre-registered hypothesis judged OOS (P5), never fit to this table in-sample.

### 2.4 Generalizability — *does the score's meaning hold across time, regimes, populations, and settings?*

**Standard.** Score properties and interpretations must generalize across populations, settings, tasks, and time — and the *boundaries* of generalization must be stated.

**Current evidence.** This is the project's strongest aspect *by design*: pre-registration with frozen dates, all-time vs. post-registration OOS windows, `paths.csv` for reproducible grading, the 2% friction haircut, `exit_sim.py` realism check, min-n gates (~200 graded / ~30 per tier / ~25% hold-out), and a direction-stability requirement across ≥3 weekly snapshots. This *is* a generalizability program.

**Verdict: Partial (well-architected, thinly populated).** The machinery is Established; the evidence is thin because the log is young.

**Gaps.**
- **Single regime, ≈18 days.** No cross-regime evidence; the `market_regime` field is captured but not yet a promotion gate.
- **The sampling frame is uncharacterized** — "whatever FinViz/Yahoo surfaced" is a population, but its selection isn't described, so survivorship/selection CIV is unquantified.
- **Paper → real fills** acknowledged (worse on thin floats) but not yet measured.

**To meet.** Make **regime hold-out a promotion gate**: an edge must survive in ≥2 regimes before it graduates from "unvalidated." Characterize the sampling frame in writing. Plan a live-fill validation before any monetization. Publish generalizability *boundaries* on-site ("verified in quiet-market conditions only," etc.).

### 2.5 External — *does the score relate to the criterion and the outside world as it should?*

**Standard.** Convergent evidence (score correlates with what it should — forward return), discriminant evidence (distinguishable from noise and from irrelevant factors), and applied utility (edge usable net of costs).

**Current evidence.** Criterion = forward return net of haircut in `outcomes.csv`; `leaderboard.json` reports expectancy deltas with 95% CIs; a crowd-level FDR note states "3/6 positive by point estimate, ~3/6 expected by chance." Utility is gated by `MONETIZATION-GATE.md` Gate 2 (edge > slippage).

**Verdict: Absent-to-date — and that is the honest headline.** 0/6 hypotheses significant; H-EX1 leads at Δ +1.7pp (CI [−3.2, +5.8], n=30, not significant); Bayesian P(H-EX1 beats baseline) ≈ 4%. **On current evidence the construct's external/criterion validity is unsupported.** The project's design is what lets you say that cleanly rather than hide it.

**Gaps.**
- No explicit **discriminant control arm** — a random microcap benchmark matched on price/float to prove the score does better than chance selection.
- Convergent evidence is null by definition until a hypothesis clears significance.

**To meet.** Add a matched random-pick control arm as the discriminant benchmark. Keep reporting effect sizes with CIs. Treat the **Gate-1 verdict (fires 2026-07-27)** as the formal external-validity readout, and publish it whichever way it lands — a documented null is valid evidence, and publishing it *is* the North Star.

### 2.6 Consequential — *what are the value implications and social consequences of using the scores?*

**Standard.** The consequences of score interpretation and use — including harms traceable to underrepresentation or CIV, and fairness. For a tool people may trade on, this is not optional; it's the aspect with real-world teeth.

**Current evidence.** Multiple safeguards already function as consequential-validity controls: "unvalidated" labels wherever the model appears, no monetization until the science gate clears, public null-publishing, the haircut, the `exit_sim.py` gap-through warning, and the verifiability North Star itself (which prevents misleading claims). Publisher's-exclusion / *Lowe v. SEC* positioning is noted in the market study.

**Verdict: Partial (strong instincts, incomplete articulation).**

**Gaps.**
- No written **intended-use / misuse statement** (e.g., someone over-leverages a single thin-float pick).
- **Reflexivity is unmonitored** — publishing a thin-float name can move it and contaminate its own outcome. This is simultaneously a consequential *and* CIV threat and deserves an explicit monitor.
- **Consequence-of-error framing** is implicit: a false positive costs a user real money, so the cost of a Type-I error here is asymmetric and should be stated.

**To meet.** Write an intended-use + misuse-and-consequences note tied to the current validity state. Add a reflexivity monitor (does publishing measurably move the name in the minutes after?). State the asymmetric cost of error explicitly, and let it justify the conservative "stay personal until the gate clears" default.

---

## 3. Uniform Guidelines reach — picks as "selections"

The **Uniform Guidelines on Employee Selection Procedures** (EEOC, 1978; 29 CFR Part 1607) govern when an employer may use a test that "selects" people. They don't apply here — a screener selects tickers, not protected persons. But treating a **pick as a selection decision** is a productive stress test, because the Guidelines are ruthless about exactly the things a young quant record tends to fudge: proof of a real criterion relationship, robustness across subgroups, and documentation.

**Criterion-related validity (§14B).** The Guidelines' preferred proof: a statistically significant relationship (p < .05) between selection score and job performance, on a sample representative of the applicant pool, with an unbiased, relevant criterion — plus attention to sample size and cross-validation. This maps *exactly* onto the pre-registered OOS program: tier (selection score) vs. forward return (performance), on the screened universe (applicant pool). Under this standard, ThePickLog's score **currently could not be used to justify selection** — 0/6 relationships clear significance. That is the correct verdict, and the design is what surfaces it.

**Content validity (§14C).** Permissible only when the procedure *samples* the job's content, and explicitly **not** appropriate for measuring constructs or traits inferred rather than observed. A predictive "edge" score is a construct, not a content sample — so the Guidelines would push you *away* from a content-validity argument and *toward* criterion-related evidence. Useful confirmation that the forward log, not a plausibility story about the factors, has to carry the case.

**Construct validity (§14D).** The most demanding route: define the construct, show it matters to the job, show the procedure measures it, and link it to performance. This is essentially Messick's program in regulatory clothing — so §14D and Section 2 above are the same obligation. Anywhere the doc says "define the construct," the Guidelines agree it's load-bearing.

**Job analysis.** The Guidelines require defining what success on the job *is* before validating a predictor of it. Analog: a written **outcome definition** — entry rule, exit arm, haircut, and win definition. You largely have this in `HYPOTHESES.md`/`PRINCIPLES.md`; formalize it as the "job analysis" of the record so the criterion can't drift.

**Adverse impact & the 4/5ths rule → subgroup robustness.** The Guidelines flag a procedure whose selection rate for a subgroup falls below 80% of the top group's. The transferable idea is **robustness across subgroups**: sectors, float buckets, price buckets, regimes. Two tests fall out:
- **Concentration.** If the entire edge lives in one thin pocket (one sector, one float bucket), treat it as fragile — the analog of a procedure that "works" only by disparately excluding a subgroup. No single bucket should carry the result.
- **Differential validity.** Does the score→return slope differ by bucket? The planned **R2 hierarchical (partial-pooling) Bayesian model is precisely a subgroup-validity analysis** — it's the tool that answers this honestly without slicing yourself into noise.

**Documentation standards (§15).** The Guidelines demand a detailed validation record: problem and setting, sample description, criterion measures, statistical results, cutoff-score rationale, dates. ThePickLog's committed CSVs + `PRINCIPLES.md` + `HYPOTHESES.md` already approximate a §15 report. Formalize them into a single **validity dossier** with those headings — it doubles as the artifact a skeptic (or a lawyer, at Gate 4) reads.

**Cutoff scores.** The Guidelines require cutoffs to be reasonable and consistent with acceptable proficiency — not arbitrary. This lands right back on the **structural gap**: the 75/60/45 tier cuts and the +10% exit target need a stated justification, not just a chosen number.

The Guidelines reach reinforces four Messick findings rather than adding new ones: significance is mandatory (external), cutoffs must be justified (structural), the edge must not be a single-bucket artifact (generalizability), and it must be documented to a stranger's standard (consequential + North Star).

---

## 4. Consolidated gap register

Priority: **P1** = blocks any "validated" claim or monetization · **P2** = strengthens the argument materially · **P3** = polish.

Status as of 2026-07-07: rows 1, 3, 4, 10 **closed**; rows 2, 6, 8 **studied + registered forward**; row 5 **gate codified** (live-fill deferred); row 9 **closed**; row 7 owned by the 7/27 verdict task.

| # | Aspect | Gap | Status / where | Pri |
|---|--------|-----|----------------|-----|
| 1 | Content | Momentum-only inputs omit liquidity/catalyst/fade drivers | **Closed** — domain + coverage matrix written (Domain-Coverage-Spec); underrep. labelled | P2 |
| 2 | Substantive | Fade mechanism not discriminated from rivals | **Studied** — heat→drawdown confirmed, fade-as-edge not; unique-prediction test registered **H-SUB1** (Empirical Studies §1) | P2 |
| 3 | Structural | Weights & tier cuts (75/60/45) unjustified | **Closed (documented) + registered** — calibration flat, rvol weight near-inert (81% <10); re-derivation registered **H-STR2** (Empirical Studies §3) | P1 |
| 4 | Structural | Compensatory vs. conjunctive untested | **Closed** — conjunctive gate concentrates worst names, no lift; combination form is not the lever (Empirical Studies §2) | P1 |
| 5 | Generalizability | Single-regime; frame uncharacterized; paper≠real | **Gate codified** — regime hold-out gate in PRINCIPLES P5 + frame characterized; live-fill deferred (Gate 2). Regime-fragile: risk-on −5.49% | P1 |
| 6 | External | No discriminant control arm | **Studied + registered** — forward log indistinguishable from broad pool (CIs overlap, both neg.); true control registered **H-CTRL** (Empirical Studies §4) | P2 |
| 7 | External | Criterion relationship null to date | **Owned by 7/27 task** — Gate-1 verdict `thepicklog-gate1-external-validity-verdict` | P1 |
| 8 | Consequential | Reflexivity unmonitored | **Design done + registered** — monitor spec + ~nil current exposure; **H-REFLEX**, activates at scale (Generalizability & Consequential B.2) | P2 |
| 9 | Consequential | No intended-use/misuse + cost-of-error statement | **Closed** — use/misuse + asymmetric-loss justification written (Generalizability & Consequential B.1) | P2 |
| 10 | UG / Docs | No single §15-style validity dossier | **Closed** — Validity-Dossier-UG15 indexes the whole record to §15 headings | P3 |

**Reading the register:** the P1 cluster is small and coherent — justify the score's structure (3, 4), prove the edge generalizes past one regime (5), and let the pre-registered criterion test render its verdict (7). Everything else strengthens the argument but none of it can substitute for those four. Notably, nothing here asks you to *manufacture* a positive result; the framework is satisfied by a rigorously documented null just as much as by a win.

---

## 5. How this plugs into the North Star and the weekly audit

Messick supplies the *claims* a validity argument must make; the North Star requires each to be *stranger-reproducible*; the weekly audit is where the two meet operationally. Concretely:

- **Extend `PRINCIPLES.md §4`** from a mention of Messick to a pointer at this document as the standing validity argument.
- **Add six lines to the weekly verifiability audit** (`AUDIT_LOG.md`) — one per aspect — each asking whether the on-site claim for that aspect is currently backed by reproducible evidence or is still labeled "unvalidated." An aspect that can't be reproduced from the CSVs fails the audit exactly as a headline number would.
- **Wire the gate to the register:** `MONETIZATION-GATE.md` Gate 1 is the External-validity verdict (row 7); Gate 2 is applied utility (external); Gate 4 (legal) is where the §15 dossier (row 10) earns its keep. The gates and the six aspects are the same commitments viewed from two angles.

The through-line: a claim ships only if it names which aspect of validity it rests on, and a stranger can pull the CSVs and confirm that aspect holds. Passing Messick without passing the North Star is a private belief; passing the North Star without Messick is a reproducible number that may not mean what it says. ThePickLog's standard is both.

---

*Framework references: Messick, S. (1989), "Validity," in Linn (ed.) Educational Measurement, 3rd ed.; Messick, S. (1995), "Validity of Psychological Assessment," American Psychologist 50(9). Uniform Guidelines on Employee Selection Procedures (1978), 29 CFR Part 1607 — cited by analogy only; not legally applicable to security screening.*
