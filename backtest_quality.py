"""
backtest_quality.py — join the Quality Lens grade onto every backtest pick and
run the §1.1 downside-filter test:

    "Quality-Green names have shallower drawdown (MAE) and far fewer
     catastrophic rugs than Red/Black names."

Reads backtest_results.csv (tier, mae_5d, returns, win) + fundamentals_cache.json
(captured fundamentals), grades each ticker with quality_lens.compute_quality,
joins by ticker, writes backtest_quality.csv, and prints the per-grade stats.

Regenerate the cache on a machine that can reach the API:
    for each ticker T in the universe:
       GET /api/edgar?symbol=T            -> fundamentals_cache.json["edgar"][T]
       GET /api/fmp?fn=profile&symbol=T   -> fundamentals_cache.json["profile"][T]
(EDGAR is the same source the live site prefers; the grade therefore matches
the site's Quality chip for the same filings.)
"""
import csv, json, os, statistics as st
from collections import defaultdict
from quality_lens import assemble_fundamentals, compute_quality

HERE = os.path.dirname(os.path.abspath(__file__))


def load_grades():
    with open(os.path.join(HERE, "fundamentals_cache.json")) as fh:
        cache = json.load(fh)
    grades = {}
    for sym, edgar in cache["edgar"].items():
        prof = cache.get("profile", {}).get(sym, {})
        f = assemble_fundamentals(sym, edgar, prof)
        grades[sym] = compute_quality(f)
    return grades


def med(xs): return round(st.median(xs), 2)
def mean(xs): return round(st.mean(xs), 2)


def main():
    grades = load_grades()

    print("=== Quality Lens grade per ticker (from captured filings) ===")
    print(f"{'sym':<6}{'label':<8}{'score':>6}  {'classification':<12}")
    for sym in sorted(grades):
        g = grades[sym]
        print(f"{sym:<6}{g['label_name']:<8}{g['overall']:>6}  {g['classification']:<12}")

    rows = []
    with open(os.path.join(HERE, "backtest_results.csv")) as fh:
        for r in csv.DictReader(fh):
            try:
                r["mae_5d"] = float(r["mae_5d"])
                r["ret5"] = float(r["ret_open_5dclose_net"])
                r["win"] = int(r["win"])
            except (ValueError, KeyError):
                continue
            g = grades.get(r["ticker"])
            r["q_label"] = g["label_name"] if g else "Ungraded"
            r["q_score"] = g["overall"] if g else ""
            r["q_class"] = g["classification"] if g else ""
            rows.append(r)

    # write joined file
    out = os.path.join(HERE, "backtest_quality.csv")
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["trading_date", "ticker", "tier", "score", "q_label", "q_score",
                    "q_class", "mae_5d", "ret_open_5dclose_net", "win"])
        for r in rows:
            w.writerow([r["trading_date"], r["ticker"], r["tier"], r["score"],
                        r["q_label"], r["q_score"], r["q_class"],
                        r["mae_5d"], r["ret5"], r["win"]])

    def block(name, g):
        if not g:
            print(f"  {name:<22} n=   0  (no rows)")
            return
        mae = [x["mae_5d"] for x in g]
        rug30 = 100 * sum(1 for x in mae if x < -30) / len(g)
        rug50 = 100 * sum(1 for x in mae if x < -50) / len(g)
        winr = 100 * sum(x["win"] for x in g) / len(g)
        print(f"  {name:<22} n={len(g):>4}  medMAE={med(mae):>7}  meanMAE={mean(mae):>7}  "
              f"rug<-30%={rug30:>5.1f}  rug<-50%={rug50:>5.1f}  med5dRet={med([x['ret5'] for x in g]):>7}  win%={winr:>5.1f}")

    by_label = defaultdict(list)
    by_class = defaultdict(list)
    for r in rows:
        by_label[r["q_label"]].append(r)
        by_class[r["q_class"] or "Ungraded"].append(r)

    n_tk = len({r["ticker"] for r in rows})
    n_graded_tk = len({r["ticker"] for r in rows if r["q_label"] != "Ungraded"})
    print(f"\n=== §1.1 test — drawdown by Quality grade ===")
    print(f"(rows={len(rows)}, tickers={n_tk}, graded tickers={n_graded_tk})\n")

    print("By risk label:")
    for lab in ["Green", "Yellow", "Red", "Black", "Ungraded"]:
        block(lab, by_label.get(lab, []))

    print("\nGrouped — Safe (Green+Yellow) vs Risky (Red+Black):")
    safe = by_label.get("Green", []) + by_label.get("Yellow", [])
    risky = by_label.get("Red", []) + by_label.get("Black", [])
    block("Safe (Green+Yellow)", safe)
    block("Risky (Red+Black)", risky)

    print("\nBy quality classification:")
    for c in ["Investable", "Speculative", "Too Hard", "Ungraded"]:
        block(c, by_class.get(c, []))

    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
