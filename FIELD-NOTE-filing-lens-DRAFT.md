# Field note (DRAFT, not published): we asked a small AI model to read SEC filings. It failed our test once, then passed a narrower one.

*Draft 2026-09-28 on branch `jev-filing-lens`. Nothing in this note is on the site yet. Every number below can be re-derived from files in the repository, and each claim names its file.*

## Why we tried this

ThePickLog grades picks from price data. Two kinds of events can make that data lie.

- **Reverse splits.** A reverse split multiplies the quoted price overnight, and an unadjusted feed turns that into a fake gain. This is the split-adjustment trap described on the site.
- **Halts and delistings.** These freeze or end a quote, and a frozen quote looks like a stock that simply did not move.

Both events are announced in SEC filings, usually a day or more before the price data shows them. We wanted to know whether a model could read those filings reliably enough to warn the price-integrity checks.

The model is TypeSafe AI's **Jev**, pinned to version `jev-1.13.0`. It answers fixed multiple-choice questions and gives a probability for every option. We ask it six questions per filing: reverse split, split ratio, listing status, dilution, going concern, and other material events.

The rule we set before any test: **no answer acts on anything unless its question passes a bar we wrote down first.** The bar was at least 95% precision when the model is at least 90% sure, with at least 30 true cases in the sample.

## Test 1: 543 filings, 2025–26 (`calibration_run2/`)

The labels came from three sources:

- **Market data (Yahoo split history):** decided splits wherever it could.
- **8-K item codes:** decided bankruptcy, auditor change and restatement.
- **A separate AI reader (Anthropic's Claude):** labeled the rest, quoting the filing for every label.

Seventeen labels were later found wrong. Each correction is listed with its evidence in `label_corrections.csv`, and both scorings are published: `result.json` (corrected) and `result_as_labeled.json`. Total cost of the run was about $0.22.

| Question · answer | True cases | Right when ≥ 90% sure | Bar met? |
| --- | --- | --- | --- |
| Reverse split · effective | 58 | **40 of 48 (0.83)** | **No** |
| Reverse split · announced | 48 | 44 of 44 | yes |
| Listing · halt | 43 | 20 of 21 (0.95) | yes |
| Listing · delisting | 39 | 10 of 10 | yes |

The question we cared about most failed. The misses were mostly filings that *mention* a split that happened weeks earlier, such as a prospectus reciting past corporate actions. The model called those splits "effective".

We also looked at 8-Ks alone, where the model did better (36 of 38). **We do not count that as evidence.** We picked that cut after seeing the results, and a cut chosen after the fact can always be made to look good.

**We also re-asked 40 filings, byte for byte identical.** None of the 240 answers changed, but probabilities moved by up to 0.10. One halt answer crossed the 0.90 line between runs. Two consequences follow:

- The record of what the model said is the **logged response**, not a re-run.
- Every threshold needs a review band on either side of it.

## Test 2: a new question, pre-registered on filings it had never seen (`calibration_v2/`)

We rewrote the split question so it says explicitly that a split mentioned "as previously disclosed" counts as *historical*. Then we wrote the test down before drawing the sample: `REGISTRATION-split-v2.md`, commit 36a7c0e.

- **Sample:** every 2024 8-K carrying Item 5.03 or 3.03 from a ticker in our pick log. That was 196 filings, none used before. Items 5.03 and 3.03 are the filings the split check actually reads.
- **Labels:** made by the same kind of AI reader, from the same text the model sees, with a quote for each label.
- **Hash first:** the finished label file's hash was committed (945e3ad) **before** the model saw a single filing. Nobody could tune the labels to the answers.

| Registered outcome | Bar | Result |
| --- | --- | --- |
| "Effective" right when ≥ 90% sure | ≥ 0.95 with ≥ 30 true cases | **24 of 24**, with 30 true cases |
| Same, on labels as first made | ≥ 0.90 | 24 of 24 (no corrections were made) |
| "Announced" | ≥ 0.95 | 29 of 29 |
| Split ratio, when there was a split | ≥ 0.95 | 59 of 59 |
| 30 filings re-asked | 0 answers change | 0 changed |

**It passed. Here is what that does not mean:**

- **24 of 24 is a small number.** The honest 95% range for the true precision starts at 0.86, not 0.95.
- **The failure from test 1 hardly occurred in this sample.** Only 2 of these 196 filings recite an old split, so this test shows the question works *on 8-Ks announcing their own corporate actions*. It does not show the recital problem is solved everywhere.
- **The model missed 6 of the 30 real splits at the 90% line.** Four of the six were still answered "effective", just with lower confidence, so they go to human review instead of being lost.
- **The labels come from an AI reader, not a person.** They agree with the market record: all 30 "effective" labels have a Yahoo split within 30 days before to 3 days after the filing. That agreement is a check, not a proof.

## What the model is now allowed to do

Very little, on purpose.

- **One route is allowed.** A reverse split the model calls "effective" at ≥ 0.90 may go straight to the split check, but only for an 8-K carrying Item 5.03 or 3.03. The split check still confirms the ratio and date against the price series before anything changes.
- **The model never edits a row, a grade or a count.**
- **Everything else goes to review or is ignored.** That includes lower-confidence answers, other filing types and every other question.

The live pipeline starts in **shadow mode**: it logs every answer and acts on none. We will judge it on that log before anything is switched on.

## Check it yourself

```
git clone https://github.com/joshldavis/ThePickLog && cd ThePickLog && git checkout jev-filing-lens
FILING_LENS_QUESTIONS=v2 python3 score_split_v2.py --cal calibration_v2          # test 2 verdict
cd calibration_run2 && mkdir -p run_jev-1.13.0 && (cd run_jev-1.13.0 && unzip -q ../responses.zip) && cd ..
FILING_LENS_QUESTIONS=v1 JEV_MODEL=jev-1.13.0 JEV_API_KEY=x python3 calibration_run.py --cal calibration_run2   # test 1, from the logged answers
```

Neither command needs an API key or the network. Both re-score the logged model answers against the committed labels. To check the answers themselves, re-fetch any filing from its `doc_url`, confirm it matches `text_sha256`, and send it with the question block to `jev-1.13.0`. Expect small probability drift (see test 1).

*Not investment advice.*
