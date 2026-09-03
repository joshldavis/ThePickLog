# ThePickLog — Audit Log

## 2026-09-03 — The scheduler fix worked, and uncovered a second failure underneath

**The trigger ladder did its job.** All five scan rungs dispatched, ~43 minutes apart (the concurrency group serialising them exactly as intended), and **the first two landed inside the pre-open window**:

| cron | fired (UTC) | ET | inside window? |
|---|---|---|---|
| `0 07` | 11:56:55 | **07:56** | ✅ yes |
| `0 08` | 12:39:54 | **08:39** | ✅ yes |
| `0 09` | 13:23:36 | 09:23 | ✗ (+3m51s past the cutoff) |
| `0 10` | 14:06:45 | 10:06 | ✗ |
| `0 11` | 14:44:45 | 10:44 | ✗ |

Replaying the guards against those exact timestamps returns `early=False, late=False` for the first two: they were cleared to scan.

**They failed anyway.** Run 131's step list: *Verify pre-open timing rules* — success. ***Run scan* — failure.** Whole job 28 seconds, of which ~15 is `pip install`. The scan body died in roughly five seconds, at 07:57 ET, with nothing wrong with the clock.

So a **second, independent failure has been sitting underneath the scheduler problem**, invisible for a week because the pre-open gate refused before the scan body ever executed. `quote_integrity.py` shipped 08-29; the last successful scan was 08-26; **it has therefore never once run in a successful scan** — today was its first real execution. That is suggestive, not proven.

**The diagnosis is INCOMPLETE and this entry says so rather than guessing.** Two hypotheses were raised and both were killed by evidence: a throttled universe fetch cannot be it (16 symbols failing all their retries burns ~144 s in backoff alone, against a 28 s job), and `market_regime()` cannot be it (it catches `Exception` and returns `"unknown"`). What remains needs the run log, and **the run log is unreadable**: GitHub gates Actions logs behind a login, `GET /actions/jobs/{id}/logs` returns 403 unauthenticated, and the browser session available here is signed out.

**⭐ Generalisable lesson, and the reason for the fix below: an apparatus that can explain only ONE failure mode will quietly mislead you about every other one.** The session ledger was built for late dispatches and does that well — five sessions are disclosed in public because of it. But a session lost to a *broken scanner* is exactly as absent from the record as one lost to a late cron, and until today only the second kind left a trace. The record could say *"we were late"* and could not say *"we were broken"*, which reads from outside as though lateness were the only thing that ever goes wrong.

**Shipped:** the scan step now tees its output (`set -o pipefail` is load-bearing — without it `tee`'s exit code wins and a failed scan reports success), and a new `ignitionscan.py record-failure` step writes a `reason=scan error` row into `skipped_sessions.csv` carrying the last error line, for any scan failure the pre-open gate did not already explain. It is idempotent per session, never raises (it runs on the failure path and must not mask the failure it describes), and runs before the existing `if: failure()` committer that pushes the row. **Tomorrow's failure, if there is one, explains itself in public data instead of behind a login.**

**Still open:** the actual cause of the 09-03 scan failure. Six sessions now missing — 08-27, 08-28, 08-31, 09-01, 09-02, 09-03.


## 2026-09-02 — Scheduler correction — **⚠️ the 08-29 fix did not work, and its diagnosis was wrong**

Three more sessions are gone: **08-31, 09-01, 09-02**, on top of 08-27 and 08-28. `picks.csv` still ends 2026-08-26. Five sessions, all permanently unfillable, one lost per trading day for a week.

**The 08-29 diagnosis was wrong, and this entry exists to correct it on the record.** That audit concluded GitHub had *dropped* the `0 11` dispatch, and reasoned from there: *"margin cannot fix a dropped dispatch, only a second independent one can"* → ship a redundant `0 10` cron. The post-fix data refutes the premise. Every dispatch fires. They are all delayed by roughly the same amount:

| session | `0 10` fired | `0 11` fired | delay | outcome |
|---|---|---|---|---|
| 08-31 | 17:22:48Z (+7h23m) | 17:43:21Z (+6h43m) | ~7h | both refused |
| 09-01 | 14:30:03Z (+4h30m) | 15:14:36Z (+4h15m) | ~4.5h | both refused |
| 09-02 | 14:03:35Z (+4h03m) | 14:44:56Z (+3h45m) | ~4h | both refused |

**Redundancy was the wrong axis; margin was the right one — the exact opposite of what was concluded.** A second trigger reading the same delayed clock inherits the delay. Note how narrow it is: on 09-02 the first dispatch landed 14:03Z against a 13:20Z cutoff, **missing by 43 minutes**. Each additional hour of margin genuinely buys back a session. This is a documented GitHub-wide problem, and community reports specifically note that changing the cron minute does not help.

**⭐ Generalisable lesson: a fix inherits the failure mode of the diagnosis it was built on.** "Dropped" and "delayed" produce identical symptoms in the Actions tab — a red run and a missing cohort — and are distinguished only by the *dispatch timestamps*, which nobody looked at until after the fix had shipped and failed. Before designing around a failure mode, confirm which one it is from data that can tell them apart.

**What shipped now**

- **Primary trigger moved off GitHub's scheduler.** `api/cron-scan.js` + a `crons` entry in `vercel.json` fire `workflow_dispatch` from Vercel Cron — a different scheduler on a different clock, which is the only change that actually addresses the cause. Hobby precision is per-hour (±59 min); scheduled at 11:00 UTC it lands 07:00–07:59 ET, inside a 3h20m window. The schedule is deliberately daily rather than Mon–Fri because Hobby rejects expressions it judges to run more than once a day and a rejected cron fails the whole deployment; weekend dispatches are harmless now (see below).
- **The GitHub crons stay as a backup, laddered** to `0 07`/`0 08`/`0 09`/`0 10`/`0 11`. Whichever trigger arrives first logs the cohort; the same-day idempotency guard makes every later arrival a clean no-op, so the ladder is free.
- **The scan window now has a FLOOR as well as a ceiling** (`market_time.SCAN_FLOOR`, 06:00 ET). An early rung — or a punctual Vercel dispatch — can now arrive before pre-market quotes exist, and scanning then would log a cohort priced off the prior session: the 2026-06-19 phantom bug with a new cause. **Too-early is a clean no-op (exit 0, no ledger row); too-late remains a refusal (exit 1, ledger row).** The asymmetry is deliberate — nothing is lost by being early, so it must not consume a session in the public count. A selftest asserts the two guards are disjoint at every hour.
- **The scanner enforces the trading calendar itself** (`is_session`), instead of relying on the cron's `1-5` day field. An external trigger can dispatch any day; the calendar check belongs with the scanner, not the caller.

**Still owner-only:** the Vercel trigger is inert until two env vars exist — `GITHUB_DISPATCH_TOKEN` (fine-grained PAT, this repo only, Actions: Read and write) and `CRON_SECRET`. The endpoint fails loudly with HTTP 500 and names the missing variable rather than silently doing nothing, because a trigger that quietly stops firing is the failure mode this whole exercise exists to eliminate. **Until those are set, the laddered GitHub crons are the only trigger.**

**Not touched:** the grade cron still runs on GitHub's scheduler. Grading has no deadline — a late grade is simply a late grade — and the grader is delicate enough that it should not be changed in the same pass as the thing that is actually broken.


## 2026-08-29 — Weekly verifiability audit — **⚠️ Issues found (3)**

Every published number still re-derives exactly from the raw CSVs — no displayed claim is false. The issues are all in the apparatus and its disclosure: **two trading sessions are simply absent from the log and the site never says so, the watchdog built to catch exactly that could not see it, and one prose sentence now contradicts the table printed directly beneath it.**

**Issue 1 — two market sessions missing from picks.csv, undisclosed. 2026-08-27 (Thu) and 2026-08-28 (Fri) have no cohort.** The log runs 06-09 → 08-26 and stops. Root cause traced end to end: GitHub's best-effort cron dropped the `0 11 * * 1-5` (07:00 ET) scan trigger on both days and dispatched it roughly **ten hours late** — 20:49 UTC on 08-27, 21:16 UTC on 08-28. `market_time.py` did its job and refused: *"refusing to scan — scan started 17:16:43 EDT, at or past the 09:20 ET cutoff … no rows were written."* Exit code 1, red in Actions. **This is the pre-open gate working, not failing** — the exact drift documented in the workflow comment from 2026-08-04, except that this time nothing bad was logged. The 21:00 UTC grade cron drifted too (firing 00:23 / 05:03 / 03:01 UTC the following days) but succeeded, which is why outcomes kept flowing and the gap is easy to miss. **What is wrong is the silence.** The site truthfully says "1019 picks across 49 trading days (2026-06-09 → 2026-08-26)" — it does not claim coverage it lacks — but a stranger cannot tell from the site whether those two sessions were attempted and refused, or never attempted, or produced no candidates. The record discloses late cohorts and ungradeable picks; it has no vocabulary for a *skipped session*. Prescribed fix, in order of value: **(a)** add a redundant early cron (`0 10` alongside `0 11`) with a same-day idempotency guard, so one dropped dispatch still lands pre-open; **(b)** have the refusal write a `SKIPPED` row to a session ledger with the reason and the attempted timestamp, so the gap lives in the public data rather than only in the Actions tab; **(c)** surface a skipped-session count on the Track record beside the late-cohort exclusion.

**Issue 2 — the dead-man's switch is watching the wrong signal, and stayed green through the whole thing.** `watchdog.yml` alerts when `picks.csv OR outcomes.csv OR paths.csv` has gone `STALE_DAYS: 4` without a commit. The grade runs committed outcomes.csv and paths.csv on 08-27, 08-28 and 08-29, so the watched signal never went stale and no issue was filed — while the scan had not run for two sessions. **A watchdog whose freshness test is satisfied by a different job than the one that failed cannot detect that job failing.** It would have taken a full four-day scan outage plus a simultaneous grader outage to trip. Prescribed fix: watch **picks.csv alone**, and assert the *content*, not the commit — the maximum `trading_date` in picks.csv must equal the most recent completed US market session (holiday calendar excepted), alerting at one session of drift rather than four days. This is the standing lesson arriving a third time: the 08-08 audit caught the grader failing silently, the 08-19 UI audit caught prose diverging from its own data, and this one catches **the alarm itself failing silently**. Audit the apparatus, not just the measurements.

**Issue 3 — prose contradicts the table beneath it. "If the score ranked edge, A would beat B would beat C here — it doesn't."** On the Mean net column of that very table, it now does: **A −1.7% > B −1.8% > C −3.3%**, monotone across the first three tiers. The neighbouring sentence in the score explainer — "the hottest tiers (A/B) have shown the deepest drawdowns — **not better returns**" — is half true: the drawdown claim holds cleanly and is still monotonic (avg worst dip A −23.1%, B −18.7%, C −15.5%, D −14.8%), but "not better returns" is false on mean net and true only on median net (A/B −3.4% vs C −2.5% / D −2.7%). **This was predicted in last week's entry** — A-tier stopped being the worst on mean net on 08-22 and has now crossed all the way to best. Direction matters for severity: the site is being *harder on itself* than its data supports, so no reader is pushed toward the product. It is still a sentence a stranger can falsify from the table above it, which is precisely the North Star test. Prescribed fix is the 08-19 contract, not a rewrite: **derive the sentence from the same rows that build the table** — compute whether the ordering is monotone on the displayed metric and say so, and state that no interval separates the tiers (A `[-4.2%, +1.2%] ns` and B `[-4.8%, +1.1%] ns` both include zero, so no tier ordering is established either way). A hardcoded ranking claim under a live table will always eventually invert.

Data checks (recomputed in-browser from the live /picks.csv + /outcomes.csv):

- **Data served:** picks.csv 200 (1,147 rows / 197 KB), outcomes.csv 200 (1,060 rows / 130 KB). ✅
- **Real data shown:** Track record renders **914 real graded rows** with real tickers and dates — no sample fallback, zero occurrences of a sample badge anywhere on the page. ✅
- **No silent gaps (calendar):** ⚠️ **56 distinct trading dates 06-09 → 08-26; 2026-08-27 and 2026-08-28 missing — see Issue 1.** Every other US market weekday since 06-09 is present (Juneteenth 06-19 and the observed 07-03 excepted). One cohort sits on a holiday — 06-19, the known phantom scan — and all 14 rows carry the VOID note; disclosed, not orphaned. Late-cohort derivation reproduces exactly from `published_at`: **7 cohorts / 128 picks** (06-15 (13), 07-06 (16), 07-07 (16), 07-09 (21), 07-13 (21), 07-27 (22), 08-03 (19)), unchanged for a fourth week — **the pre-open gate has now held for 17 consecutive logged sessions since 08-03**, and on 08-27/08-28 it held by refusing outright, with the 08-26 cohort logging at 11:17 UTC (≈07:17 ET).
- **Claims == data (timely, non-VOID):** picks 1,019 ✅ (1,147 − 128 late) · "49 trading days (2026-06-09 → 2026-08-26)" ✅ · graded 914 ✅ · win 32.71% → "33%" ✅ · median net −2.72 → "−2.7%" ✅ · avg worst dip −17.685 → "−17.7%" ✅ · mean net −2.46 · avg 5d-swing net −5.83 · wins 299 / misses 615 ✅. Tier table exact on all five columns: **A 262/201/−1.7%/−3.4%/[−4.2%,+1.2%] ns · B 68/42/−1.8%/−3.4%/[−4.8%,+1.1%] ns · C 283/18/−3.3%/−2.5%/[−4.2%,−2.5%] · D 301/16/−2.5%/−2.7%/[−3.3%,−1.7%]** ✅ (tiers sum to 914, reconciles exactly). The *numbers* are all correct; only the sentence under them is stale — Issue 3.
- **Awaiting-outcome disclosure verified as stated.** The page says "10 picks are more than three sessions past the grading window with no outcome (C: 3, D: 7)". Reproduced exactly, and reproducing it required using a **real** trading calendar including 08-27 and 08-28 — an index-of-logged-cohorts count gives 8 and misses two, which is itself a small confirmation that the site counts sessions correctly even though it did not scan them. **All ten are BNZI.** ✅
- **Honest grading:** SUGP 08-20 (+3.11 = (2.775 − 2.64)/2.64·100 − 2), CODX 08-20 (−0.23), JAGX 08-20 (−1.54) and HKIT 08-20 (+6.80) recompute to the stored value exactly; entry = open, 2% cost haircut, win flag consistent with the sign of net. **Zero duplicate pick_ids** in either CSV, zero regrades, zero rows graded on or before their own trading date. ✅
- **Disclaimers:** educational + not-advice + no-broker-dealer on index; educational + not-advice on method; all three on disclaimer. ✅
- **Validity (six aspects):** (a) **structural — tiers still framed as intensity, not quality.** The site states "Tiers A–D rank that intensity, not quality… read a high tier as a downside flag, not a green light" and nothing anywhere implies higher tier = better, so this aspect **passes on its own terms**; the drawdown evidence behind it is intact and monotonic. The supporting prose has nonetheless drifted from the mean-net column — logged as Issue 3, a disclosure defect, not a reversal of the finding. (b) **external — labelling honest:** the page still leads with "EXPERIMENT 01 FAILED", and "unvalidated" is carried **17×** on index and **2×** on method for the model itself ✅. (c) all three Messick docs return 200 (Validity-Framework 21.9 KB, Domain-Coverage-Spec 7.0 KB, Structural-Justification 6.9 KB) and all three are linked from method.html §9 ✅. Content, substantive, generalizability and consequential claims unchanged from the standing rubric and still either evidence-backed or labelled. ✅

**Chronic item, now escalated — BNZI, 14 consecutive cohorts pending (07-31 → 08-21), 10 of them past the disclosure threshold, up from 5 two weeks ago.** Every other name grades; BNZI never has. The retry loop still does not terminate, so its `UNGRADEABLE` row never gets written and it accrues one new silent pending per session. No published number is wrong — all ten are counted in public — but the count now climbs by one per session indefinitely. The prescribed hard retry cap (10 sessions, then write the `UNGRADEABLE` row with a reason and stop) has been outstanding since 08-15 and would now fire on all ten at once. **Separately: GitHub Issue #2 from the 2026-08-08 audit is still open although the 08-15 audit confirmed its fix landed.** A resolved alarm left open erodes the channel this design depends on; it should be closed.

Grading forward this week: 08-24 (24) → grades 08-31; 08-25 (24) → 09-01; 08-26 (24) → 09-02. **Then nothing — the grader has no cohort to grade on 09-03 or 09-04, because the 08-27 and 08-28 scans never happened. The gap propagates forward a week.** Plus the 14 BNZI stragglers, which only clear if the grader retries successfully or writes their UNGRADEABLE rows.

### ❌ CORRECTION, same day — the BNZI diagnosis above (and in the 08-15 and 08-22 entries) was WRONG

**What I claimed, three weeks running:** *"The retry loop is not terminating, so its `UNGRADEABLE` row never gets written."* **That is false.** The retry cap exists and works. `cmd_grade` declares a symbol dead at `tds > 20` sessions, and BNZI's oldest pending pick (07-31) sits at exactly 20 — it goes terminal on Monday 08-31. Nothing was stuck; it was one session short of the cap I said didn't exist. I asserted a mechanism failure across three published entries without ever reading the mechanism.

**This is the Swing Terminal lesson arriving from the other direction.** That teardown recorded: *before publishing a finding about someone else's record, first reproduce the part of their data that is known-good — if your method can't reproduce their correct rows, your method is the defect.* The same discipline applies to our own apparatus, and I skipped it: BNZI had graded normally 38 times before 07-31, which I never checked, and which immediately rules out "chronically unpriceable ticker."

**What is actually wrong — and it is worse, and it is on the scan side.** BNZI's pick rows are **byte-identical every session from 2026-08-11 to 2026-08-26**: price `1.91`, gap **exactly `0.00%`**, RVOL `0.59`, float `1352833`. Twelve consecutive sessions. A live stock does not gap exactly 0.00% twelve times running. The stock halted around 07-31, our price source kept returning its last quote forever, and the scanner logged a fresh "pick" every session against a price that no longer existed. **Those twelve were never forecasts.** The five picks from 07-31 → 08-10 are different and legitimate: real, varying screens that became ungradeable when the stock halted. The 08-07 pick was real and graded normally.

This is the **same defect as the phantom 2026-06-19 cohort, one level down.** `_is_stale_duplicate_scan` compares a *whole cohort* to the prior session, so it catches a dead feed — but it is blind to a single dead ticker inside a live cohort, because the other 23 names moved normally.

**Restatement.** A derived stale-quote exclusion now removes those 12 rows from published counts, on the same terms as the late-cohort exclusion: computed in-browser from public `picks.csv`, nothing deleted, reproducible by a stranger. Effects, in full:

- **Picks logged 1,019 → 1,007.**
- **Awaiting-outcome 10 → 5** (07-31, 08-04, 08-05, 08-06, 08-10 — all genuine halt casualties).
- **Zero graded picks are affected, so no return, win rate, median, tier or calibration figure on the site moves at all.** The 12 were all ungraded; that is why this went unnoticed — it inflated a count, not a performance number.

**The rule earns its right to remove public rows three ways:** it is *derived* rather than stored; it is *not threshold-tuned* (requiring the quote tuple to repeat 2 or 3 times gives the identical 12 rows); and it *validates on known-good data* — run without the session filter it independently rediscovers the already-confirmed 06-19 phantom cohort (CUPR, GCDT, PW, IOTR, BJDX) without being told it exists. The Python and the in-browser JS were checked for byte-identical output on the live log before shipping.

**Generalisable lesson, and the reason this entry exists:** *a chronic anomaly is evidence about the apparatus, not a fact about the world.* BNZI failing every day for a month was never "a stubborn ticker" — it was the system telling me something was broken upstream, and I spent three weeks writing down the symptom as though it were the diagnosis. When the same name fails the same way every day, stop describing it and go read the code that produces it.

**Update, same day — Issues 1 and 2 are fixed (commit `9fc9e3d`).** Issue 3 and the BNZI item are addressed in commit `d498de9`.

- **Redundant scan cron.** A second trigger at `0 10 * * 1-5` now runs alongside `0 11`. Margin cannot fix a *dropped* dispatch — only a second independent one can — so both must now be missed to lose a session. A same-day idempotency guard in the workflow's `Decide command` step makes whichever cron lands second a clean no-op. That guard is load-bearing rather than tidiness: the scanner dedupes on `(ticker, trading_date)`, so a second scan an hour later screens a moved market and would append *different* tickers to the same cohort, inflating it with names chosen after the first look.
- **Watchdog rewritten to assert content instead of commit recency.** It now runs `watchdog_check.py`, which requires the newest `trading_date` in **picks.csv alone** to be the session the scanner already owed — evaluated against the 09:20 pre-open cutoff, not the 09:30 bell, because the scanner logs *before* the open. Threshold is one session, not four days: a missed cohort is unrecoverable, so the alarm has to fire while the next morning's run can still be dispatched by hand. **Regression-tested against this very outage: it reports `GAP=2, MISSING=2026-08-27,2026-08-28`** — the failure the previous version slept through. `NYSE_HOLIDAYS` moved into `market_time.py` so the scanner and the watchdog share one calendar; the new session helpers are covered by that module's selftest, which the watchdog job runs before the check.
- **Deliberately not done:** the `SKIPPED` session ledger and the Track record disclosure (Issue 1's items b and c). Those want a derived data contract rather than a hand-written note that goes stale — the same reasoning that made the late-cohort exclusion derived from `published_at` instead of a stored flag.
- **Expect one redundant alarm.** The new watchdog will file a correctly-reasoned issue about 08-27/08-28 until the next successful scan. The gap is real and permanently unfillable, so the alarm is right, merely duplicative of Issue #3; it self-clears on the first good Monday scan because the check measures forward from the newest logged cohort.

**Second update — Issue 3, the BNZI correction above, and the two remaining Issue-1 items all shipped.**

- **Frozen-quote guard (scan side, the root cause).** `quote_integrity.py` refuses to publish a candidate whose `(price, gap, RVOL, float)` has not moved since the last time we screened it. This stops the source; the derived exclusion cleans the existing rows.
- **Per-ticker death rule (grade side).** The per-pick cap waits ~20 sessions before declaring a name dead, which is right for *one* pick whose fetch might be transient — but it is the wrong evidence when the *same ticker* has failed across six or more past-due cohorts in a single run. That is one dead symbol, not six transient outages. All six remaining BNZI stragglers now clear on the next grade run instead of trickling out one per session for three more weeks.
- **`_trading_days_since` now counts real sessions, not weekdays.** It treated market holidays as trading days, so every threshold expressed in that unit — including the retry cap that decides when a name is declared dead — ran fast across a holiday week. No published return was ever wrong (the window check caught it downstream), but the unit was not the one the comments claimed. It now shares one calendar with the scanner and the watchdog.
- **Skipped-session ledger (Issue 1b/1c).** The pre-open refusal writes `skipped_sessions.csv` (date, attempted timestamp, reason), idempotent per session, and the Track record discloses the count and links the file. Because a refused scan exits 1 and skips every later step — which is exactly why 08-27 and 08-28 left no public trace — the ledger gets its own committer that runs `if: failure()`. The two known sessions are backfilled and **explicitly marked RECONSTRUCTED** in the `detail` column, since the ledger did not exist when they were refused.
- **Tier caption derived (Issue 3).** The sentence is computed from the same `tierStats` that renders the table, reports whether the ordering is monotone on the displayed metric, and names which intervals separate from zero. It reads correctly today and will invert itself automatically rather than going stale again.
- **Healthchecks ping narrowed to the scan.** It was `if: success()`, so the nightly grade run pinged the monitor and kept it green straight through the scan outage — the same blind spot as the old watchdog, in a second place. The scan is the unrecoverable half, so it now owns the ping alone.
- **GitHub Issue #2 closed**, ~3 weeks after the 08-15 audit confirmed its fix.
- **Workflow serialised (`concurrency` group).** The same-day idempotency guard above is only sound once the first run has *pushed*. GitHub runs concurrent dispatches in PARALLEL, so under the very drift the second cron exists to survive, the 10:00 and 11:00 scans can arrive a minute apart: both check out a `picks.csv` with no cohort for today, both therefore PASS the guard (it reads the file and cannot see another runner mid-scan), and the second appends a *different* set of tickers to the same session, screened against a market that has moved. That is the exact cohort inflation the guard was written to prevent, surviving the guard. A `concurrency` group with `cancel-in-progress: false` queues the second dispatch behind the first, so it starts after the push, sees the cohort and no-ops. **The guard and the group are load-bearing only together** — found while reviewing `9fc9e3d` and `d498de9`, neither of which is wrong, but both of which assume a serialisation the workflow did not have.

Still open and deliberately not done: nothing from this audit. The next verifiability audit should confirm picks-logged reads 1,007, awaiting-outcome reads 5 (then 0 once the death rule fires), the skipped-session note renders, and BNZI stops appearing in new cohorts.

## 2026-08-22 — Weekly verifiability audit — **✅ All claims verify**

Every published number re-derived in-browser from the raw CSVs and matched to the site, to the displayed decimal. **Both of last week's open items closed themselves:** the partial 08-14 grader run recovered (all 7 stragglers from the 08-07 cohort are graded), and the 5 previously-disclosed overdue picks now carry explicit outcomes rows instead of sitting silent. One chronic item remains and is correctly disclosed, not hidden.

- **Data served:** picks.csv 200 (1,075 rows / 185 KB), outcomes.csv 200 (944 rows / 116 KB). ✅
- **Real data shown:** Track record renders 798 real graded rows with real tickers and dates — no sample fallback. ✅
- **No silent gaps (calendar):** 53 distinct trading dates 06-09 → 08-21; **zero missing US market weekdays** (Juneteenth 06-19 and the observed 07-03 excepted). One cohort sits on a holiday — 06-19, the known phantom scan — and all 14 rows carry the VOID note; disclosed, not orphaned. Late-cohort derivation reproduces exactly from `published_at`: **7 cohorts / 128 picks** (06-15 (13), 07-06 (16), 07-07 (16), 07-09 (21), 07-13 (21), 07-27 (22), 08-03 (19)), unchanged for a third week — **the pre-open gate has now held for 14 consecutive sessions since 08-03**, with the 08-21 cohort logging at 11:14 UTC (≈07:14 ET). ✅
- **Claims == data (timely, non-VOID):** picks 947 ✅ (1,075 − 128 late) · 46 timely trading days ✅ · graded 798 ✅ · win 32.46% → "32%" ✅ · median net −2.655 → "−2.7%" ✅ · mean net −2.858 → "−2.9%" ✅ · avg worst dip −17.55 → "−17.6%" ✅ · avg 5d-swing net −5.47 → "−5.5%" ✅ · wins 259 / misses 539 / pending 130 / all 947 — reconciles exactly ✅. Tier table exact on all four columns: A 211/165/−3.1/−2.7, B 66/42/−2.0/−3.4, C 255/18/−3.2/−2.6, D 266/16/−2.6/−2.6 ✅. Calibration bands exact on both n and win rate: 264/27%, 225/31%, 53/36%, 44/41%, 48/27%, 164/42% (sums to 798) ✅.
- **Awaiting-outcome disclosure verified as stated.** The page says "5 picks are more than three sessions past the grading window with no outcome (C: 3, D: 2)". Reproduced exactly — and the threshold is exactly as worded: a pick counts once **more than** 8 sessions have elapsed (5-day window + 3), which admits 07-31 (C), 08-04 (C), 08-05 (D), 08-06 (C), 08-10 (D) and correctly excludes 08-11 onward at 8 sessions. **All five are BNZI.** ✅
- **Last week's two open items, both resolved:** (1) the 08-14 partial grader run — all 7 names that missed (BNZI, CUPR, NCT, SVRN, RKDA, IOTR, BYAH) have graded; it was a transient batch failure, not per-ticker unpriceability, as suspected. (2) The prescribed UNGRADEABLE fix has landed on the backlog: WAI 07-16, PRPL 07-20, GREE 07-21 and GREE 07-22 now carry `no entry bar` rows and SLAI 07-17 carries `UNGRADEABLE: only 1 of 6 sessions ever printed — halted or delisted mid-window`. They no longer inflate the awaiting count. ✅
- **Honest grading:** GCDT 08-13 (+20.14 = (0.513 − 0.42)/0.42·100 − 2), IOTR 08-13 (−0.71), JAGX 08-13 (−2.13) and SUGP 08-13 (−2.50) recompute to the stored value exactly; entry = open, 2% cost haircut, win flag consistent with the sign of net. **Zero duplicate pick_ids** in either CSV, zero regrades, zero rows graded on or before their own trading date. ✅
- **Disclaimers:** educational + not-advice + no-broker-dealer on index; educational + not-advice on method; all three on disclaimer. ✅
- **Validity (six aspects):** (a) **structural — tiers still framed as intensity, not quality.** The site states "Tiers A–D rank that intensity, not quality… read a high tier as a downside flag, not a green light" and the glossary repeats "how hot the setup is, not how good"; the tier-table commentary says outright "If the score ranked edge, A would beat B would beat C here — it doesn't." The data backs both: A beats B on nothing (A −3.1% vs B −2.0% mean net), and **drawdown is still monotonically deeper by heat** — avg worst dip A −22.7%, B −18.1%, C −15.6%, D −15.2%. Nothing on the site implies higher tier = better ✅. (b) **external — labelling honest:** the page leads with "EXPERIMENT 01 FAILED", and "unvalidated" is still carried on both index (×2) and method (×2) for the model itself ✅. (c) all three Messick docs (Validity-Framework 22.5 KB, Domain-Coverage-Spec 7.2 KB, Structural-Justification 7.1 KB) return 200 and all three are linked from method.html §9 ✅. Content, substantive, generalizability and consequential claims unchanged from the standing rubric and still either evidence-backed or labelled. ✅

**Note for the standing rubric, not a failure: A-tier is no longer the single worst mean net.** It was −3.98% on 08-15; it is −3.10% today, and C-tier (−3.19%) is now marginally worse. The *drawdown* half of the structural finding is untouched and still cleanly monotonic, and the site never asserts "A is worst on mean" — it asserts the tiers don't rank edge, which holds. But if a future page starts leaning on "A-tier has the worst return" as the headline, that specific sentence would now need re-deriving before it ships. This is the general lesson from the 08-19 UI audit arriving again: a prose sentence asserting a ranking must be computed from the table beneath it, not from the week it was written.

**Chronic item still open — BNZI, now 10 consecutive cohorts (07-31 → 08-14, including the late 08-03).** Every other name grades; BNZI never has. The retry loop is not terminating, so its `UNGRADEABLE` row never gets written and it accumulates one new silent pending per session. Five of the ten have crossed the disclosure threshold and are being counted in public, so no published number is wrong — but the count will keep climbing by one per week until the grader gives up. Prescribed fix, unchanged from 08-15: hard retry cap (e.g. 10 sessions), after which the grader writes the `UNGRADEABLE` row with the reason and stops retrying. That cap would fire on BNZI this week.

Grading forward this week: 08-17 (25) → grades 08-24; 08-18 (24) → 08-25; 08-19 (24) → 08-26; 08-20 (24) → 08-27; 08-21 (24) → 08-28. Plus the 10 BNZI stragglers, which only clear if the grader retries successfully or writes their UNGRADEABLE rows.

## 2026-08-15 — Weekly verifiability audit — **✅ All claims verify**

Every published number re-derived in-browser from the raw CSVs and matched to the site, to the displayed decimal. Last week's grading gap is **closed as a disclosure defect**: the Track record now states the awaiting-outcome count and tier split in plain language, and the number it prints is exactly reproducible. One watch item recorded below (a partial 08-14 grader run), not a failed claim.

- **Data served:** picks.csv 200 (954 rows / 164 KB), outcomes.csv 200 (811 rows / 100 KB). ✅
- **Real data shown:** Track record renders 669 real graded rows with real tickers and dates — no sample fallback. The only "sample" string on the page is the owner-only live-quote note on today's screen (data-vendor licensing), which is not a fallback badge. ✅
- **No silent gaps (calendar):** 48 distinct trading dates 06-09 → 08-14; **zero missing US market weekdays** (Juneteenth 06-19 and the observed 07-03 excepted). One cohort sits on a holiday — 06-19, the known phantom scan — and all 14 of its rows carry the VOID note; it is disclosed, not orphaned. Late-cohort derivation reproduces exactly from `published_at`: **7 cohorts / 128 picks** (06-15, 07-06, 07-07, 07-09, 07-13, 07-27, 08-03), unchanged from last week — **the pre-open gate has held for 9 consecutive sessions since 08-03**, with the last five cohorts logging at 11:34–11:38 UTC (≈07:35 ET), comfortably pre-open. ✅
- **Claims == data (timely, non-VOID):** picks 826 ✅ (954 − 128 late) · 41 timely cohorts ✅ · graded 669 ✅ · win 32.0% → "32%" ✅ · median net −2.78 → "−2.8%" ✅ · mean net −3.20 → "−3.2%" ✅ · avg worst dip −18.12 → "−18.1%" ✅ · avg 5d-swing net −5.90 → "−5.9%" ✅ · wins 214 / misses 455 / pending 142 ✅ (669 graded + 142 pending + 14 VOID + 1 ungradeable = 826, reconciles exactly). Tier table exact on all four columns: A 161/123 tickers/−3.98/−3.24, B 62/40/−2.60/−3.64, C 219/18/−3.36/−2.62, D 227/16/−2.64/−2.66 ✅. Score-bucket counts and win rates exact (n=225/190/51/41/40/122; 28/32/37/37/30/37%) ✅.
- **Awaiting-outcome disclosure verified as stated.** The page says "5 picks are more than three sessions past the grading window with no outcome (A: 3, B: 1, C: 1)". Reproduced exactly: SLAI 07-17 (A), PRPL 07-20 (A), GREE 07-21 (B), GREE 07-22 (A), BNZI 07-31 (C). The sixth candidate a naive count would add — BNZI 08-03 — is correctly absent because 08-03 is itself a late cohort and excluded from every number on that page. The prescribed fix from 08-08 is working in the direction that matters: WAI 07-16 now carries an explicit `no entry bar` outcomes row instead of vanishing, and the remaining five are counted in public rather than dropped. ✅
- **Honest grading:** KRO 08-07 (+1.49 = (8.59 − 8.30)/8.30·100 − 2) and WLDS 08-07 (−2.95) recompute to the stored value exactly; entry = open, 2% cost haircut, win flag consistent with sign of net. **Zero duplicate pick_ids** in either CSV, zero regrades. ✅
- **Disclaimers:** educational + not-advice + no-broker-dealer on index; educational + not-advice on method; not-advice + broker-dealer on disclaimer. ✅
- **Validity (six aspects):** (a) **structural — tiers still framed as intensity, not quality.** The site states "Tiers A–D rank that intensity, not quality… read a high tier as a downside flag, not a green light" and the glossary repeats "how hot the setup is, not how good". The data still backs it: A-tier has the **worst mean net (−4.0%)** and drawdown is **monotonically deeper by heat** — avg worst dip A −24.2%, B −18.4%, C −16.4%, D −15.4%. Nothing on the site implies higher tier = better ✅. (b) **external — labelling honest:** the page leads with "EXPERIMENT 01 FAILED · verdict 2026-07-29 · n=309 · −3.0pp vs baseline" (the published Gate-1 FAIL supersedes "unvalidated"), and "unvalidated" is still carried on both index and method for the model itself ✅. (c) all three Messick docs (Validity-Framework, Domain-Coverage-Spec, Structural-Justification) return 200 and are all three linked from method.html §9 ✅. Content, substantive, generalizability and consequential claims unchanged from the standing rubric and still either evidence-backed or labelled. ✅

**Watch item (not a failed claim): the 08-14 grader run was partial.** The 08-07 cohort came due on 08-14 and **7 of its 25 picks got no outcomes row** — BNZI (C), CUPR (C), NCT (C), SVRN (D), RKDA (D), IOTR (D), BYAH (B). Every prior cohort has missed at most **one** name (always the chronic unpriceable ticker), so 7 is a 7× spike, and six of the seven graded normally on other dates — which argues batch failure, not per-ticker unpriceability. They are still inside the retry window so no published number is wrong today. If they are still missing at the next audit they will cross the disclosure threshold and the awaiting-outcome count will jump from 5 to ~11. Worth a look at the 08-14 grader logs before then. Separately, **BNZI has now failed to grade on 8 consecutive cohorts** (07-31 → 08-11) — that is the retry loop never terminating, so its `UNGRADEABLE` row never gets written; consider a hard retry cap (e.g. 10 sessions) after which the grader writes the row and stops.

Grading forward this week: 08-10 (25) → grades 08-17; 08-11 (25) → 08-18; 08-12 (25) → 08-19; 08-13 (26) → 08-20; 08-14 (26) → 08-21. Plus the 7 stragglers from the 08-07 cohort and the 5 disclosed overdue picks, which only clear if the grader retries successfully or writes their UNGRADEABLE rows.

## 2026-08-08 — Weekly verifiability audit — **⚠️ Issues found (1)**

Live site fetched and every published number re-derived from the raw CSVs — all displayed claims verify. One integrity gap found in the grading apparatus: six picks past their 5-trading-day grading mark have silently never been graded.

**The issue — silent grading gap, skewed toward A-tier.** These picks have no outcomes row and no VOID note, weeks past their grade date: WAI 07-16 (A), SLAI 07-17 (A), PRPL 07-20 (A), GREE 07-21 (B), GREE 07-22 (A), BNZI 07-31 (C). Cohort-mates on the same dates graded normally (e.g. the rest of the 07-31 cohort graded 08-07), so this is per-ticker — most likely halts/delistings where the grader can't fetch prices and skips without writing anything. Two problems: (1) the grader fails silently, the exact failure mode the pre-open gate was built to eliminate on the scan side; (2) **4 of the 6 are A-tier** — if ungradeable names (halts, delistings) concentrate in the hottest tier and drop out of the record, the published A-tier mean is flattered by survivorship. Prescribed fix: grader writes an explicit outcomes row (note=UNGRADEABLE, reason) for any pick it cannot price at grade time; CI check that fails loudly if any pick older than its grade window has no outcomes row; Track record page discloses the count.

Data checks (recomputed in-browser from /picks.csv + /outcomes.csv):

- **Data served:** picks.csv 200 (827 rows / 145 KB), outcomes.csv 200 (705 rows / 89 KB). ✅
- **Real data shown:** srcBanner = "Live data"; Track record renders 582 real graded rows (real tickers/dates), no sample fallback. ✅
- **No silent gaps (calendar):** 43 distinct trading dates 06-09 → 08-07, zero missing market weekdays (Juneteenth + observed 7/4 excepted). The 06-19 holiday cohort = the known phantom cohort, all 14 rows VOID — disclosed, not orphaned. Late-cohort derivation reproduces exactly: 699 timely / 128 late / 7 cohorts, matching the site's exclusion list to the pick. ✅
- **Claims == data (timely, non-VOID):** picks logged 699 ✅ · graded 582 ✅ · win 30.6% → "31%" ✅ · median net −2.96 → "−3.0%" ✅ · mean net −3.58 → "−3.6%" ✅ · avg worst dip −18.96 → "−19.0%" ✅ · avg 5d-swing −6.85 → "−6.8%" ✅ · tier table exact match (A 125/−5.3, B 53/−3.1, C 195/−3.3, D 209/−3.0) ✅. Note: the tier table now leads with MEAN NET + clustered CIs, not win rate — the old P1 win-rate/mean-net mismatch is resolved.
- **Honest grading:** spot checks PW 06-09 (+5.0 = (10.40−9.72)/9.72·100−2) and GCDT 06-09 (−5.32) recompute exactly; win flags consistent; zero duplicate pick_ids in either CSV, zero regrades. ✅
- **Disclaimers:** educational + not-advice + no-broker-dealer present on index; educational/not-advice on method; not-advice/broker-dealer on disclaimer. ✅
- **Validity (six aspects):** (a) tiers presented as heat ("⚠ hot"/"○ cool") and the tier table explicitly states A does NOT beat B/C — no quality-ranking implication ✅; (b) model labelling honest: index leads with "EXPERIMENT 01 FAILED" (published Gate-1 FAIL supersedes "unvalidated"); method.html still carries "unvalidated" ✅; (c) all three Messick docs return 200 and are linked from method.html §9 ✅.

Grading forward this week: 08-03 (19, late cohort — grades for the record, excluded from headline) → grades 08-10; 08-04 (24) → 08-11; 08-05 (24) → 08-12; 08-06 (24) → 08-13; 08-07 (25) → 08-14. Plus the 6 stragglers above, which need the fix before they'll ever grade.

## 2026-08-04 — **❌ CORRECTION: 128 picks were logged after the opening bell**

**Severity: HIGH — this contradicted the site's central claim.** Found by an outside review of the public `picks.csv`, not by us. Full public write-up: `/late-cohorts.html`.

**The defect.** The daily scan is scheduled on GitHub Actions for 07:30 ET. Actions cron is documented as *best-effort*; under load it drifts. On **7 sessions** it drifted past the 09:30 ET opening auction and logged anyway: **128 picks**, 2 to 72 minutes late.

| session | picks | scan ran (ET) | vs open |
|---|---|---|---|
| 2026-06-15 | 13 | 09:32 | +2 min |
| 2026-07-06 | 16 | 10:42 | +72 min |
| 2026-07-07 | 16 | 09:33 | +3 min |
| 2026-07-09 | 21 | 10:04 | +34 min |
| 2026-07-13 | 21 | 09:34 | +4 min |
| 2026-07-27 | 22 | 09:53 | +23 min |
| 2026-08-03 | 19 | 09:57 | +27 min |

Every affected cohort is late **in its entirety** — the whole morning scan, not stragglers. The headline metric is the same-day open→close return, so a pick logged at 09:32 was scored against an opening price that had already printed. That is not a forecast.

**Root cause.** `cmd_scan` guarded against NYSE holidays and against a stale/duplicate quote feed (added after the 2026-06-19 phantom cohort) but **never checked the wall clock**. We guarded the market and the data and forgot to guard the deadline.

**Impact on published numbers.** Graded rows, excluding VOID:

| group | n | mean net | median net | win |
|---|---|---|---|---|
| as published | 596 | −2.68% | −2.72% | 30.9% |
| **timely only (corrected)** | 487 | **−3.40%** | −2.76% | 31.2% |
| late cohorts | 109 | +0.55% | −2.48% | 29.4% |

**We do NOT claim the violation flattered the record.** The mean gap is +3.95pp but the **median gap is +0.28pp**, and the entire mean difference is one position — JLHL +240.9% on 07-09. Drop it: late mean −1.67%. Drop the top three: −2.99%, indistinguishable from timely. Late-cohort medians are −4.07/−2.88/−1.10/−1.65/−2.83/−2.26, all negative and ordinary. Per Experiment 01's own lesson (delete your best trade and look again), the protocol failure is real and the contamination is not measurable. Both halves are stated publicly.

**Impact on Experiment 01 — verdict UNCHANGED.** Five of the seven cohorts fall in its window: in-window 461 graded mean −2.64%; timely-only 365 mean **−3.65%**. The published FAIL stands, by a slightly wider margin. No verdict anywhere reverses.

**Remediation (all shipped this commit):**
1. **Hard pre-open gate** — new `market_time.py`; `cmd_scan` and `cmd_scan_market` resolve now in `America/New_York` and `sys.exit` non-zero at or after **09:20 ET** for the target session. A late run writes nothing. 10-minute margin so a near miss fails loudly rather than landing by luck.
2. **Scan cron moved 07:30 → 07:00 ET** for margin. The gate is the guarantee; the cron is convenience.
3. **`today` is now derived in market time**, not the CI runner's UTC clock.
4. **Exclusion is DERIVED, not stored** — no hand-set flag. `market_time.is_timely()` (Python) and `isTimelyPick()` (index.html, dashboard.html) compute it from `published_at` × `trading_date`, so anyone can reproduce our exact exclusion set from the public CSV. Three independent implementations agree: 602 timely / 128 late / 7 cohorts.
5. **DST handled** via `zoneinfo` / `Intl` with an explicit zone — 09:30 ET is 13:30Z in summer, 14:30Z in winter; hard-coding either breaks the check for half the year. Selftest covers both directions and **gates the CI job**.
6. **Rows are NOT voided.** They stay in `picks.csv` with their outcomes. Unlike the 06-19 phantom cohort (a session that never happened), these were real scans logged late — the honest remedy is exclude-and-disclose, not delete.
7. **Every surface excludes them and says what it dropped**: landing KPI strip, Track record, `dashboard.html`, `weekly_report.py`, `hypo_eval.py`. No silent truncation.
8. **Weekly audit now checks timeliness**, so a recurrence surfaces in days rather than six weeks.

**Also corrected:** the Track record page described the headline as a 5-day grading without stating that the headline number is the **same-day open→close** and that the 5-day wait exists to measure MFE/MAE/path. Reworded.

**Process note.** This was in a file we have published for weeks. We never ran the check on our own data; a reader did. The lesson recorded for future audits: *audit the measurement apparatus, not just the measurements.*

## 2026-08-01 — Weekly verifiability audit — **✅ All claims verify**

Live site fetched same-origin from https://thepicklog.vercel.app (build `2026-07-31 18:13 ET · 0cd0ff2`); every displayed number recomputed independently from the raw CSVs. All six data checks pass and the six-aspect validity labelling is honest. One **new** data-hygiene issue found — five picks are stuck permanently ungraded by a transient-retry path that never terminates. No displayed claim is affected.

**Six data checks:**
- **1. Data served — PASS.** `/picks.csv` HTTP 200 (124,508 B, **711** rows), `/outcomes.csv` HTTP 200 (74,699 B, 588 rows = **574 graded** + 14 VOID Juneteenth placeholders). `/candidates.csv`, `/control_outcomes.csv`, `/leaderboard.json` (generated_at `2026-07-31`) all 200.
- **2. Real data shown — PASS.** Track record renders the live log — "711 picks logged" and "574 graded" match the CSVs exactly. No sample-fallback badge; the only "sample" string on-site is "out-of-sample" in the pricing block.
- **3. No silent gaps — PASS.** **38** trading dates, 2026-06-09 → 2026-07-31. Every US market weekday present; the only absence is the observed July 4 holiday (07-03), which correctly has no cohort. New sessions 07-27 → 07-31 all logged (22/24/24/24/24), so the daily scan is running loudly. No **new** holiday cohort since the 06-28 phantom fix — the 06-19 Juneteenth rows are the known, explicitly VOID-noted set.
- **4. Claims == data — PASS, exact on every figure.** Recompute vs site: picks **711**=711; graded **574**=574; win rate 30.31% → site **30%**; median net −2.72% → **−2.7%**; mean net −2.91% → **−2.9%**; avg worst dip −19.21% → **−19.2%**. Win-by-tier: A 31% (n=110), B 33% (n=42), C 34% (n=189), D 26% (n=233) — all four match. All six calibration buckets match exactly (0–44 n=231/26%/−2.6%; 45–54 n=161/34%/−3.3%; 55–64 n=41/34%/−1.6%; 65–74 n=30/33%/−4.6%; 75–84 n=24/38%/−0.6%; 85–100 n=87/29%/−3.8%). Best 5d-net **+661.2%** (DFNS, 07-22). Ledger reconciles: 574 graded + 123 pending + 14 void = 711.
- **5. Honest grading — PASS.** 0 duplicate `pick_id` in picks.csv, 0 duplicate outcome rows (no regrades), 0 orphan outcomes, **0** rows where the `win` flag disagrees with the sign of the net return. Entry = session open with a flat 2pp haircut, verified on spot checks: PW 06-09 open 9.72 → close 10.40 = +6.99% gross → **+5.0% net**; GCDT 06-09 0.693 → 0.67 = −3.32% gross → **−5.32% net**.
- **6. Disclaimers — PASS.** index: "Educational / informational use only", "Nothing here is investment advice", "We are not a broker-dealer or registered investment adviser". method.html: "Educational / informational only — not investment advice". disclaimer.html: "We are not a registered investment adviser or broker-dealer". *(Minor wording note: disclaimer.html carries the adviser/broker-dealer and not-advice language but not the literal word "educational" — it lives on index and method. Cosmetic only.)*

**Six-aspect validity (Messick):**
- **Structural — honest.** method.html states it explicitly: *"the top tier historically has the worst mean net and the deepest drawdowns — which is exactly why tiers are labelled as a heat scale, not a quality grade."* On-site tier chips read `A ⚠ hot` / `D ○ cool` — intensity, not rank. **Nowhere does the site imply higher tier = better.** Data confirms the drawdown half of the standing finding cleanly and monotonically: mean MAE by tier A **−27.3%** > B −19.7% > C −18.3% > D −16.0%.
- **Precision note on that sentence.** "Worst mean net" is not literally true on current data — A-tier mean net is −3.1% while **B-tier is −4.1%** (C −2.9%, D −2.6%). The claim errs *against* the model (self-critical, non-promotional) so it is not a validity failure, but on a site whose entire pitch is that its numbers survive checking, accuracy should cut both ways. **Suggested fix:** reword to "the top tier has the deepest drawdowns and no better net return than the bottom tier" — which the data supports exactly.
- **Content / substantive / generalizability / external / consequential — all six aspects named and addressed** in method.html, with Messick cited by name.
- **Unvalidated label — present.** method.html 2×: *"Until the data clears the bar the model is treated as unvalidated"* and *"The model is unvalidated until the sample and out-of-sample bars above are cleared."* Index carries the PROTOTYPE banner, the "we tested our own screener, it lost" framing, and the explicit "our picks as a group have lost money so far". Gate-1's external verdict (published FAIL, 2026-07-29) is rendered on `gate.html` and `experiment-01.html`, both 200.
- **Validity docs — reachable + linked.** All three return HTTP 200 and are linked from method.html §9: Messick Framework (22,455 B), Domain-Coverage Spec (7,190 B), Structural-Justification (7,071 B). `experiments.html`, `experiment-01.html`, `experiment-02.html`, `trust.html` all 200.

**⚠️ New data-hygiene issue — five picks stuck permanently ungraded (no claim affected).**
Last week's audit predicted ~123 grades landing 07-23 → 07-29 from the 07-16…07-22 cohorts. **118 landed; five did not:** `WAI` (07-16), `SLAI` (07-17), `PRPL` (07-20), `GREE` (07-21), `GREE` (07-22) — all v0.3-yf, all now well past their 5-session mark. Cause is `ignitionscan.py:433-442`: a missing price fetch is classified **transient** and the row is left ungraded "so the next run retries." For a delisted/halted/renamed ticker that fetch never succeeds, so the retry loop never terminates and the pick sits pending forever. This is honest as displayed (they show as Pending, nothing is fabricated or deleted) but it is a slow leak: the pending pool accretes un-gradeable rows that quietly dilute the "Pending (123)" figure. **Prescribed fix:** add a terminal-state guard — if a pick is still ungraded more than ~10 trading days past its `trading_date`, write an outcome row with empty metrics and a `note` (e.g. `NO DATA: price fetch unavailable N sessions past grade date`), exactly as the Juneteenth VOID rows already do, and surface those separately from genuinely-pending picks.

**Standing note (unchanged):** the 14 Juneteenth (2026-06-19) picks remain permanently ungraded with an explicit `VOID: phantom scan — NYSE closed` note and empty metrics. Correctly excluded from the 574 graded count and from every displayed statistic. The 06-28 holiday-skip fix continues to hold — no new holiday cohort has been logged since.

**Grading in the coming week:** 123 ungraded, of which **118 are gradeable** and 5 are the stuck rows above. Cohorts reach their 5-trading-day mark: 07-27 (22) ~08-03, 07-28 (24) ~08-04, 07-29 (24) ~08-05, 07-30 (24) ~08-06, 07-31 (24) ~08-07 — ~118 fresh grades landing 08-03 → 08-07. (The 5 stuck picks and the 14 Juneteenth picks will not grade.)

## 2026-07-29 — Selection and timing: both searches closed, with structural reasons

Two exhaustive negative results, logged so neither has to be re-run. Both were prompted by asking
whether anything in the log supports a *directional* claim after Gate 1 failed. Neither does — and
in both cases the reason is structural rather than "we tried and missed."

### Selection — 58 tests, nothing survives, and every apparent positive is one stock

Swept every available variable across both cohorts with ticker-clustered CIs: `price_at_screen`,
`float_shares`, `rvol`, `gap_pct`, `short_interest_pct`, `score`, plus five never previously
tested — `appearance_idx` (how many times a name had been picked before), `is_fresh` (new or
returning after a >7-day gap), `breadth` (picks that day), day-of-week, and `watch_level` — against
same-day and 5-day return, plus categorical and interaction keeps (dilution, catalyst, regime
splits, SI>=20, low breadth, dilution x regime, SI x dilution).

- **0 of 36 correlation tests survive Benjamini-Hochberg at q=0.05.** Eleven of 58 look
  significant uncorrected against **~2.9 expected by chance** — mildly elevated, with none of the
  coherent structure the H-RISK1 magnitude family showed.
- **Every apparently-positive subset collapses to a single stock (DFNS, +663% over 5 sessions).**
  Removing that one name: score top-third 5-day **+18.96% -> -5.82%** (median -20.29%); gap
  top-third **+23.98% -> -0.60%**; rvol top-third **+22.95% -> -1.68%**.
- The one candidate that briefly looked real — **"freshness"**, fresh names beating stale ones,
  negative `appearance_idx` correlation in *both* cohorts and a v0.3 spread of +5.90pp with
  CI [+1.69, +12.12] — **died on inspection.** Its positive mean is DFNS again (**+6.57% ->
  -3.86%** without it; **median -8.49%**, win rate 36%), and across v0.3's 10-day window
  `appearance_idx` largely encodes *picked early vs late in the window* — a time effect, not a
  property of the name. The v0.2 version (fresh -5.67% vs stale -10.77%) is "loses less," not
  "makes money," and is not significant.
- **Decisive criterion applied throughout:** a selection rule is only useful if what it *keeps*
  makes money in absolute terms, not merely loses less than what it drops. Only **2 of 24** tercile
  subsets beat the ~2% round-trip cost, and both are the DFNS artifact. Medians are negative
  essentially everywhere.

**Two structural reasons this is not a testing failure.** (1) **v0.2 has no choice set** — it
admits **13-16 of its 16 names every single day** (median 15/day across 30 days). You cannot select
from a set you always take in full. v0.3 does choose (top 10 of eligible) but holds only 80 graded
picks over 10 days, and the eligible-but-unpublished control pool is 32 rows, none graded until
`grade_controls.py` accrues. (2) **Every variable in `picks.csv` is a magnitude descriptor** — gap,
relative volume, float, price are all volatility/liquidity measures. **There is no directional
information in the inputs at all**, which is precisely why the model predicts range and not return
(H-RISK1). Direction in these names lives in things the log never captures: news content, order
flow, retail attention velocity, float rotation, halt dynamics, offering terms.

**Methodological rule adopted from this:** means on this data are dominated by single names, so any
future evaluation here must pre-commit to **median and trimmed statistics** — as H-SHORT1's pass bar
already requires. A mean-based screen on this dataset will find DFNS and call it an edge.

### Timing — closed at daily resolution, and for a reason that makes further search pointless

Timing was already the most-tested area (23 exit variants in `exit-study-LATEST.md`, five registered
families), and after the 2026-07-29 `exit_sim.py` fix **every one loses to simply closing same-day**.
Three timing dimensions had never been tested; all three now have been.

- **Entry timing — the decisive result, never previously examined.** Every rule to date assumes
  entry at the pick-day open. Raw one-session drift entered at successively later points (v0.2,
  n=379): d0 open->close **-0.86%**, d0 close->d1 close **-1.46%**, d1 open->close **-0.61%**,
  d1 close->d2 close **-1.46%**, d2 **-0.79%**, d3 **-0.94%**, d4 **-0.90%**, overnight-only
  **-0.79%**. **There is no entry point anywhere in the window with positive drift** — it is roughly
  **-0.9% per session, everywhere**, several individually significant. The entry is not mistimed;
  the drift is persistent across the whole window.
- **Therefore exit rules cannot fix this, as a matter of arithmetic.** An exit rule does not change
  drift; it only decides how much of it is absorbed. With negative drift at every horizon the
  optimal exit is the **shortest possible hold**, which is exactly what the corrected study reports
  (same-day close **-2.86%** net beats hold-to-5-days **-10.49%** and beats all 23 variants).
  Extended to its conclusion, the optimal timing rule is *not to enter*. No further exit rule needs
  testing at this resolution — none can exist that manufactures positive expectancy from negative
  drift.
- **Risk-normalised exits — tested and refuted.** Because a -10% stop is breached by 85% of
  top-quintile names but 56% of bottom-quintile ones, scaling stops to predicted range (per H-RISK1)
  looked promising. It is not: scaled stop at 0.4x predicted range gives **-7.37%** vs fixed -10% at
  **-7.51%** — indistinguishable, both far worse than same-day close. Scaled targets and
  target+stop combinations all land between -6.16% and -9.38%. **The risk gauge does not rescue exit
  rules**; it describes how violently the position will move while losing.
- **State-dependent exit — tested and refuted.** Exiting when a name drops off the screen returns
  **-10.29%** (v0.2) and **-3.62%** (v0.3), both worse than doing nothing.

**Why "if it's up 20%, sell" feels like it should work.** The median pick touches **+9.1%** at some
point within five sessions, so most of them *do* rise. Capping fails anyway because reaching a
target is not random — the names that get there are disproportionately the ones that would have run
further, so the rule caps winners while retaining full downside. Observed exactly: target +10% gives
a 44% win rate at -6.2% net, and target +5% gives a **67% win rate at -4.4% net**. **A rule that
raises the win rate while lowering expectancy is the signature of this trap** (PRINCIPLES P4).

**The one frontier left open, honestly labelled: intraday.** All of the above is daily-bar
resolution, so when a pick touches +9.1% we cannot tell whether that happened in the first thirty
minutes or on day four. If the spike is concentrated near the open, an intraday rule would be a
different object from anything tested here. That is a **data gap, not an analysis gap** — it needs
minute-level capture the project does not collect, and intraday microcap execution costs run well
above the 2% haircut used throughout, so the bar is higher than it appears. Not registered; recorded
as the only surviving timing question.

**Net: selection and timing are both closed at current data and resolution.** The project's one
established predictive relationship remains H-RISK1 (magnitude, not direction), registered forward
the same day.

## 2026-07-29 — Follow-up: the model predicts MAGNITUDE, not direction — **H-RISK1/H-RISK2 registered**

Same-day follow-up to the Gate-1 verdict. Every one of the 33 registrations to date asked whether
the model predicts **profit**; none asked whether it predicts anything else. It does.

**Finding.** The composite score is a replicated predictor of how violently a name moves, while
carrying essentially no information about which way. Mean |rho| across the tested family:
**0.258 for magnitude** (drawdown depth, total range, upside excursion) vs **0.072 for direction**
(same-day and 5-day signed return). Ticker-clustered: v0.2 (n=444) score→|MAE| **+0.206**,
score→range **+0.277**, score→same-day return **+0.004 (ns)**; v0.3 (n=80, a disjoint 67-ticker
universe) **+0.320**, **+0.440**, **−0.054 (ns)**.

**Stress tests it survived.** (1) Replication across two universes built differently. (2) A
within-day test that differences out the market — ranking picks against each other on the same
morning: score→range mean rho **+0.255**, positive on **77% of 30 days**, p=0.0001, while
score→same-day return is rho +0.010, p=0.78. (3) Benjamini–Hochberg across **26 tests** — 10
survive at q=0.05, the top 8 all magnitude, and the four worst p-values in the whole family
(0.63/0.70/0.78/0.94) are all score→direction. (4) An out-of-time split: score→|MAE| **+0.149
early → +0.328 late**, both significant — it strengthened. (5) A partial correlation controlling
for price level, the obvious confound: +0.206→+0.196 and +0.440→+0.443, essentially unmoved.
Also: for risk the four-factor composite **beats every one of its own inputs** on v0.2 (score
+0.206 vs rvol +0.123, float +0.127, price −0.136, gap −0.029) — the opposite of its behaviour
for return, where H-STR3 finds it adds nothing over gap alone.

**Usable as a gauge.** v0.2 score quintiles: P(drawdown ≥20%) runs **20.2% → 48.3%** (2.4×) and
P(≥35%) runs 4.5% → 18.0% (4×). Honest caveat: Q2–Q4 are a plateau, so it is a usable gauge, not
a precision instrument.

**Why H-F4 ("skip hot tiers") missed this.** Tiers A+B are only **11.7%** of v0.2 picks, so
removing them barely moves a mean — the filter had almost no power by construction, which is
exactly the Δ +0.1pp null it returned. The signal is **continuous**; the filter was **binary and
applied to a rare category**. In v0.3 the same labels cover **97.5%** of picks, so the identical
filter is meaningless in the opposite direction — the cohort-incomparability problem registered
today as H-STR3.

**What this is NOT — registered in advance so a confirmation cannot be oversold.** This is
substantially **volatility persistence**, a long-documented regularity; the score is built from
gap and relative volume, both volatility measures, so it *should* work. It is **not alpha**, it is
**not tradeable** (magnitude without direction needs options, and options on floats this thin are
absent or unusably wide), and it **does not reopen Gate 1**, which remains failed. It is also
post-hoc, which is why it now has a forward window.

**Registered as H-RISK1 (magnitude-not-direction) and H-RISK2 (calibration), batch #6, frozen
2026-07-29, with `risk_eval.py` shipped alongside** so they cannot become orphans like the six
registered-but-never-computed hypotheses this week's audit turned up. H-A2, H-STR3-B and H-SIZE1
were drafted and deliberately left unregistered; that decision is recorded in HYPOTHESES.md so
they cannot be quietly registered later after more data has been seen.

**Why register something expected to pass.** A record containing only refutations is externally
indistinguishable from a broken instrument that returns "no" to everything. A pre-registered
confirmation, run through the same clustering and multiplicity discipline as the failures, is what
demonstrates the apparatus **discriminates** rather than merely rejects.

## 2026-07-29 — Gate-1 external-validity verdict — **❌ FAIL (pre-registered null confirmed)**

The pre-registered external-validity gate reaches its verdict. Evaluated on `leaderboard.json`
(generated 2026-07-29), recomputed by `hypo_eval.py` and cross-checked against the raw CSVs.
Publication was due 2026-07-27 and is recorded here on 07-29; the data pipeline was continuous
and unaffected throughout.

**Verdict: the exit edge did NOT survive out-of-sample. Gate 1 FAILS.**

- **H-EX1 (+10% limit exit) — refuted, and refuted in the negative direction.** n_post = 309;
  avg net/trade **−5.9%** vs same-day-close baseline **−2.9%**; **Δ −3.0pp**; pooled 95% CI
  **[−4.4, −1.5]**; cluster CI **[−6.0, −0.6]** (both exclude zero); effective N = **16 names**,
  **5/16** favor the rule (no name-majority); stability **stable**, 5.1 weeks live. The rule does
  not merely fail to beat the same-day close — it loses to it significantly, and the loss survives
  the H-IND1 ticker-clustering correction.
- **Sign history — why pre-registration was the whole point:** **+1.7pp (n=30) → −2.1pp (n=200) →
  −3.0pp (n=309)**. The in-sample read was +8% median. The forward sign inverted and then
  stabilised as n grew. An unregistered version of this project would have shipped the +1.7pp.
- **Selection filters (H-F1–F4, H-CLEAN) — no edge.** All mature (n 214–317, 5.3 weeks) and all
  Δ between −0.1 and +0.1pp with every pooled and cluster CI straddling zero.
- **v0.3 exit family — no better.** H-V3-EX5 (+10% target / −20% stop) is significantly negative
  (n_post 61, Δ **−6.5pp**, CI [−10.8, −2.3], cluster CI [−10.0, −2.8], 15/54 names favor).
  H-V3-EX1/EX2/EX3/EX4 remain **immature** (`stability: building`, 2.3 weeks) — their third
  consecutive weekly snapshot lands with the **2026-08-01** report.
- **Multiplicity, stated plainly:** across 11 live rules there are 6 positive point estimates
  against **5.5 expected by chance**, and the only 2 results clearing significance are both
  **negative**. That is the signature of no effect.

**Decision (MONETIZATION-GATE.md): Gate 1 FAILED → No-Go.** Gates 2–4 are not opened. ThePickLog
remains a personal, transparent research instrument. The verifiable record — including this
published null — is the artifact. This is the process working exactly as designed: it stopped us
selling noise.

**Scope of the verdict (do not over-read it either).** This refutes *this screen's* exit rule and
current selection filters on the graded record to date. The whole live log spans 2026-06-09 →
2026-07-29, so per PRINCIPLES P5 the honest statement is *no edge in this screen, at this N, in
this regime* — not that no edge could ever exist.

**Two corrections shipped alongside this verdict (both found while auditing it):**

1. **`exit_sim.py` was inflating every bar-priced exit rule — fixed.** The exit study reported the
   same-day-close baseline as **+8.0%** avg net when the true value is **−2.9%**. Cause: for the 65
   graded picks predating grade-time path capture, the study **re-fetched daily bars live**. A
   re-fetch returns *split-adjusted* prices while `entry_open` was recorded *unadjusted* at grade
   time, so a single reverse split injects a four-figure return — which inflated the mean of every
   rule that exits at a bar price (same-day close, hold-to-5d, day-N close, both trailing rules,
   H-EX5a/b, H-EX7) while leaving target/stop rules (whose exit price is capped at the level)
   untouched. That is why the defect looked selective. The re-fetch fallback contradicted
   PRINCIPLES P1 (`paths.csv` is captured once and never re-pulled) and has been removed: the study
   now replays **only** the append-only grade-time record, and every pick must additionally
   reconcile — `bars[0]` must reproduce the stored `ret_open_close_net` to within 0.05pp or the pick
   is dropped and counted. **Effect: n 399 → 379 (65 excluded, 0 unreconciled), same-day close now
   reads −2.9% and equals `outcomes.csv` by construction, and every ⭐ marker disappears — with
   correct data, no exit rule in the study beats the same-day close.** This matters beyond the
   report: MONETIZATION-GATE **Gate 2 is defined on the `exit_sim.py` path-walked number**, so the
   gate's own reference metric had been untrustworthy, and three arms were spuriously starred.
2. **The "float-dominated" structural claim was wrong — corrected.** The validity write-ups stated
   that because the .35 rvol sub-score is near-inert (81% of picks below 10), the composite is
   "effectively float-dominated." The premise holds (84% below 10 on current data) but the
   conclusion inverts the truth. On the v0.2 cohort `float_score` is **almost perfectly constant
   (mean 99.92, sd 0.26)** and `price_score` is **exactly constant (sd 0.00)**, because a fixed
   16-name ultra-low-float universe maxes both out — so **40% of the nominal weight (float .30 +
   price .10) cannot affect the ranking at all**, contributing **0.0%** of score variance. The live
   inputs are rvol (54.8% of variance) and gap (45.2%), and by rank correlation the score is
   **gap-dominated**: ρ(score, gap) **+0.925** vs ρ(score, rvol) **+0.576** vs ρ(score, float)
   **+0.081**. Rvol is not inert so much as *rarely activated but decisive when it fires*; **float
   is the dead input.** Corrected in the empirical-studies and §15 dossier docs.
   **New structural finding from the same check:** the composite measures *different things in the
   two cohorts*. On v0.3 (market-wide) float becomes live and rvol takes over — variance shares
   rvol **66.0%** / float **26.4%** / gap **7.6%**, rank correlations rvol **+0.738** / float
   **+0.529** / gap **+0.395**. So the A–D tier scale is **not comparable across cohorts**, which
   also explains why v0.3 is ~83% tier A. Registered forward as **H-STR3**.

## 2026-07-22 — Weekly verifiability audit — **✅ All claims verify**

Manual functional-test run of the rewritten audit workflow (log-primary delivery + commit/push + issue-on-failure), executed off the Saturday cadence. Live site fetched same-origin from https://thepicklog.vercel.app; every value recomputed from the raw CSVs. All six data checks pass and the six-aspect validity labelling is honest.

**Six data checks:**
- **1. Data served — PASS.** `/picks.csv` HTTP 200, `/outcomes.csv` HTTP 200, both non-empty (543 picks / 406 graded).
- **2. Real data shown — PASS.** Track record renders the live log; "543 picks logged" matches the CSV exactly. Only "sample" string on-site is "out-of-sample" (pricing), not a data fallback.
- **3. No silent gaps — PASS.** 31 trading dates, 2026-06-09 → 2026-07-22; new sessions 07-20/07-21/07-22 all present, so the daily scan is running loudly. Only absent weekdays are Juneteenth (06-19) and observed July 4 (07-03) — both holidays.
- **4. Claims == data — PASS.** Recompute vs site: picks 543=543; blended win rate 31.5% → site **32%**; median net −2.47% → **−2.5%**; avg worst dip −18.4% = **−18.4%**; best 5d-net **+170.5%**. Win-by-tier: A 29.8% (n=57), B 44.4% (n=27), C 35.0% (n=143), D 27.4% (n=179).
- **5. Honest grading — PASS.** Spot-checked PW/GCDT/NCT: 2% haircut applied exactly, win = sign of same-day net on every row, 0 duplicate pick_ids (no regrades).
- **6. Disclaimers — PASS.** Educational, "not investment advice," and "not a broker-dealer" all present.

**Six-aspect validity (Messick):**
- **Structural — honest.** Tiers presented as intensity/heat, not quality; no "higher tier = better" wording. Data confirms the standing finding more strongly than ever: A-tier has the **worst** mean 5d-net (−15.3%) of all four tiers (B −6.0%, C −7.5%, D −8.1%).
- **Unvalidated label — present** on index and method (2× each). Gate-1 external verdict correctly deferred to the 2026-07-27 task; not rendered here.
- **Validity docs — reachable + linked.** All three return HTTP 200 and are linked from method.html §9: Messick Framework, Domain-Coverage Spec, Structural-Justification.

**Minor note (no claim affected):** the 14 Juneteenth (2026-06-19) picks remain permanently ungraded (market closed, empty entry). Correctly excluded from the 406 graded count. The 07-03 holiday correctly has no cohort, so the phantom-cohort fix is holding for new dates.

**Grading in the coming week:** 137 ungraded. Recent cohorts reach their 5-trading-day mark — 07-16 (26) ~07-23, 07-17 (24) ~07-24, 07-20 (25) ~07-27, 07-21 (22) ~07-28, 07-22 (26) ~07-29 — ~123 fresh grades landing 07-23→07-29. (The 14 Juneteenth picks will not grade.)

## 2026-07-18 — Weekly verifiability audit — **✅ All claims verify**

Live site checked directly (fetched same-origin from https://thepicklog.vercel.app). All six data checks pass and the six-aspect validity labelling is honest. One minor data-hygiene note (holiday-orphaned picks), no claim is affected.

**Six data checks:**
- **1. Data served — PASS.** `/picks.csv` HTTP 200 (81.6 KB, 470 rows), `/outcomes.csv` HTTP 200 (44.8 KB, 347 rows). Both non-empty.
- **2. Real data shown — PASS.** Track record renders the live log ("this page re-derives from them"; "Live data — quotes pulled from Financial Modeling Prep"). The only "sample" string on the page is "out-of-sample," not a sample-fallback badge.
- **3. No silent gaps — PASS.** 28 distinct trading dates, 2026-06-09 → 2026-07-17. Every US market weekday present; the only absences are Juneteenth (06-19) and the observed July 4 holiday (07-03). No weekday silently missing.
- **4. Claims == data — PASS.** Recomputed from the raw CSVs: 470 logged / 333 graded / win rate 33.9% → site shows 470 / 333 / **34%** (match). Best 5d-net = **+170.5% (CUPR)**. Win-rate-by-tier: A 30.3% (n=33), B 55.0% (n=20), C 36.2% (n=127), D 30.1% (n=153) — reconciles to the graded set.
- **5. Honest grading — PASS.** Spot-checked 4 rows across the file (PW, NCT, MASK, PTLE): entry = pick-day open; 2% cost haircut applied exactly (`ret_open_close_net == (close−open)/open×100 − 2.0` within rounding); win column = sign of net return on every checked row; no duplicate pick_ids (no regrades).
- **6. Disclaimers — PASS.** Educational, "not advice," and "not a broker-dealer" all present.

**Six-aspect validity (Messick):**
- **Structural — honest.** method.html states plainly: "the momentum tiers rank intensity (and drawdown), not forward return — the top tier historically has the worst mean net and the deepest drawdown." This week's data confirms it: A-tier has the **worst** mean 5d-net (−10.8%). No "higher tier = better" claim anywhere.
- **Unvalidated label — present.** "Until the data clears the bar the model is treated as unvalidated." Gate-1 external verdict correctly deferred (owned by the 2026-07-27 task; not rendered here).
- **Validity docs — reachable + linked.** All three referenced from method.html §9 and return HTTP 200: Messick Framework, Domain-Coverage Spec, Structural-Justification (plus Empirical-Validity-Studies and Validity-Dossier-UG15 also linked).

**Minor note (no claim affected):** 14 picks carry `trading_date 2026-06-19` (Juneteenth — market closed), so they can never grade and sit permanently in the ungraded pool. They're correctly excluded from the 333 graded count and don't touch any published number, but worth checking why the scan logged a holiday cohort.

**Grading in the coming week:** 137 picks currently ungraded. The recent cohorts reach their 5-trading-day mark next week — 07-13 (21 picks) ~07-20, 07-14 (26) ~07-21, 07-15 (26) ~07-22, 07-16 (26) ~07-23, 07-17 (24) ~07-24 — ~123 fresh grades landing 07-20→07-24. (The 14 06-19 holiday picks will not grade.)

## 2026-07-06 — First six-aspect validity audit (Messick) — **⚠️ 1 fail, 5 partial/absent (all labeled)**

New audit dimension per `PRINCIPLES.md §3 item 5`: each of Messick's six aspects of construct
validity is either backed by stranger-reproducible evidence or explicitly labeled *unvalidated*.
Standing rubric: `ThePickLog-Validity-Framework-Messick-2026-07-06.md`. This first run establishes the
baseline verdicts; nothing here contradicts the North Star — every verdict below is reproducible from
the committed CSVs and code.

- **Content — Partial.** Domain now written down (`ThePickLog-Domain-Coverage-Spec-2026-07-06.md`):
  the score samples 4 of ~15 domain drivers, all from 2 of 7 families. Momentum-only
  **underrepresentation** is labeled, not hidden. Technical quality (point-in-time capture) solid.
- **Substantive — Partial.** Process model (spike→fade) + `exit_sim.py` fills-fidelity check exist;
  rival mechanisms not yet discriminated. No unvalidated claim on the site.
- **Structural — FAIL for the quality interpretation (backed & reproducible).** Monotonicity check on
  165 graded rows (`ThePickLog-Structural-Justification-2026-07-06.md`): tier ordering is
  non-monotonic on return (top tier A worst mean net −4.59%; B best) and monotonic on drawdown the
  wrong way (A −24.7% MAE deepest → C −16.2% shallowest — Finding A confirmed). **Action:** re-label
  A–D as an intensity/heat scale, not a quality ranking. Also corrected: true tier cutpoints are
  **75/60/45** (not the 90/75/50 an earlier inventory recorded) — verified against `tier_of()`.
- **Generalizability — Partial.** Machinery Established (pre-registration, OOS windows, `paths.csv`,
  haircut, min-n gates); evidence thin — single ~18-day regime. `market_regime` captured but not yet
  a promotion gate. Model labeled *unvalidated* everywhere, so no over-claim.
- **External — Absent-to-date (honestly labeled).** 0/6 hypotheses significant; H-EX1 Δ +1.7pp
  (CI [−3.2,+5.8], n=30), Bayesian P(beat)≈4%. Criterion validity unsupported so far. Gate-1 verdict
  fires **2026-07-27** and will be published either way.
- **Consequential — Partial.** Safeguards active (unvalidated labels, no monetization pre-gate, null
  publishing, haircut, gap-through warning, North Star). Pending: written intended-use/misuse +
  cost-of-error note, and a **reflexivity monitor** (does publishing move the thin-float name?).

**Net:** no aspect makes an unbacked on-site claim; the one hard **FAIL** (structural) is a labeling
defect with a concrete, shippable fix. External validity remains the open question the whole project
is gated on. Re-audit these six alongside the weekly verifiability run.

---

## 2026-06-28 — Resolution of the 06-27 finding (Juneteenth phantom cohort) — **✅ Fixed**

The market-holiday issue flagged below is resolved before the affected rows could grade (~06-29).

**Verified phantom:** all **14** picks dated **2026-06-19** (Friday, Juneteenth, NYSE closed) carry
`price_at_screen` **byte-identical to the 2026-06-22 session** (and *not* to the true prior session
06-18). Confirmed stale/duplicate quotes — not a real screen. None had graded yet (0/14).

**Fix 1 — voided the cohort (immutability-respecting).** Rather than delete the immutable picks
rows (they stay as evidence the scanner misfired), appended a terminal **VOID** outcome for each of
the 14: blank returns/win + an explanatory `note`. Effect: they are now "resolved" (the grader skips
them — 0 of the 06-19 cohort remain pending, so the ~06-29 run cannot grade them off a bogus open),
and every performance stat already filters on non-empty return, so they are **excluded from all
metrics**. `weekly_report.py` §1 now reports them as a separate **voided** count (106 graded / 74
pending / 14 voided). Integrity checks still pass.

**Fix 2 — scanner guard (so it can't recur).** `ignitionscan.py` `cmd_scan` now (a) skips known
**NYSE_HOLIDAYS** as a clean no-op (logs nothing, exit 0), and (b) has a source-agnostic
**stale/duplicate-quote backstop**: if ≥80% of the day's quotes are byte-identical to the most
recent logged session (the closed-market/frozen-feed signature), it fails loudly and logs nothing.
The backstop is what catches anything the calendar misses (future years, half-days, feed outages).
Both tested offline.

---

## 2026-06-27 — Weekly verifiability audit — **⚠️ Issues found (1)**

Every claim the live site *displays* verifies exactly against the raw CSVs. One data-hygiene issue: a scan ran on a market holiday. Audit ran clean via Chrome (last week's tooling block is resolved).

**✅ What verified**
- **Data served:** `/picks.csv` and `/outcomes.csv` both HTTP 200, non-empty — 194 picks, 106 graded rows.
- **Real log, not sample:** Track record renders "Pulled live from the public pick log — 194 picks across 14 trading days (2026-06-09 → 2026-06-26)" with real WIN/MISS/pending rows. No sample fallback.
- **Claims == data (all match):** picks 194 ✓ · graded 106 ✓ · win rate 37% (recomputed 36.8%) ✓ · median net −3.0% (−2.96) ✓ · mean net −2.8% (−2.81) ✓ · avg worst dip −18.0% (−17.96) ✓ · avg 5d swing −5.4% (−5.35) ✓ · Best Net +20% (best same-day 19.9%) ✓.
- **Win-rate by tier — exact:** A 33% (n=9) · B 56% (n=9) · C 41% (n=41) · D 30% (n=47).
- **Honest grading:** 106/106 graded rows reproduce from entry=pick-day open, (close−open)/open − 2% cost; win = positive net. 0 sign mismatches, 0 duplicate pick_ids, 0 missing entry_open.
- **Disclaimers present:** educational/informational, not advice, not a broker-dealer, not affiliated with Buffett — all on Overview and Track record.

**⚠️ Issue — scan ran on a market holiday (2026-06-19, Juneteenth, NYSE closed)**
No trading weekday is *missing* (all 14 in 06-09→06-26 present). But 2026-06-19 is Juneteenth — NYSE was closed — yet 14 picks are logged that day, and their `price_at_screen` values are **byte-identical to the 06-22 session** (stale/duplicate quotes). The scan did not fail loudly on a closed market; it produced a phantom screen. These rows are still **pending** (ungraded), so no displayed performance stat is corrupted *yet* — but they will hit the 5-day grading mark ~06-29 and would grade off a bogus 06-19 "open." **Fix before then:** void/remove the 06-19 cohort, and add a US-market-holiday skip (or a "fail loudly on stale/duplicate quote" guard) to the scanner so a closed day produces no log rather than a copy of the next session.

**Grading in the coming week:** graded through the 06-18 cohort. Reaching the 5-trading-day mark next: **06-19 cohort ~06-29** (the anomalous rows — void first), **06-22 ~06-30**, **06-23 ~07-01**.

## 2026-06-22 — Weekly verifiability audit — **⚠️ COULD NOT RUN (tooling, not site)**

The audit could not be completed this week because the live site was unreachable from the audit environment. This is an environment/tooling failure — **it is NOT evidence that the site is broken.** No live check (CSV fetch, Track-record render, claims==data, grading) could be performed, so nothing is certified this week.

**What blocked it:**
- Chrome browser tool offline — 8+ retries, "Claude in Chrome is not connected." This is the path prior audits used to reach the live site.
- `web_fetch` is provenance-gated: it only fetches URLs that appeared in an actual user chat message; the scheduled-task URLs don't qualify, so `/picks.csv` and `/outcomes.csv` returned "URL not in provenance set."
- WebSearch doesn't return the site or raw CSVs.
- curl/wget intentionally not used (prohibited as a web_fetch workaround).

**Why the local clone can't substitute:** `~/Documents/AMD Ventures/stock screener/ignitionscan` is 1 unpushed local commit ahead of origin/main (HEAD b5be38a vs origin d4aa3ac), has **no outcomes.csv** at all, and its picks.csv only runs through 2026-06-15. It can't verify what a stranger sees on the live site today.

**To unblock next run (any one works):** open Chrome with the Claude extension signed in before the scheduled time; or run the audit interactively so the live URLs enter the chat provenance; or add a permitted server-side fetch path for the two static CSVs.

**Upcoming grades (UNVERIFIED — from last week's 06-16 snapshot, not today's live data):** as of 06-16 only the 06-09 cohort (13 picks) was graded. On a 5-trading-day mark the 06-10 cohort grades ~06-17, 06-11→~06-18, 06-12→~06-19, 06-15→~06-23, 06-16→~06-24 — so several cohorts should have graded by now; confirm on the next successful run.

## 2026-06-16 — First-grades integrity check — **PASS**

Scan resumed, grades landed, and the live Track record matches the data. Claims == data.

**1. picks.csv — 200, scan resumed, no weekday gap.**
HTTP 200. 78 picks across 6 trading days (2026-06-09 → 2026-06-16). 6-15 (Mon) and 6-16 (Tue) both present, so the scan resumed cleanly. Every US market weekday in the window is present (6-09 Tue, 6-10 Wed, 6-11 Thu, 6-12 Fri, 6-15 Mon, 6-16 Tue). Note: 2026-06-13 is a **Saturday** (6-14 Sunday) — correctly no scan; the flagged "6-13 miss" doesn't apply because 6-13 was never a trading day. No gaps.

**2. outcomes.csv — exists, grader ran.**
HTTP 200. 13 graded rows = the full 2026-06-09 cohort, which reached the 5-trading-day grading mark. Grader confirmed running.

**3. Live Track record — REAL log, not the sample fallback.**
"Pulled live from the public pick log — 78 picks across 6 trading days." The only "sample" string on the page is a prototype disclaimer ("Educational sample for development hand-off"), not a fallback badge. Headline: 78 logged / 13 graded / **Win rate 38%** / median net -2.5% / mean net -2.2% / avg worst dip -18.3%. Win-rate-by-tier populates: A 50% (n=2), B 33% (n=3), C 40% (n=5), D 33% (n=3).

**4. Recomputed win rate matches.**
Independently from outcomes.csv: 5 wins / 13 graded = **38.5%** → site rounds to 38%. MATCH. Tier counts reconcile exactly to the 6-09 cohort (A 2, B 3, C 5, D 3 = 13).

**5. Methodology spot-check — clean.**
- Entry = pick-day open: grader uses the trading_date bar's Open; all 13 entry_open > 0.
- 2% cost haircut applied: verified all 13 rows satisfy ret_open_close_net == (close − open)/open × 100 − 2.0 within rounding (max diff < 0.005).
- Win = positive net return: win column matches sign of ret_open_close_net on all 13 rows (0 mismatches) — not an "ever touched +20%" definition.
- No regrades: 0 duplicate pick_ids.

**Most important fix:** None blocking. Minor housekeeping — the local git clone is stale (no outcomes.csv locally; local picks.csv only to 6-15), but the live/remote is correct, so this is a working-copy nit, not a product issue. `git pull` to resync the local clone when convenient.
