# Calibration run 2 (2026-09-25) — the record

543 filings, `jev-1.13.0`, question block v1 (`6be36476189a…`). This is the run in which
`reverse_split = effective` FAILED the pre-set bar (0.833 at p >= 0.90 vs 0.95), which led
to the pre-registered v2 test in `../calibration_v2/` and `../REGISTRATION-split-v2.md`.

- `responses.zip` — every raw Jev response, each stamped with the sha256 of the text and of
  the question block it answered. The logged response is the record (re-asking drifts).
- `candidates.csv` — the sample: doc_url + text_sha256 per filing (texts are re-fetchable).
- `labels.csv`, `truth.csv`, `labels_model/`, `merge_summary.json` — how labels were made.
- `label_corrections.csv` — 17 corrections, each with its evidence; `audit.csv` (0 filled).
- `result.json` (corrected) and `result_as_labeled.json`, with reliability tables.

Re-score without a key or network (from the repo root):

    cd calibration_run2 && mkdir -p run_jev-1.13.0 && (cd run_jev-1.13.0 && unzip -q ../responses.zip) && cd ..
    FILING_LENS_QUESTIONS=v1 JEV_MODEL=jev-1.13.0 JEV_API_KEY=x python3 calibration_run.py --cal calibration_run2
