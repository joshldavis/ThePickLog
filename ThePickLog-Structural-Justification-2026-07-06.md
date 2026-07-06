# ThePickLog — Structural Justification & Monotonicity Check

**Structural-validity artifact (P1, gap register rows 3 & 4)**
Date: 2026-07-06 · Companion to `ThePickLog-Validity-Framework-Messick-2026-07-06.md` §2.3

Messick's structural aspect asks whether the **scoring structure mirrors the structure of the construct** — structural fidelity. For a graded ranking like A/B/C/D, that reduces to two checkable claims: (1) the way inputs are combined is justified, and (2) the tier ordering matches the outcome ordering (a higher tier should mean a better name). This document states the current structure, then tests claim (2) empirically against the committed log.

---

## 1. The current structure (from source, not memory)

Read directly from `ignitionscan.py` (`MODEL_VERSION = "v0.2-yf"`):

**Weights** (sum = 1): `float 0.30 · rvol 0.35 · gap 0.25 · price 0.10`
**Composite:** `score = Σ wᵢ · componentᵢ`, each component a 0–100 sub-score.
**Tier cutpoints:** `tier_of(s) = A if s≥75 · B if s≥60 · C if s≥45 · D otherwise`

> Note: an earlier inventory recorded the cutpoints as 90/75/50. The source of truth is `tier_of()` above — **75/60/45**. The framework doc has been corrected to match. (This is itself a small North-Star win: the claim was checked against the code and fixed.)

**The rationale gap (row 3).** Neither the weights nor the cutpoints are derived from data or documented anywhere. They are reasonable-looking v0.2 defaults. Under both Messick (structural fidelity) and the Uniform Guidelines (cutoffs must be "reasonable and consistent with acceptable proficiency," §5H), an undocumented cutpoint is a validity gap regardless of whether the number happens to be good.

---

## 2. Monotonicity check — does tier ordering match outcome ordering?

**Method (reproducible).** Join `picks.csv` (`pick_id → tier, score`) to `outcomes.csv` on `pick_id`; keep rows with a non-blank `ret_open_close_net` (excludes voided/pending); n = **165** graded rows. For each tier compute win %, mean/median net open→close, mean 5-day net, and mean `mae_5d` (drawdown). This is variable-selection evidence per P1 (**not** a performance claim), and it is the correct diagnostic for structural fidelity, which is about *ordering*, not profitability.

### Result

| Tier | n | win % | mean net O→C | median O→C | mean 5d net | mean MAE (drawdown) |
|------|---|-------|-------------|-----------|------------|---------------------|
| **A** (≥75) | 12 | 33% | **−4.59%** | −5.28% | −16.70% | **−24.68%** |
| **B** (≥60) | 14 | 57% | −1.70% | +0.89% | −1.98% | −20.52% |
| **C** (≥45) | 71 | 41% | −1.89% | −0.75% | −3.99% | **−16.19%** |
| **D** (<45) | 68 | 25% | −4.25% | −3.81% | −9.14% | −17.95% |

### Verdicts

- **Expectancy is NON-monotonic in tier.** Ordering by mean net is **B > C > D ≈ A**, with the *top* tier (A) essentially the *worst*. A higher score does **not** mean a better forward return. Structural fidelity for the "quality" interpretation: **fails.**
- **Drawdown IS monotonic in heat — the wrong way (Finding A confirmed).** MAE deepens as the score rises across A→C: A −24.7% (deepest) → B −20.5% → C −16.2% (shallowest). The score orders *risk*, cleanly, in the opposite direction from desirability. D breaks the clean run (−17.9%), consistent with D being a grab-bag of low-activity names.
- **Every tier's mean net is negative after costs** — consistent with the null external-validity finding; no tier is a "buy."

### Score-band calibration (finer than tiers)

| Score band | n | % positive | mean net O→C | mean MAE |
|---|---|---|---|---|
| 85–100 | 11 | 36% | −4.52% | −25.05% |
| 70–85 | 2 | (n too small) | — | — |
| 55–70 | 26 | 42% | −1.39% | −20.58% |
| 45–55 | 59 | 42% | −2.35% | −15.83% |
| <45 | 67 | 25% | −4.07% | −17.71% |

The calibration curve — the thing `SYNTHESIS §1.3` calls "hardest to fake" — is **flat-to-inverted**: % positive is ~36–42% across every band above 45 and the *top* band (85–100) has both the worst return and the deepest drawdown. A validity curve that should slope up if the score ordered edge is instead flat, with a down-tick at the top.

---

## 3. Interpretation: the score is a heat meter, and its structure should say so

The structural evidence and the content evidence (`ThePickLog-Domain-Coverage-Spec` §3) converge: the momentum composite is a well-behaved **intensity/heat index** — it orders drawdown monotonically — but its tier *labels* imply a quality ranking the data doesn't support. A→D reads as "best to worst"; the outcomes say "hottest/riskiest to coldest." That mismatch between label structure and construct structure is the structural-validity defect, stated precisely.

Caveats held honestly: A (n=12) and B (n=14) are small; B's strong showing rests on 14 names and should not be over-read; and this is the full graded log, not the post-registration OOS cut. None of those caveats rescue the ordering — the *top* tier being the *worst* on return and *deepest* on drawdown is a direction problem, not a precision problem.

---

## 4. Recommendations (structural, not performance)

1. **Re-label the tiers as an intensity scale, not a quality scale.** Present A–D as heat/volatility bands ("A = hottest, deepest expected drawdown"), matching the code's own "activity, not safety" comment and the Finding-A flag already in `brief.md`. This is a labeling fix a stranger can verify from this table — shippable now.
2. **Test combination form (row 4).** The linear composite is compensatory (a thin float offsets weak volume). Test a conjunctive alternative (require rvol *and* float above thresholds) against the log; if the construct is non-compensatory, a conjunctive gate should sharpen the calibration curve.
3. **Justify or retire the cutpoints.** Either derive 75/60/45 from the calibration curve (where do outcomes actually break?) or document them as arbitrary intensity bands. Do not present them as proficiency thresholds until they're one or the other.
4. **Do not promote any weight change in-sample.** Per P5, re-weighting to chase this table is overfitting. Any new structure is a new pre-registered hypothesis judged post-registration OOS — the same bar as every other rule.

---

## 5. Reproduce this

```
# from repo root
python3 - <<'PY'
import csv, statistics as st
picks={r['pick_id']:r for r in csv.DictReader(open('picks.csv'))}
rows=[]
for o in csv.DictReader(open('outcomes.csv')):
    v=o.get('ret_open_close_net','').strip()
    if not v: continue
    p=picks.get(o['pick_id']);  r=float(v)
    mae=o.get('mae_5d','').strip()
    rows.append((p['tier'], float(p['score']), r, float(mae) if mae else None))
for t in 'ABCD':
    g=[x for x in rows if x[0]==t]; oc=[x[2] for x in g]
    mae=[x[3] for x in g if x[3] is not None]
    print(t, len(g), f"win={100*sum(1 for x in oc if x>0)/len(g):.0f}%",
          f"mean={st.mean(oc):+.2f}", f"MAE={st.mean(mae):+.2f}")
PY
```

Anyone with the committed CSVs runs this and lands on the table in §2. That is the standard: the structural finding, like every other claim, is a stranger away from verification.
