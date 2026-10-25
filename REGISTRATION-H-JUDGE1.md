# Pre-registration — H-JUDGE1 (rater validity) and H-AUTH1 (authority allocation): can an AI judge forecast a pick's drawdown better than the score already does?

**Registered:** 2026-10-25, a Sunday, before the 2026-10-26 open. The git commit that adds this file is the timestamp. **Forward window: v0.3-yf picks with `trading_date` from 2026-10-26 through 2026-12-31** (the same end as H-JEV1 Part B and H-JEV2). **One verdict look, on or after 2027-01-11**, run together with H-JEV Part B. An interim readout at n ≥ 150 is report-only and changes nothing.

**Shadow mode, binding.** Nothing a judge returns touches selection, a pick card, the site, a grade, a count or a trade. A pass licenses *advisory use in shadow mode* only, and any later display would be a new registration.

**Why the code isn't in this commit.** `judge/` is kept out of the public repo because Vercel serves the repo root, and arms 1b/1c read third-party SEC filing text (see `.gitignore`). So this file freezes the instrument **by sha256**. Every judge file is listed below, and the three prompts are reproduced in full at the end. Any change to a listed file after this commit is an amendment and must be recorded here before it is used.

## What was already seen, stated before any window data exists

- **Baseline B0** was fitted and frozen on 2026-10-07 from picks traded before this window (`judge/b0_frozen_dd20.json`: v0.3 n = 476, 344 tickers, dd20 base rate 0.511, in-sample AUC 0.667). It uses no window data.
- **The H-AUTH1 stakes cut points** were derived on 2026-09-23 from graded v0.3 picks before this window (`judge/stakes_cutpoints_v03.json`: thin float < 1,438,267 shares).
- **Pipeline tests only.** Judge 2 was tested on 2026-10-25 against one pre-window pick (JAGX, 2026-10-06), once per arm, written to a scratch file outside `predictions.csv`. Its outcome was not opened. Jev was live-tested on the same pick on 2026-10-06, also to a scratch file. Neither appears in the record.
- **Direction is known to be unpredictable here and drawdown is known to be partly predictable** (Gate 1, the 2026-07-29 sweep, H-RISK1/2, H-JEV1 Part A). That is why drawdown is the primary criterion. It is a reason to expect a modest effect at most, not evidence for one.

## The instrument (frozen)

**Criterion (primary).** `dd20 = mae_5d ≤ −20`: the stock trades at least 20% below the entry open within the entry session plus the next 5 sessions. This is the H-RISK2 / H-JEV target. **Secondary, reported only:** `pass = ret_open_close_net > 0`.

**Judges.**
- **J1 = `jev-1.13.0`**, pinned. It answers two `noul` questions (`drawdown_20`, `close_above_open`), whose block is frozen in `run_judge.py` as `JEV_QUESTIONS`.
- **J2 = OpenAI `gpt-5.5-2026-04-23`**, a pinned dated snapshot, called through Chat Completions with `reasoning_effort: "low"`, JSON mode, no tools and no web access (`CHAT_VENDORS` in `run_judge.py`). It was chosen 2026-10-25. It is from a different vendor than J1, so agreement between the two judges means something. No shutdown date for this snapshot was announced at registration. The December 2026 retirements (`gpt-5-2025-08-07`, `o3-2025-04-16`, etc.) were avoided deliberately. If the snapshot is retired before every window pick has been judged, J2 is **INSUFFICIENT**. It is never re-pinned under this registration.
- `run_judge.py` refuses a reply whose `model` differs from the pinned id (`VERSION DRIFT`).

**Arms**, each judge with k = 3 repeats:

| Arm | Input | Purpose |
|---|---|---|
| 1a | screen-time fields only, identity masked | null control |
| 1b | fields + the **same pre-open filings Jev read for H-JEV** (`build_preopen.py` ← `jev-backfill-results/state/pick_filings.csv`), company name and ticker masked | the claim |
| 1c | same as 1b, unmasked | distraction test |

**Judge ids** (`sha256(vendor|model|spec|arm)[:16]`) are fixed by the files below. A different id means a different judge, and it is not graded here:

| | 1a | 1b | 1c |
|---|---|---|---|
| J1 jev | `3a9e41808e79383d` | `eba1959bfef55d6f` | `141d1c3ba251ed96` |
| J2 openai | `e101ea07b45b0ce5` | `5fc3edde622cd06d` | `caf2c6f4daf187e6` |

**Timing.** Every input is strictly pre-open: filings accepted before 09:30 ET on the trading date, plus screen-time fields only. Each judge is a pinned version released before the window opens and has no web or tool access, so **runs may be batched after the fact**. Batches should run at least monthly, so a retirement notice costs as little as possible. `predictions.csv` is append-only: a pick × judge × repeat is asked once, and the first answer is the record.

**Frozen files (sha256)**

| file | sha256 |
|---|---|
| `judge/run_judge.py` | `30d300bef2c9728777995e714784e5c1f9bd474af9afe0e931d43497273cb403` |
| `judge/grade_judge.py` | `545b76cd423847de44c1b01e4ba4e950a31a7f546359de805d3c146399e1ceef` |
| `judge/build_preopen.py` | `4bec870b999588d8aa5465f68b1a046c734a9012dbed71ebcc4042abb4754988` |
| `judge/PROMPT-1a.md` | `0f0d8981b6f9315f815c8964c5cd1378c40ad3bc9c1265ac57852874f327f6f7` |
| `judge/PROMPT-1b.md` | `bbf6ca5c22cf7a24e55ed58fb2a2bfe435232a632ea4de2911de6d734caa074a` |
| `judge/PROMPT-1c.md` | `7c2836b9012fd7b897dbccd765b657ae5f9dd8b5dcafefe8add354beb2cc3255` |
| `judge/b0_frozen_dd20.json` | `d17662897cff90bf214d6f5194e12022a6cf035f0d7f5b3e7f94ef1f1c5ac228` |
| `judge/stakes_cutpoints_v03.json` | `8f65b890abcb1a50465b7040d3c3e08e73b775dadaa92a82db71354aa619b25f` |
| `filing_lens.py` (via `build_preopen.py`) | `c768ee5a0ad8a45a0a533c231c75f12e39bd40b4c61f349cfe2ff6a80e4823d2` |

## H-JUDGE1 — does an AI judge add drawdown information beyond the score?

**Baselines.** B0 = logistic `dd20 ~ score` (frozen, above). B1 = the window's base rate. BJ = logistic `dd20 ~ B0 + Jev flag_any` (H-JEV1's flag).

**Pass, per judge × arm, at the single verdict look, ticker-cluster-corrected:**
- **Floors:** ≥ 300 graded picks **and** ≥ 100 distinct tickers. If either is unmet at the look, the result is **INSUFFICIENT**: not a fail and not a pass.
- **M1r:** after Platt recalibration fit on the first 100 window picks, holdout ECE ≤ 0.10 and the slope CI includes 1.0. Raw M1 is reported and expected to fail.
- **M2:** AUC cluster CI excludes 0.50.
- **M3:** Brier skill vs B1 > 0, CI excludes 0.
- **M4 (the claim):** ΔAUC over B0 ≥ 0.03, ΔAUC cluster CI excludes 0, **and** the LR test for `dd20 ~ B0 + judge` has p < .05 **after Holm across the fixed family of 6 judge × arm tests**. A judge or arm that is absent or not at verdict counts as p = 1, so a missing arm can never weaken the correction.
- **M5:** ICC(1) across the 3 repeats ≥ 0.80.

**Abstention (v0.3a).** An abstained or unparseable repeat is scored as **B0's forecast** for that pick. Abstained picks are never dropped and count toward the floors. A judge that abstains on everything reproduces B0 and fails M4 by construction. M5 uses non-abstained repeats only.

**Key secondary (reported, not pass/fail):** M4J, the judge's ΔAUC and LR over **BJ** (score + Jev's flag). Also reported: M6 cross-judge ρ; M7 abstention diagnostics; M8 drift by month; M9 confidence → accuracy (J2 only); the dd20 rate by judge-probability quintile.

**Registered priors.** 1a: expected to FAIL M4 (null control). 1b: P(pass) ≈ 0.25 for each judge. B0 is already strong (AUC 0.667), and the filing signal in H-JEV Part A is real but modest. 1c vs 1b: two-sided, no direction predicted. M4J: near zero for J1 (same model, same documents), open for J2.

**Kill conditions.** ICC(1) < 0.60: too noisy to be a rater. Cross-judge ρ < 0.20: "AI judgment" is model idiosyncrasy here.

## H-AUTH1 — a pre-declared rule for when the AI may act alone

**The decision being allocated:** whether a judge's drawdown call could be shown on a pick card automatically, or must go to a human. Shadow mode only: nothing is shown.

**Rule (frozen), per J1 arm 1b prediction (mean of repeats):**
- **AUTO:** |p_dd20 − 0.511| ≥ 0.20, float not in the thin tercile (< 1,438,267 shares), and `dilution_flag` blank.
- **REVIEW:** any other non-abstained prediction.
- **BLOCK:** abstained or unparseable. Deferred to B0 and scored as B0.

**Pass requires both**, on the AUTO subset: (a) judge Brier < B0 Brier on the same picks, with the ticker-cluster CI of the difference excluding 0; and (b) calibration-in-the-large within ±0.10. **Reported:** the AUTO rate, and judge vs B0 Brier on REVIEW picks. The rule should hand humans the cases where the AI is no better.

**Registered prior.** P(pass) ≈ 0.25. This tests whether an authority-allocation rule can be pre-registered and scored like any other hypothesis. It is not a claim that the AI should act.

## Reproduce (on the machine holding `judge/` and the H-JEV state)

```
python3 jev_backfill.py select --from 2026-10-26 --to 2026-12-31     # H-JEV exposure (shared)
python3 judge/build_preopen.py --since 2026-10-26
set -a; . jev.env; set +a                                            # J1 key
python3 judge/run_judge.py --vendor jev    --arm 1a --k 3 --since 2026-10-26   # and 1b, 1c
OPENAI_API_KEY=… python3 judge/run_judge.py --vendor openai --arm 1a --k 3 --since 2026-10-26   # and 1b, 1c
python3 judge/grade_judge.py --registered 2026-10-26 --jev-flags <H-JEV flag_any CSV>   # refuses a verdict before 2027-01-11
```

`grade_judge.py` gates mechanically. Before `--verdict-on` (default 2027-01-11) no judge is ever labelled a verdict. At or after it, both floors must hold or the result is `insufficient`. Holm is applied with `--holm-m 6` (default). A synthetic test on 2026-10-25 confirmed each gate: verdict blocked before the date, `insufficient` when the ticker floor is unmet, and Holm-adjusted p raised correctly with the absent arms counted as p = 1.

**Not registered:** anything that lets judge output touch selection, the site, or a trade.

---

## The three prompts, verbatim

J2 receives these, with `{{RECORD}}` replaced by the JSON screen-time record (`ALLOWED_FIELDS` in `run_judge.py`, ticker included only in 1c) and `{{TEXT}}` by the pre-open filing text (masked in 1b). J1 receives the same record and text through Jev's fixed question block.

### PROMPT-1a.md

```
# AI-Judge prompt — Arm 1a (screen-time fields only, identity MASKED) — v0.3 (drawdown-primary)

You are a forecaster being scored on calibration and discrimination, not on confidence or eloquence.

You will be given the screen-time record of one US microcap stock that a mechanical screener selected before the market opened on the trading date. The ticker is not shown; do not try to identify the company. Nothing after the open is included.

Your task: give two probabilities for this pick.

1. p_dd20 — the probability that the stock trades 20% or more BELOW the trading date's opening price at any time during that trading session or the next five trading sessions. For picks like this, roughly half do.
2. p_pass — the probability that the stock closes on the trading date more than 2% above that day's opening price (a 2% round-trip cost). For picks like this, roughly a third do.

Rules:
- Each probability is between 0.02 and 0.98. Do not give 0 or 1, and do not retreat to 0.5 to avoid commitment.
- If the record gives you no usable basis to move away from those base rates, set abstain to true and still give your best probabilities.
- Confidence is your self-assessment of how much the evidence tells you: low / med / high. It will be checked against your realized accuracy.
- Reason: one sentence, at most 200 characters, naming the specific evidence that drove p_dd20. Do not restate the record.
- You have no tools and no web access. Use only what is below.

Return only this JSON, nothing else:
{"p_dd20": <float>, "p_pass": <float>, "confidence": "<low|med|high>", "abstain": <true|false>, "reason": "<string>"}

Record:
{{RECORD}}
```

### PROMPT-1b.md and PROMPT-1c.md

These are identical to 1a except:
- **The second paragraph.** In 1b: *"You will be given the screen-time record of one US microcap stock that a mechanical screener selected before the market opened on the trading date, plus the text of SEC filings that were public before that day's open. Nothing after the open is included. The company's name and ticker have been replaced with [COMPANY] and [TICKER]; do not try to identify it."* In 1c: the same, but saying the record includes the ticker, and without the masking sentence.
- **The abstain rule** reads *"If the record and filings give you no usable basis…"*.
- **A final block:** *"Pre-open SEC filings (may say none were selected):\n{{TEXT}}"*.

The exact bytes are fixed by the sha256 values above.

---

## Amendment 1 — 2026-10-25, about 40 minutes after registration and before any window pick existed

**What was wrong.** This registration fixes the window as picks traded **2026-10-26 through 2026-12-31**, but neither `run_judge.py` nor `grade_judge.py` enforced the end date. `grade_judge.py`'s `load()` dropped picks before `--registered` and had no upper bound. Judge batches are allowed to run after the fact, so a January batch would have judged January picks, and the grader would have pulled them into the verdict sample: picks outside the registered window, and a sample whose size depends on when the batch happened to run.

**The change, made to the grader only.** `grade_judge.py` gains `--until` (default `2026-12-31`), and `load()` drops any pick with `trading_date > until`. Nothing else changed. `run_judge.py` is untouched; it may still judge later picks, and those predictions are simply never graded under this registration.

**Why this is safe.** At the moment of the change **zero window picks existed** (the window opens with the 2026-10-26 open), `judge/predictions.csv` did not exist, and no judge had been run on any window pick. It enforces the window the registration already states, and it can only shrink the sample to that window. It cannot make a pass easier.

**Verified.** The synthetic smoke test grades the same as before when `--until` covers the data. With `--until` set before the data, it grades nothing.

| file | sha256 (supersedes the row above) |
|---|---|
| `judge/grade_judge.py` | `c745189104a8b03eeff60f0efab0dbb8b2a8a5ddbaf282606dcbe31c886d183d` |

Every other frozen file and hash above is unchanged. The grading command becomes:
`python3 judge/grade_judge.py --registered 2026-10-26 --until 2026-12-31 --jev-flags <H-JEV flag_any CSV>`.

---

## Amendment 2 — 2026-10-25, before the 2026-10-26 open: a reported-only disagreement read

**What is added.** One secondary analysis, `judge/disagree_route.py`. It is **reported only**. It has no pass/fail, it is not in the Holm family, and **nothing it prints can change an H-JUDGE1 or H-AUTH1 verdict**. A routing claim drawn from it needs its own forward registration.

**The question.** Raters who share a prior and still disagree hold different information (Aumann 1976). So on picks where the three raters disagree, does an AI judge do better or worse than the score baseline, compared with picks where they agree? If better, disagreement is a signal to listen to the judge. If worse, disagreement is a signal to defer to B0.

**Fixed now.**
- **Raters, arm 1b only (the H-AUTH1 arm):** B0, J1 = `jev` 1b, J2 = `openai` 1b. Each judge's forecast for a pick follows the registered abstention rule: an abstained or unparseable repeat counts as B0, and the forecast is the mean over repeats. Only picks both judges answered are used. The rest are counted.
- **Disagreement:** D = max − min of the three forecasts. **ASK if D ≥ 0.20**, the same margin as H-AUTH1 AUTO. All other picks are REST.
- **Estimates, per judge J:** Brier(J) − Brier(B0) on ASK, the same on REST, and the difference-in-differences **DiD = ASK − REST**. Each has a ticker-cluster bootstrap 95% CI (2,000 resamples, seed 2026). DiD < 0 means the judge gains on B0 where raters disagree.
- **Also reported:** ASK rate; Brier of B0, J1, J2 and the mean of the three on ASK and REST; the share of ASK picks where J is closer to the outcome than B0; ASK × H-AUTH1 route (AUTO, REVIEW, BLOCK). For this cross-tab only, a pick with missing float counts as thin.
- **Floor:** at least 30 ASK picks on at least 20 tickers, or the read is labelled INSUFFICIENT.
- **When:** once, at the 2027-01-12 readout, with the same window as the grader: `python3 judge/disagree_route.py --registered 2026-10-26 --until 2026-12-31`.

**Why this is safe.** No window pick exists yet, and `judge/predictions.csv` does not exist. No frozen file changes, and every hash above still holds. The script only reads the frozen inputs.

**Smoke test** (synthetic judges on historical v0.3-yf picks, not a result; `judge/_tests/disagree_smoke.py`). A J2 that has real signal on 40% of picks: ASK rate 0.36, J2 DiD −0.21 [−0.22, −0.20]. A J2 that is pure noise on 40% of picks: DiD +0.03 [−0.05, +0.11]. The noise J1: DiD −0.003 [−0.005, −0.000] in the first case and +0.001 [−0.003, +0.005] in the second, so a near-zero DiD can clear zero by chance. That is one reason this read stays reported-only.

| file | sha256 |
|---|---|
| `judge/disagree_route.py` | `d99c00b43b757dcd570adffb5e3f0cd4cfe7fe5b4b04ab28c282a689cda297cb` |
