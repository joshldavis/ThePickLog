#!/usr/bin/env python3
"""
exit_sim.py — make EXIT RULES testable on the graded forward log.

The grader records only the max-favorable (MFE) and max-adverse (MAE) move over the
5-session window — not their ORDER — so it can't tell you what a profit target or stop
would actually have returned. This simulator fills that gap by replaying the **daily
OHLC path** of each graded pick and applying a grid of exit rules, then comparing win
rate / expectancy against the current hold-to-close baseline.

Why daily bars, not true intraday: intraday history expires (~60 days on Yahoo) and isn't
reproducible, which would break the "a stranger can verify" standard. Daily OHLC is always
retrievable and stable, so this study is fully reproducible. The one thing daily bars
can't resolve is a same-day collision where BOTH the target and the stop are touched — we
apply the **conservative convention (assume the STOP filled first)** so results can't be
optimistically inflated. Fills are assumed exactly at the level; the same 2% cost haircut
as the grader is applied. These are IN-SAMPLE exploratory results on a small N — a chosen
rule must be pre-registered (HYPOTHESES.md) and validated forward, never fit-and-shipped.

USAGE:
  python3 exit_sim.py --selftest          # offline logic check (no network)
  python3 exit_sim.py                      # fetch daily paths for graded picks, write report
NOT INVESTMENT ADVICE.
"""
import argparse, csv, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
HAIRCUT = 2.0          # match ignitionscan grader
WINDOW = 5             # trading sessions after entry (entry day + 5 -> 6 bars)


# ---------------------------------------------------------------------------
# PURE CORE (offline-testable): given entry price + daily bars, return net %.
# bars: list of {"o","h","l","c"}, bars[0] is the entry session.
# ---------------------------------------------------------------------------
def _ret(entry, exit_price):
    return (exit_price - entry) / entry * 100.0


def simulate(entry, bars, rule):
    """Gross % for one exit rule, before the cost haircut."""
    T, S, TR = rule.get("target"), rule.get("stop"), rule.get("trail")
    hi = entry * (1 + T / 100.0) if T else None
    lo = entry * (1 - S / 100.0) if S else None
    typ = rule["type"]
    last_c = bars[-1]["c"]

    if typ == "close0":
        return _ret(entry, bars[0]["c"])
    if typ == "hold":
        return _ret(entry, last_c)
    if typ == "target":
        for b in bars:
            if b["h"] >= hi:
                return _ret(entry, hi)
        return _ret(entry, last_c)
    if typ == "stop":
        for b in bars:
            if b["l"] <= lo:
                return _ret(entry, lo)
        return _ret(entry, last_c)
    if typ == "target_stop":
        for b in bars:
            hit_t, hit_s = b["h"] >= hi, b["l"] <= lo
            if hit_s:                       # conservative: stop wins a same-day collision
                return _ret(entry, lo)
            if hit_t:
                return _ret(entry, hi)
        return _ret(entry, last_c)
    if typ == "trail":
        peak = entry
        for b in bars:
            trail_lvl = peak * (1 - TR / 100.0)   # peak known ENTERING this session
            if b["l"] <= trail_lvl:
                return _ret(entry, trail_lvl)
            peak = max(peak, b["h"])              # today's high only arms tomorrow's stop
        return _ret(entry, last_c)
    # --- batch #2 rule types (H-EX3..H-EX9, registered 2026-07-02) ---
    if typ == "closeN":                      # H-EX5: exit at day-N close (bars[0] = entry day)
        n = rule["day"]
        return _ret(entry, bars[min(n, len(bars) - 1)]["c"])
    if typ == "target_timestop":             # H-EX4: target live through day-N only; unfilled -> day-N close
        n = rule["day"]
        for b in bars[:n + 1]:
            if b["h"] >= hi:
                return _ret(entry, hi)
        return _ret(entry, bars[min(n, len(bars) - 1)]["c"])
    if typ == "partial":                     # H-EX6: half fills at target, half rides to last close
        for b in bars:
            if b["h"] >= hi:
                return 0.5 * _ret(entry, hi) + 0.5 * _ret(entry, last_c)
        return _ret(entry, last_c)
    if typ == "target_trail":                # H-EX7: trail arms only AFTER a +target touch;
        armed = False                        # trail level from PRIOR sessions' peak only
        peak = entry                         # (no same-day ratchet; touch day can't exit on the trail)
        for b in bars:
            trail_lvl = peak * (1 - TR / 100.0)
            if armed and b["l"] <= trail_lvl:
                return _ret(entry, trail_lvl)
            if b["h"] >= hi:
                armed = True                 # arms starting the NEXT session
            peak = max(peak, b["h"])
        return _ret(entry, last_c)
    raise ValueError("unknown rule type " + typ)


def net(entry, bars, rule):
    return simulate(entry, bars, rule) - HAIRCUT


RULES = [
    {"name": "Same-day close (current)", "type": "close0"},
    {"name": "Hold to 5d close", "type": "hold"},
    {"name": "Target +10%", "type": "target", "target": 10},
    {"name": "Target +15%", "type": "target", "target": 15},
    {"name": "Target +20%", "type": "target", "target": 20},
    {"name": "Target +30%", "type": "target", "target": 30},
    {"name": "Stop -10%", "type": "stop", "stop": 10},
    {"name": "Stop -15%", "type": "stop", "stop": 15},
    {"name": "H-EX2 +10% target / -20% stop [registered 2026-06-24]", "type": "target_stop", "target": 10, "stop": 20},
    {"name": "Target +20% / Stop -10%", "type": "target_stop", "target": 20, "stop": 10},
    {"name": "Target +15% / Stop -10%", "type": "target_stop", "target": 15, "stop": 10},
    {"name": "Target +20% / Stop -15%", "type": "target_stop", "target": 20, "stop": 15},
    {"name": "Trailing 15%", "type": "trail", "trail": 15},
    {"name": "Trailing 20%", "type": "trail", "trail": 20},
    # --- batch #2, registered 2026-07-02 (HYPOTHESES.md "Exit-rule batch #2") ---
    {"name": "H-EX3 Target +5% [registered 2026-07-02]", "type": "target", "target": 5},
    {"name": "H-EX4 +10% target / day-2 time stop [registered 2026-07-02]", "type": "target_timestop", "target": 10, "day": 2},
    {"name": "H-EX5a Day-1 close [registered 2026-07-02]", "type": "closeN", "day": 1},
    {"name": "H-EX5b Day-2 close [registered 2026-07-02]", "type": "closeN", "day": 2},
    {"name": "H-EX6 half at +10%, half to 5d close [registered 2026-07-02]", "type": "partial", "target": 10},
    {"name": "H-EX7 trail 15% after +10% touch [registered 2026-07-02]", "type": "target_trail", "target": 10, "trail": 15},
    {"name": "H-EX8 tier target A/B +20%, C/D +10% [registered 2026-07-02]", "type": "tier_target", "targets": {"AB": 20, "CD": 10}},
    {"name": "H-EX9a +10% target / -10% stop [registered 2026-07-02]", "type": "target_stop", "target": 10, "stop": 10},
    {"name": "H-EX9b +10% target / -30% stop [registered 2026-07-02]", "type": "target_stop", "target": 10, "stop": 30},
]


def resolve_rule(rule, tier):
    """H-EX8 is the one pick-dependent rule: the target level depends on the pick's tier.
    Resolve it to a concrete uniform rule; all other rules pass through unchanged."""
    if rule["type"] == "tier_target":
        t = rule["targets"]["AB" if tier in ("A", "B") else "CD"]
        return {"type": "target", "target": t}
    return rule


# ---------------------------------------------------------------------------
# Data (network): daily bars for each graded pick
# ---------------------------------------------------------------------------
def _read(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load_paths():
    """Grade-time daily paths persisted by the grader (paths.csv). These are the
    REPRODUCIBLE source — captured from the same fetch that produced the outcome, so they
    can't drift like a re-fetch can. Returns {pick_id: [bar, …]} sorted by session_idx."""
    rows = _read(os.path.join(HERE, "paths.csv"))
    by_pid = {}
    for r in rows:
        pid = r.get("pick_id")
        b = {"i": int(r["session_idx"]),
             "o": _f(r["open"]), "h": _f(r["high"]), "l": _f(r["low"]), "c": _f(r["close"])}
        if None in (b["o"], b["h"], b["l"], b["c"]):
            continue
        by_pid.setdefault(pid, []).append(b)
    out = {}
    for pid, bars in by_pid.items():
        bars.sort(key=lambda x: x["i"])
        if len(bars) >= WINDOW + 1:
            out[pid] = [{"o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]} for b in bars[:WINDOW + 1]]
    return out


def fetch_bars(ticker, start):
    """Daily OHLC window: entry session + WINDOW sessions (<= WINDOW+1 bars)."""
    import yfinance as yf
    from datetime import datetime, timedelta
    end = (datetime.strptime(start, "%Y-%m-%d") + timedelta(days=16)).strftime("%Y-%m-%d")
    df = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
    if df is None or len(df) == 0:
        return None
    df = df.reset_index()
    df["d"] = df["Date"].astype(str).str[:10]
    idx = df.index[df["d"] == start]
    if len(idx) == 0:
        return None
    i0 = idx[0]
    w = df.iloc[i0:i0 + WINDOW + 1]
    if len(w) < WINDOW + 1:
        return None
    return [{"o": float(r["Open"]), "h": float(r["High"]),
             "l": float(r["Low"]), "c": float(r["Close"])} for _, r in w.iterrows()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()

    # COHORT SEAL (H-UNIV1, 2026-07-08): the exit study + every H-EX registration
    # were frozen against the v0.2 fixed-16 record; replay that closed cohort only.
    picks = {p["pick_id"]: p for p in _read(os.path.join(HERE, "picks.csv"))
             if (p.get("model_version") or "").startswith("v0.2")}
    outs = _read(os.path.join(HERE, "outcomes.csv"))
    graded = [o for o in outs if o.get("pick_id") in picks
              and _f(o.get("entry_open")) and _f(o.get("ret_open_close_net")) is not None]

    paths = load_paths()  # pick_id -> grade-time bars (the reproducible source)
    results = {r["name"]: [] for r in RULES}
    used = from_record = 0
    for o in graded:
        entry = _f(o.get("entry_open"))
        bars = paths.get(o.get("pick_id"))
        if bars:
            from_record += 1
        else:
            try:
                bars = fetch_bars(o["ticker"], o["trading_date"])
            except Exception as e:
                print(f"  fetch skip {o['ticker']} {o['trading_date']}: {type(e).__name__}")
        if not bars:
            continue
        used += 1
        tier = (picks.get(o.get("pick_id")) or {}).get("tier", "")
        for r in RULES:
            results[r["name"]].append(net(entry, bars, resolve_rule(r, tier)))

    _write_report(results, used, len(graded), from_record)


def _agg(xs):
    if not xs:
        return (float("nan"), float("nan"), float("nan"))
    wr = 100.0 * sum(1 for x in xs if x > 0) / len(xs)
    return (wr, st.mean(xs), st.median(xs))


def _write_report(results, used, n_graded, from_record=0):
    from datetime import datetime
    fetched = used - from_record
    prov = (f"{from_record} from the append-only grade-time record (paths.csv), {fetched} "
            "re-fetched (picks that predate path capture)")
    L = ["# ThePickLog — exit-rule study · " + datetime.utcnow().date().isoformat(), "",
         f"Daily-resolution replay of **{used}** graded picks (of {n_graded}). Conservative "
         "same-day tie (stop fills first); 2% cost haircut; fills at level. **In-sample / "
         "exploratory** — a chosen rule must be pre-registered and validated forward.", "",
         f"_Bar provenance: {prov}. Grade-time paths are reproducible from committed data; "
         "re-fetched bars can drift if Yahoo revises history, so they converge to the "
         "append-only source as the record matures._", "",
         "| exit rule | n | win% | avg net/trade | median |", "|---|---|---|---|---|"]
    base = None
    rows = []
    for r in RULES:
        wr, mean, med = _agg(results[r["name"]])
        rows.append((r["name"], wr, mean, med))
        if r["type"] == "close0":
            base = mean
    for name, wr, mean, med in rows:
        star = ""
        if base is not None and mean == mean and mean - base >= 2.0 and "current" not in name:
            star = " ⭐"
        L.append(f"| {name}{star} | {len(results[name])} | {wr:.0f}% | {mean:+.1f}% | {med:+.1f}% |")
    L += ["", "⭐ = avg net/trade at least +2pp better than the current same-day-close exit.",
          "",
          "**Read the median, not just the mean.** When a rule's avg net is far above its "
          "median (e.g. trailing stops), the average is carried by a few outlier runners — the "
          "*typical* trade is the median, which may still be negative. Such rules are high-"
          "variance and unreliable at this N.",
          "",
          "**Slippage caveat:** target/stop/trailing fills are assumed exactly at the level. On "
          "thin low-float names, gaps blow through stops and you rarely fill a target cleanly, so "
          "real-world results for stop/trailing rules would be **worse** than shown here. The 2% "
          "haircut does not capture gap-through slippage.",
          "",
          "_Not investment advice. In-sample/exploratory; a rule must be pre-registered "
          "(HYPOTHESES.md) and validated on post-registration picks before it means anything._"]
    os.makedirs(os.path.join(HERE, "reports"), exist_ok=True)
    out = os.path.join(HERE, "reports", "exit-study-LATEST.md")
    with open(out, "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nwrote {out}")


def _selftest():
    # Construct a known path and verify each rule exits where expected.
    entry = 100.0
    # day0: o100 h112 l95 c108 ; day1: h120 l104 c118 ; day2: h130 l85 c90
    bars = [{"o": 100, "h": 112, "l": 95, "c": 108},
            {"o": 108, "h": 120, "l": 104, "c": 118},
            {"o": 118, "h": 130, "l": 85, "c": 90}]
    g = lambda rule: round(simulate(entry, bars, rule), 1)
    assert g({"type": "close0"}) == 8.0, g({"type": "close0"})
    assert g({"type": "hold"}) == -10.0
    assert g({"type": "target", "target": 10}) == 10.0          # day0 high 112 >= 110
    assert g({"type": "target", "target": 25}) == 25.0          # day1 high 120 >= 125? no -> day2 130>=125 yes
    assert g({"type": "stop", "stop": 10}) == -10.0             # day2 low 85 <= 90
    # target+stop: +20% (120) vs -10% (90). day0: h112<120,l95>90 none. day1: h120>=120 hit_t, l104>90 -> +20.
    assert g({"type": "target_stop", "target": 20, "stop": 10}) == 20.0
    # collision day2 if target high: +35/-10 -> stop first. target 35 -> 135 never; use target 28 (128) and stop 12 (88): day2 h130>=128 AND l85<=88 -> conservative stop -> -12
    assert g({"type": "target_stop", "target": 28, "stop": 12}) == -12.0
    # trailing 15% (peak known entering each session): day0 trail=85, low95>85 keep, peak->112;
    # day1 trail=95.2, low104>95.2 keep, peak->120; day2 trail=102, low85<=102 -> exit 102 -> +2.0
    assert g({"type": "trail", "trail": 15}) == 2.0, g({"type": "trail", "trail": 15})
    # --- batch #2 rule types ---
    # closeN: day-1 close 118 -> +18 ; day-2 close 90 -> -10
    assert g({"type": "closeN", "day": 1}) == 18.0
    assert g({"type": "closeN", "day": 2}) == -10.0
    # target_timestop: +25% target never touched by day-1 (h112, h120 < 125) -> exit day-1 close +18
    # (plain +25% target would have filled day2 at 130>=125 -> the time stop is what changed the result)
    assert g({"type": "target_timestop", "target": 25, "day": 1}) == 18.0
    # target_timestop: +10% target touched day0 (112>=110) -> +10, time stop never reached
    assert g({"type": "target_timestop", "target": 10, "day": 2}) == 10.0
    # partial: half fills at +10 (day0), half rides to last close (-10) -> 0.0
    assert g({"type": "partial", "target": 10}) == 0.0
    # target_trail 15% after +10% touch: day0 h112>=110 arms (no same-day exit), peak->112;
    # day1 trail=95.2, low104 holds, peak->120; day2 trail=102, low85<=102 -> exit 102 -> +2.0
    assert g({"type": "target_trail", "target": 10, "trail": 15}) == 2.0
    # target_trail never armed: +40% target never touched -> 5d close -10
    assert g({"type": "target_trail", "target": 40, "trail": 15}) == -10.0
    # resolve_rule: tier A -> +20 target, tier D -> +10 target
    r8 = {"type": "tier_target", "targets": {"AB": 20, "CD": 10}}
    assert resolve_rule(r8, "A") == {"type": "target", "target": 20}
    assert resolve_rule(r8, "D") == {"type": "target", "target": 10}
    assert g(resolve_rule(r8, "A")) == 20.0   # day1 h120 >= 120
    assert g(resolve_rule(r8, "D")) == 10.0   # day0 h112 >= 110
    print("exit_sim selftest PASS — all rule paths exit where expected")
    print("  (target+stop collision correctly resolves to the stop — conservative)")
    print("  (batch #2: closeN / target_timestop / partial / target_trail / tier_target verified)")


if __name__ == "__main__":
    main()
