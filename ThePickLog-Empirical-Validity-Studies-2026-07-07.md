# ThePickLog — Empirical Validity Studies

**Closing gap-register rows 2 (substantive), 3 & 4 (structural), 6 (external discriminant)**
Date: 2026-07-07 · Companion to `ThePickLog-Validity-Framework-Messick-2026-07-06.md`

Four studies run on the committed log (`picks.csv` × `outcomes.csv`, n = 180 graded; `backtest_results.csv`, n = 2,124 as the broad-pool reference). **All results here are in-sample diagnostics for variable selection (PRINCIPLES P1) — not performance claims.** Where a rule emerges it is pre-registered for out-of-sample judgement (P2/P5), never shipped from this table. Every number reproduces from the two public CSVs with the code in §5.

---

## Study 1 — Substantive: does the mechanism operate as theorized? (row 2)

The thesis: screened names spike then **fade**, and the fade should scale with heat. Test whether drawdown/return move monotonically with float thinness and with relative volume.

**By float (thinner should mean bigger, more violent moves):**

| Float | n | win % | mean net | mean MAE |
|---|---|---|---|---|
| <3M (thinnest) | 154 | 38% | −2.40% | −17.07% |
| 3–8M | 26 | 23% | −5.47% | −20.93% |

**By relative volume (higher = bigger spike):**

| RVOL | n | win % | mean net | mean MAE |
|---|---|---|---|---|
| <3× | 162 | 35% | −2.73% | −17.21% |
| 3–7× | 6 | 67% | −2.55% | −14.92% |
| 7–15× | 5 | 40% | −0.72% | −20.63% |
| ≥15× | 7 | 29% | −7.35% | −27.57% |

**Finding.** The mechanism operates *on the downside only*: the highest-RVOL names show the deepest drawdown (−27.6% MAE) and worst return (−7.35%) — spikes do fade, hard. But the fade does **not** convert to a better open→close return at higher heat, and float thinness is **not** monotonic (the mid-float bucket is worst). So "spike-then-fade" is supported as a *risk* signature, not yet as a *return* edge in the close-based metric — consistent with the project's own pivot to an intraday exit rule (H-EX1) rather than a selection or close-hold edge. **Substantive verdict: the response process behaves partly as modeled (heat→drawdown), but the unique prediction that bigger spikes carry a harvestable edge is unconfirmed.** Registered forward as **H-SUB1** (§4).

---

## Study 2 — Structural: compensatory vs. conjunctive combination (row 4)

The live score is a **compensatory** linear blend (a thin float can offset weak volume). Test a **conjunctive** gate (float *and* rvol both hot, ≥60 each).

| Group | n | win % | mean net | mean MAE |
|---|---|---|---|---|
| BOTH hot (conjunctive) | 12 | 33% | −4.59% | −24.68% |
| only float hot | 168 | 36% | −2.72% | −17.13% |
| only rvol hot | 0 | — | — | — |
| neither | 0 | — | — | — |

**Finding.** The conjunctive gate does **not** improve anything — "both hot" isolates the *worst* names (−4.59%, deepest MAE), and it is nearly empty (n=12). Crucially, **"only rvol hot" and "neither" are empty**: essentially every screened name is "float hot," and rvol almost never fires — which sets up Study 3. Compensatory vs. conjunctive is close to moot until the rvol input is fixed. **Structural verdict: combination form is not the lever; the input mix is.**

---

## Study 3 — Structural: are the weights and cutpoints justified? (row 3)

**Cutpoint calibration** — % positive by fine score band:

| Score band | n | win % | mean net | mean MAE |
|---|---|---|---|---|
| 40–45 | 74 | 27% | −3.62% | −16.71% |
| 45–50 | 38 | 45% | −2.44% | −15.55% |
| 50–55 | 27 | 41% | −2.15% | −18.15% |
| 55–60 | 15 | 33% | −0.97% | −18.16% |
| 60–70 | 13 | 54% | −1.86% | −22.90%* |
| 70+ | 13 | 38% | −4.21% | −22.90% |

The curve is **flat-to-non-monotonic**: no clean outcome break sits at 75, 60, or 45. The cutpoints are not justified by the data — they are arbitrary intensity bands, and should be described as such (as now shipped in the tier re-label).

**The weight finding (the sharper one).** — **CORRECTION 2026-07-29: the original version of
this paragraph reached the wrong conclusion and is restated here. The superseded text read: "the
composite is effectively float-dominated and the .35 rvol weight is largely inert … the score is,
in effect, a float-and-gap intensity index."** The premise was right, the inference inverted.

The nominal weights are float .30 / **rvol .35** / gap .25 / price .10. The rvol sub-score is indeed
mostly asleep: median 0.9, **85% of picks score below 10** on the v0.2 cohort. But rvol is not the
dead input — **float is.** On v0.2, `float_score` is almost perfectly constant (**mean 99.92,
sd 0.26**) and `price_score` is *exactly* constant (**sd 0.00**), because a fixed 16-name
ultra-low-float universe maxes both out on every pick. A constant cannot rank anything, so
**40% of the nominal weight (float .30 + price .10) contributes 0.0% of the score's variance and
cannot affect the ordering at all.** The two live inputs are rvol (**54.8%** of weighted variance)
and gap (**45.2%**), and by rank correlation the ordering is **gap-dominated**:
ρ(score, gap) **+0.925**, ρ(score, rvol) **+0.576**, ρ(score, float) **+0.081**. So rvol is best
described as *rarely activated but decisive when it fires* — its large weight is idle 85% of the
time, which is why gap wins the rank correlation despite carrying a smaller weight.

**The composite also measures different things in different universes.** Re-running the same
decomposition on the v0.3-yf market-wide cohort inverts the picture: float becomes live and rvol
takes over — weighted-variance shares rvol **66.0%** / float **26.4%** / gap **7.6%**, rank
correlations rvol **+0.738** / float **+0.529** / gap **+0.395**. Because the criteria-defined v0.3
universe admits names across a real float range while pushing gap and rvol near their caps, the
same formula produces a *different ranking construct* per cohort — and ~83% of v0.3 picks land in
tier A. **Consequence: the A–D tier scale is not comparable across cohorts**, and any cross-cohort
statement about tiers is invalid. **Structural verdict (unchanged in direction, sharpened): the
cutpoints and weights remain unjustified by evidence, and the four-factor label overstates the
model — on v0.2 it is a gap-and-rvol intensity index with two inert inputs, and on v0.3 it is a
different index again.** Registered forward as **H-STR1** (float-only parity), **H-STR2**
(re-derived weights/cutpoints) and **H-STR3** (does the composite add anything over gap alone) —
never re-fit and shipped in-sample.

---

## Study 4 — External: discriminant benchmark (row 6)

Does the screen *select* a distinguishable population, or just re-draw the pool?

| Population | n | mean net | 95% CI | win % |
|---|---|---|---|---|
| Broad scored pool (`backtest_results.csv`, in-sample ref) | 2,124 | −1.91% | [−2.32, −1.49] | 32% |
| Forward screened log | 180 | −2.85% | [−4.11, −1.58] | 36% |

**Finding.** The forward log is **not distinguishable** from the broad pool — the CIs overlap and the screened names are, if anything, slightly *worse*. Both populations are reliably **negative** on open→close. There is **no discriminant evidence that the screen selects positive-expectancy names**, which is again consistent with the edge (if any) living in the exit, not the selection. **Caveat:** the backtest pool is an in-sample reference with known Yahoo-drift limits, so this is a directional discriminant read, not a clean control. A *true* matched-random control (in-universe microcaps the screen did **not** pick, captured forward on the same days) is not in the data and is registered as **H-CTRL** (§4).

---

## §4 — Pre-registered forward tests (frozen 2026-07-07)

These emerge from the studies above and are frozen here per P2; only picks logged **after 2026-07-07** count. None changes the live model (P5).

- **H-SUB1 (substantive):** among post-reg picks, does 5-day MFE (spike size) scale monotonically with rvol at screen time? A positive, monotonic relationship is the unique prediction of the fade thesis; its absence means the "spike" label is mis-specified.
- **H-STR1 (structural, open):** does a **float-only** score reproduce the four-factor tier ordering on post-reg picks? If yes, the rvol/gap/price weights add no ordering information and should be dropped or re-derived.
- **H-STR2 (structural):** re-derive weights and cutpoints from post-reg data only, register the derived scheme, and judge it OOS against the current v0.2 — never promote an in-sample fit.
- **H-REG (generalizability/selection):** skip picks tagged `market_regime = risk-on`; does the kept subset beat the unfiltered baseline OOS? (In-sample, risk-on was −5.49% vs −1.7% otherwise — see the generalizability doc.)
- **H-CTRL (external discriminant):** begin capturing, per scan day, a matched random sample of in-universe microcaps the screen did **not** select, forward-only, to enable a proper screened-vs-unscreened discriminant test.

---

## §5 — Reproduce

Run from the repo root; joins `picks.csv` to `outcomes.csv` on `pick_id`, buckets, and prints every table above.

```
python3 - <<'PY'
import csv, statistics as st, math
picks={r['pick_id']:r for r in csv.DictReader(open('picks.csv'))}
rows=[]
for o in csv.DictReader(open('outcomes.csv')):
    v=(o.get('ret_open_close_net','') or '').strip()
    if not v: continue
    p=picks.get(o['pick_id']); g=lambda d,k:(float(d[k]) if (d.get(k,'') or '').strip() not in ('','None') else None)
    try: rows.append(dict(oc=float(v), mae=g(o,'mae_5d'), score=g(p,'score'),
        rscore=g(p,'rvol_score'), rvol=g(p,'rvol'), regime=(p.get('market_regime','')or'').strip()))
    except: pass
rs=[r['rscore'] for r in rows if r['rscore'] is not None]
print("rvol_score: median",st.median(rs),"share<10:",round(100*sum(v<10 for v in rs)/len(rs)),"%  share>=60:",round(100*sum(v>=60 for v in rs)/len(rs)),"%")
oc=[r['oc'] for r in rows]; se=st.pstdev(oc)/math.sqrt(len(oc))
print("forward mean",round(st.mean(oc),2),"95%CI",[round(st.mean(oc)-1.96*se,2),round(st.mean(oc)+1.96*se,2)])
PY
```
