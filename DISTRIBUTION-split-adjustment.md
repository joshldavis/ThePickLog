# Distribution drafts — the split-adjustment trap

**Link:** https://thepicklog.com/split-adjustment-trap.html

Ready to send as-is. I can't post on your behalf — these are yours to fire.

**Why this is the stronger lead piece.** The late-cohort correction is a story about *us*: our scheduler broke, we confessed. It signals integrity, and integrity is worth signalling — but the reader has to already care about ThePickLog for it to land.

This one is a story about *the reader*. It's a bug class that silently inflates results for anyone who backtests cheap stocks, it flips sign depending on your universe, and it is undetectable without a forward-only record. Someone who has never heard of you learns something they can act on tonight. That is what actually travels on Hacker News and r/algotrading — and it earns the credibility that makes the correction piece land harder afterwards.

**Lead with the bug, never with the project.** Every draft below opens on the technical trap and mentions ThePickLog second, or not at all.

---

## 1 · Hacker News (link post, not Show HN)

**Title options, best first.** HN rewards descriptive over clever; avoid anything that reads as a growth-hack headline.

- `Historical stock prices are rewritten on every split, which invented a +8% backtest`
- `Our backtest reported +8%. The real number was −2.9%. The data moved underneath it.`
- `A data bug that flips sign depending on which stocks you trade`
- `The bug that makes your backtest look good, and why you can't see it`

Prefer #1 or #2. Both state a concrete, checkable claim; #4 is the page's own title but reads more like marketing in an HN list.

**First comment — post immediately after submitting:**

> Author here. The short version of the mechanism, for anyone who doesn't want to click:
>
> A stock's price history isn't a fixed fact — it's a function of when you asked. Every split makes the vendor restate the entire prior series, so downloading AAPL's 2019 prices in 2019 and again today gives different numbers. That's correct behaviour and everyone knows it in the abstract.
>
> The failure is mixing the two. Any calculation that combines a price you *captured at the time* with one you *downloaded later* is comparing two different unit systems. In our code an entry recorded at $0.50 met a same-session close re-downloaded after a 1-for-10 reverse split at $5.00, and produced a +900% return on a trade where the stock did nothing. One row like that moved a few-hundred-trade average by ten points.
>
> The part I hadn't seen written down anywhere: **the error flips sign by universe.** Microcaps reverse-split constantly to stay above the $1 listing minimum, and reverse splits adjust history upward — so every contaminated row shows a spurious *gain*. Large caps forward-split, adjusting downward, producing spurious *losses*. Which means in exactly the universe where retail backtests get run — cheap, volatile, heavily promoted names — this bug systematically flatters you.
>
> It also corrupts selectively in a way that mimics a finding. Rules whose exit is a real market price get hit; rules with a capped exit (take profit at +10%) compute exit as entry × 1.10 and stay clean. So our results table showed most rules mediocre and three as winners — which reads as "some strategies work," the exact shape of answer you were hoping for. All three were artifacts.
>
> We only caught it because we had an append-only record of prices as seen at the time to reconcile against: 379 picks with a stored path reproduced to a maximum difference of 0.0, which isolated the corruption instantly to the 65 that had gone through a re-download. A backtest that re-downloads everything on every run has nothing to reconcile against — the error is undetectable for the same reason the results are unreproducible.
>
> Net effect: our baseline went from a reported +8.0% to an actual −2.9%, and after the fix not one of 23 exit rules beat simply selling at the first day's close.

**Timing:** Tue–Thu, 8–10am ET. Never ask anyone to upvote.

---

## 2 · Reddit

### r/algotrading — best fit. Flair: Education/Research.

**Title:** `PSA: if your backtest re-downloads prices, split adjustment may be inventing your returns — and in penny stocks it only ever inflates them`

**Body:**

> Found this in my own code while auditing a result I'd already written off as a failure. It had been inflating my numbers for weeks and threw no errors.
>
> **The mechanism.** Price history gets restated every time a company splits — a 1-for-10 reverse split multiplies the whole prior series by 10, otherwise every chart shows a fake 900% day. Fine and necessary. The problem is mixing a price you stored at decision time with one you pull later: they're in different unit systems. My entry was recorded at $0.50 as actually traded; the same session's close, re-downloaded months later after a reverse split, came back $5.00. Computed return +900% on a trade where nothing happened.
>
> **The part that makes it dangerous.** The sign depends on your universe. Microcaps reverse-split to stay above the $1 listing minimum → history adjusts *up* → spurious **gains**. Large caps forward-split → history adjusts *down* → spurious **losses**. So if you backtest cheap volatile names, this bug is systematically pleasant. If you've ever backtested penny stocks and been pleasantly surprised, rule this out first.
>
> **Why it survives review.** It's silent, it only touches rows with a corporate action in the window, and the corrupted row is usually your best trade — which nobody deletes to see if the conclusion holds. Worse, it corrupts *selectively*: rules exiting at a real market price get hit, rules with a capped exit (+10% take-profit computes as entry × 1.10) stay clean. My table came out "most rules mediocre, three winners," which reads like a finding rather than a bug.
>
> **How I found it, and why most setups can't.** I had an append-only record of prices as seen at the time. Recomputing from it: 379 picks agreed to a max difference of 0.0, which pinned the corruption to the 65 picks that had gone through a re-download. If your backtest re-downloads everything each run, there's nothing to reconcile against — the error is invisible for the same reason your results aren't reproducible.
>
> **The damage:** reported baseline +8.0% → actual −2.9%. After the fix, none of 23 exit rules beat selling at the first day's close. Three had appeared to.
>
> **Three defences, in order of value:**
> 1. Store prices forward-only at decision time and never re-pull. Works by construction, not vigilance.
> 2. If you must re-pull, reconcile — require a stored value to reproduce within a tolerance or drop the row and report the count.
> 3. Never mix adjusted and unadjusted prices in one calculation, including the entry price, which is where people usually break it.
>
> Full write-up with the numbers: [link]
>
> Not selling anything — the strategy in question already failed publicly.

### Also worth posting to

- **r/dataengineering** — reframe entirely as *"your upstream silently rewrites history; here's a reconciliation pattern"* and cut the trading framing almost completely. This is arguably the widest audience: the bug class is really "non-idempotent historical data source."
- **r/quant** — drier, lead with the selective-corruption-mimics-a-finding angle.
- **r/Python** — only if you show the reconciliation code.

**Reddit rule:** answer every comment for the first few hours. Link the field note, never the homepage.

---

## 3 · X / Twitter thread

> 1/ Our backtest said the baseline made +8.0% per trade.
>
> The real number was −2.9%.
>
> Nothing was wrong with the code. The data had changed underneath it.

> 2/ A stock's price history is not a fixed fact. It's a function of when you asked.
>
> Every split makes the vendor restate the entire prior series. Download AAPL's 2019 prices in 2019 and again today — different numbers.

> 3/ That's correct behaviour. The bug is mixing the two.
>
> A price you stored at decision time and a price you download later are in different unit systems.

> 4/ Ours: entry recorded at $0.50, as actually traded.
>
> Same session's close, re-downloaded months later, after a 1-for-10 reverse split: $5.00.
>
> Computed return: +900%.
>
> The stock did nothing. The trade never happened.

> 5/ Now the part I hadn't seen written down anywhere.
>
> The error FLIPS SIGN depending on which stocks you trade.

> 6/ Microcaps reverse-split constantly, to stay above the $1 listing minimum. Reverse splits adjust history UP → spurious gains.
>
> Large caps forward-split. Adjust history DOWN → spurious losses.

> 7/ So in exactly the universe where retail backtests get run — cheap, volatile, promoted names — this bug systematically makes you look better.
>
> It flatters you precisely where you're least equipped to notice.

> 8/ It also corrupts SELECTIVELY, in a shape that mimics a finding.
>
> Rules exiting at a real market price: hit.
> Rules with a capped exit (+10% = entry × 1.10): clean.
>
> Result: "most rules mediocre, three winners." All three were artifacts.

> 9/ That's the shape of answer you were hoping for. Which is why nobody audits it.
>
> The corrupted row is usually your best trade, and nobody deletes their best trade to check whether the conclusion holds.

> 10/ We only caught it because we kept an append-only record of prices as seen at the time.
>
> 379 picks reproduced to a max difference of 0.0 — which isolated the damage instantly to the 65 that had been re-downloaded.

> 11/ If your backtest re-downloads everything every run, you have nothing to reconcile against.
>
> The error is undetectable for the same reason your results are unreproducible. Same root cause.

> 12/ After the fix: not one of 23 exit rules beat simply selling at the first day's close.
>
> Before it, three appeared to.

> 13/ Defences, in order of value:
>
> — Store prices forward-only at decision time. Never re-pull.
> — If you must re-pull, reconcile against the stored value and drop rows that disagree.
> — Never mix adjusted and unadjusted prices, including the entry.

> 14/ Full write-up, with the numbers and what it cost us:
> https://thepicklog.com/split-adjustment-trap.html
>
> We found this while auditing a result we'd already published as a failure. It had been quietly making us look better the whole time.

---

## 4 · LinkedIn

> We found a bug in our own analysis that had been inflating our results for weeks. It threw no errors, and it only ever made the numbers better.
>
> The cause is something most people know in the abstract and few guard against in practice: historical stock prices are not fixed. Every time a company splits, the data provider restates the entire prior price series. Download the same history twice, years apart, and you get different numbers — correctly.
>
> The failure is mixing them. A price captured at decision time and a price downloaded later are in different unit systems. In our case an entry recorded at $0.50 met a re-downloaded close of $5.00 after a reverse split, and produced a +900% return on a trade where nothing had happened.
>
> What made it worth writing up is that the error is not random. Small companies reverse-split, which adjusts history upward and produces spurious gains. Large companies forward-split, producing spurious losses. So the bug systematically flatters exactly the people least equipped to catch it.
>
> Our reported baseline of +8.0% was actually −2.9%. Three strategies that appeared to beat it were artifacts.
>
> The general lesson, well beyond finance: if an upstream source can restate history, then re-downloading is not a neutral operation, and any pipeline that re-derives everything on every run has nothing to reconcile against. Store what you saw when you saw it.
>
> Write-up: https://thepicklog.com/split-adjustment-trap.html

---

## 5 · Hacker News comment-thread prep

Likely challenges and honest answers. Have these ready — the follow-up comments matter more than the post.

- **"Just use adjusted close everywhere."** Right, and that's defence #3. It fails the moment any part of your pipeline stores a price — a fill, a logged entry, a screenshot of a decision. The bug lives at the boundary between stored and re-pulled, not inside either one.
- **"This is a well-known survivorship/adjustment issue."** Adjustment is well known. The sign-flip-by-universe consequence is the part that isn't widely written down, and it's the reason it's dangerous rather than merely annoying. Say so plainly and don't over-claim novelty.
- **"Why not just use a point-in-time database?"** Correct answer for anyone who can afford one. Most retail/independent work can't, which is why the forward-only append log is the cheap substitute.
- **"So your strategy was bad anyway?"** Yes — and it had already been published as a failure before we found this. The bug made a losing baseline look like a winner, which is worse than it sounds: it would have kept us iterating on a dead idea.
