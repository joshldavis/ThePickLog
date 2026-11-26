# Reproducibility check (second run, 2026-11-26 06:22 UTC)

The workflow ran the replay a second time on its own (a PR push re-triggered it). It used the same
price data (identical SHA-256 fingerprint in `run.csv`) and produced a `summary.csv` and `coverage.csv`
identical to the first run's, apart from the run timestamp. Its duplicate trade log and by-year table
were removed; the first run's outputs one folder up are the published ones. The workflow now reruns
only when started by hand.
