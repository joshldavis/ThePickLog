# Distribution drafts — the late-cohort correction

**Link:** https://thepicklog.vercel.app/late-cohorts.html

Everything below is ready to send as-is. I can't post on your behalf, so these are yours to fire.

**Why this piece and not Experiment 01:** a correction travels further than a result. "We tested our thing and it lost" is a story about you; "our scheduler silently broke the one guarantee our data rests on, here's the forensics" is a story about a mistake the reader might be making right now. It also inoculates the Experiment 01 write-up — anyone who finds the correction first arrives already trusting the record.

**Lead with the mistake, never with the project.** Every draft below opens on the failure and mentions ThePickLog second. That ordering is the whole reason this works.

---

## 1 · Hacker News (Show HN is wrong here — submit as a link post)

**Title options, best first — HN titles are the whole game:**

- `We logged 128 stock picks after the market opened and didn't notice for six weeks`
- `Our scheduler drifted past the opening bell and quietly invalidated 128 data points`
- `GitHub Actions cron is best-effort. Our forward-graded trading log wasn't.`

**First comment (post it immediately after submitting):**

> Author here. Context that didn't fit the title:
>
> The project publishes forward-graded verdicts on trading strategies — the rule is frozen with a date before any data exists, then graded forward on public data. The one thing the entire record depends on is that picks are written down before the market opens.
>
> A reader checking our public picks.csv found that our scan had drifted past the 09:30 open on seven occasions and logged anyway, 2 to 72 minutes late. The headline metric is the same-day open→close return, so those picks were scored against an opening price that had already printed.
>
> The part I found most instructive: the tempting story is "our protocol broke in a way that flattered us." Late picks show +0.55% mean vs −3.40% for timely ones. But the *median* gap is a quarter of a point, and the entire mean difference is one microcap that ran +241%. Delete it and the gap evaporates. So the honest statement is: we broke the rule, the rule matters, and we can't demonstrate that breaking it helped us. Both halves are in the write-up.
>
> Root cause is boring and general: we guarded the market (holiday calendar) and the data (stale-feed detector) and never guarded the deadline. GitHub Actions cron is documented as best-effort; we'd treated a schedule as a guarantee. There's now a hard gate that refuses to write anything after 09:20 ET, and the exclusion is derived from the public timestamps rather than a flag we set, so anyone can reproduce it.

**Timing:** Tue–Thu, 8–10am ET. Do not vote-ring or ask anyone to upvote.

---

## 2 · Reddit

**r/algotrading** — the best fit by far. Flair: Education/Research.

**Title:** `PSA: if your strategy log runs on a scheduler, verify the timestamp at write time — ours drifted past the open 7 times`

**Body:**

> I keep a public forward-graded log of a low-float momentum screen. Picks get written to an append-only CSV before the open, graded 5 days later, everything published including the losses.
>
> Someone reviewing my raw picks.csv found 128 rows across 7 sessions where the scan had run *after* the 09:30 open — by 2 to 72 minutes. Since the headline number is the same-day open→close return, those entries were scored against a price that had already printed.
>
> Root cause: GitHub Actions cron is best-effort and drifts under load. My scanner checked for market holidays and for a frozen quote feed, but never looked at the clock. I'd treated "scheduled for 07:30" as a guarantee for two months.
>
> Two things worth stealing:
>
> 1. **Verify the deadline at write time, not in review.** A gap in your record is a fact you can work with. A silently late entry is a lie that propagates into every summary statistic until someone else finds it. My scanner now refuses to write anything after 09:20 ET and exits non-zero.
> 2. **Check whether the contamination is actually measurable before you claim it.** The late picks averaged +0.55% vs −3.40% for the clean ones, which looks damning. But the medians are a quarter-point apart and the whole gap is one ticker that ran +241%. Delete your single best trade and re-run — if your finding evaporates, it was never there.
>
> Full write-up with the numbers and reproducible code: [link]
>
> Not selling anything, the verdicts are free, and the strategy in question already failed publicly.

**Also worth posting to:** r/quant (drier, lead with the clustered-CI angle), r/datasets or r/dataengineering (reframe as a scheduler/data-integrity story and drop the trading framing almost entirely).

**Reddit rule:** answer every comment for the first few hours, and don't link the homepage in the body — only the field note.

---

## 3 · X / Twitter thread

> 1/ Our stock-pick log has one rule: every pick written down before the market opens, so nobody can know the outcome.
>
> A reader found 128 picks we'd logged *after* the opening bell.
>
> We didn't notice for six weeks. Here's the post-mortem.

> 2/ The scan runs on a GitHub Actions cron set for 07:30 ET. Two hours of margin.
>
> Actions cron is best-effort. It drifts. Seven times it drifted past 09:30 and logged anyway — once by 72 minutes.

> 3/ Why that's fatal: the headline metric is the same-day open→close return.
>
> A pick logged at 09:32 is scored against an opening price that already printed. It was never a forecast.

> 4/ The scanner had guards. Market holidays: checked. Frozen quote feed: checked.
>
> The clock: never checked.
>
> We guarded the market and the data and forgot to guard the deadline.

> 5/ Corrected headline: −2.68% → −3.40%. Worse, which given we'd already published the strategy as a failure changes the conclusion not at all.

> 6/ Now the interesting part.
>
> The tempting story is "the bug flattered us." Late picks: +0.55%. Timely: −3.40%. A four-point gap.
>
> We don't think that's true.

> 7/ The MEDIAN gap is 0.28 points.
>
> The entire mean difference is one microcap that ran +241%. Delete it: gap gone.
>
> A four-point gap that vanishes when you delete one row isn't bias. It's one lucky trade.

> 8/ So: we broke the rule, the rule matters, and we can't show you that breaking it helped us.
>
> Both halves are the finding. Claiming bias we can't demonstrate would be its own small dishonesty.

> 9/ Fixed: hard gate refuses to log anything after 09:20 ET. Cron moved earlier. The exclusion is *derived* from public timestamps, not a flag we set — so you can reproduce our exact exclusion set.

> 10/ General lesson for anyone keeping a forward-graded record of anything:
>
> You will guard the thing you're measuring and forget to guard the measurement.
>
> If a deadline is load-bearing, verify it at write time and refuse to write when you miss it.

> 11/ Full write-up, the numbers, and runnable code to check us:
> https://thepicklog.vercel.app/late-cohorts.html
>
> Found by a reader in a file we'd published for weeks. Embarrassing, and exactly why the file is public.

---

## 4 · LinkedIn

> Someone reviewing our public data found a mistake we'd been publishing for six weeks.
>
> Our project logs stock picks before the market opens and grades them forward — the whole point is that the prediction is recorded before the outcome can be known. A reader checking the raw file found 128 picks that had been logged *after* the opening bell, because our scheduler had quietly drifted.
>
> We corrected the numbers, wrote up the post-mortem, and published it in full.
>
> The part I keep thinking about: our automated checks covered market holidays and stale data feeds. They never checked whether we were on time. We had guarded everything except the assumption the whole record rested on.
>
> If you maintain any dataset where a deadline is load-bearing, verify it at write time rather than trusting the scheduler. A gap in the record is something you can work with. A silently late entry propagates into every downstream number until someone else finds it.
>
> Write-up: https://thepicklog.vercel.app/late-cohorts.html

---

## 5 · Email — to anyone already following the project

**Subject:** `A correction: we logged 128 picks after the opening bell`

> Short version: our scanner drifted past the market open on seven occasions and logged picks anyway. Those picks are now excluded from every number on the site, and the headline moves from −2.68% to −3.40%.
>
> A reader found it in the public CSV. We hadn't run the check on our own data.
>
> The full post-mortem is here, including the part where we decline to claim the mistake flattered us — the entire apparent effect is one lucky microcap: https://thepicklog.vercel.app/late-cohorts.html
>
> Nothing about the published verdicts changes. Experiment 01 still failed, slightly harder.

---

## Sequencing

1. **Hacker News first**, on its own. If it lands, everything else rides that.
2. **r/algotrading the next day**, regardless of how HN went.
3. **X thread the same day as Reddit** — it's the one that keeps working later when people search the incident.
4. **LinkedIn whenever.** Different audience, no interference.
5. Hold the email until at least one of the above has landed, so there's something to point at.

**Do not** post the same day as a market event that will bury it, and don't cross-post to a second subreddit within 24 hours.

## One caveat before you post

The site is currently anonymous. Every one of these drafts is written in first person, and the first question a good HN or r/algotrading commenter asks is "who is this?" Getting your bio and an About page up first would materially improve how this lands — it's the difference between "a person publishing their mistakes" and "an anonymous site publishing its mistakes."
