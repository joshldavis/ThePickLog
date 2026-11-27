#!/usr/bin/env python3
"""coverage_probe_exp13.py — which point-in-time S&P 500 members are missing from the EXP13
historical replay, and can a free source fill them?

Diagnostic only: reads prices, writes backtests/exp13-history/coverage-probe/. Computes NO
strategy result. Sources probed:
  yahoo   yfinance 1.7.0, as the replay used (the baseline)
  alpaca  Alpaca market data v2, SIP daily bars, split-adjusted (the project's existing keys;
          the free plan serves SIP history since 2016)
  stooq   stooq.com daily CSV, for a sample of missing names
"""
import csv
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

import backtest_exp13 as B

OUT = os.path.join(B.HERE, "backtests", "exp13-history", "coverage-probe")


def member_spans(pit):
    """{symbol: set(snapshot-window dates it was a member)} on trading dates in the window,
    using snapshot dates as the calendar proxy."""
    spans = {}
    first = max(i for i, (d, _) in enumerate(pit) if d <= B.WINDOW[0])
    rows = [(d, s) for d, s in pit[first:] if d <= B.WINDOW[1]]
    for k, (d, s) in enumerate(rows):
        end = rows[k + 1][0] if k + 1 < len(rows) else "9999"
        for t in s:
            spans.setdefault(t, []).append((max(d, B.WINDOW[0]), end))
    return spans


def alpaca_bars(symbols, start, end):
    key, sec = os.environ.get("ALPACA_KEY_ID", ""), os.environ.get("ALPACA_SECRET_KEY", "")
    if not (key and sec):
        print("alpaca: no keys in environment")
        return None
    out = {}
    hdr = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": sec, "User-Agent": "ThePickLog/1.0"}
    for k in range(0, len(symbols), 50):
        part = symbols[k:k + 50]
        token = None
        while True:
            q = {"symbols": ",".join(part), "timeframe": "1Day", "start": start, "end": end,
                 "adjustment": "split", "feed": "sip", "limit": 10000}
            if token:
                q["page_token"] = token
            url = "https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(q)
            j = None
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(urllib.request.Request(url, headers=hdr),
                                                timeout=30) as r:
                        j = json.loads(r.read().decode())
                    break
                except Exception as ex:
                    err = f"{type(ex).__name__}: {getattr(ex, 'code', '')} {str(ex)[:120]}"
                    time.sleep(2 * (attempt + 1))
            if j is None:
                print(f"alpaca chunk {k // 50 + 1} failed: {err}")
                break
            for s, bars in (j.get("bars") or {}).items():
                out.setdefault(s, []).extend(bars)
            token = j.get("next_page_token")
            if not token:
                break
            time.sleep(0.3)
    return out


def stooq_probe(symbols):
    got = {}
    for t in symbols:
        url = f"https://stooq.com/q/d/l/?s={t.lower()}.us&i=d"
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    url, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as r:
                txt = r.read().decode("utf-8", "replace")
            lines = [ln for ln in txt.splitlines() if ln and ln[0].isdigit()]
            got[t] = (len(lines), lines[0][:10] if lines else "", lines[-1][:10] if lines else "",
                      txt[:60].replace("\n", " ") if not lines else "")
        except Exception as ex:
            got[t] = (0, "", "", type(ex).__name__)
        time.sleep(0.5)
    return got


def main():
    os.makedirs(OUT, exist_ok=True)
    pit = B.load_pit()
    spans = member_spans(pit)
    ever = sorted(spans)
    print(f"{len(ever)} point-in-time members in the window")
    ydata = B.fetch_history(ever)
    usable = {t for t, b in ydata.items() if len(b) > B.MIN_BARS}
    missing = [t for t in ever if t not in usable]
    print(f"yahoo usable {len(usable)}, missing {len(missing)}")

    # member-days missing, by the year the span starts in (approximate weight)
    def span_days(t):
        n = 0
        for a, b in spans[t]:
            b = min(b, "2026-01-01")
            n += max(0, (int(b[:4]) - int(a[:4])) * 252 + (int(b[5:7]) - int(a[5:7])) * 21)
        return n

    ap = alpaca_bars([t.replace("-", ".") for t in missing], "2016-01-01", "2025-12-31")
    st = stooq_probe(missing[:40])
    rows = []
    for t in missing:
        a = (ap or {}).get(t.replace("-", "."), [])
        ad = sorted(b["t"][:10] for b in a)
        first_m = min(x for x, _ in spans[t])
        last_m = max(y for _, y in spans[t])
        in_span = sum(1 for d in ad if any(x <= d < y for x, y in spans[t]))
        s = st.get(t, ("", "", "", ""))
        rows.append({"symbol": t, "member_from": first_m, "member_to": last_m,
                     "approx_member_days": span_days(t),
                     "yahoo_bars": len(ydata.get(t, [])),
                     "alpaca_bars": len(ad), "alpaca_first": ad[0] if ad else "",
                     "alpaca_last": ad[-1] if ad else "", "alpaca_bars_in_membership": in_span,
                     "stooq_rows": s[0], "stooq_first": s[1], "stooq_last": s[2],
                     "stooq_note": s[3]})
    with io.open(os.path.join(OUT, "missing.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    tot = sum(r["approx_member_days"] for r in rows)
    post16 = [r for r in rows if r["member_to"] > "2016-01-01"]
    fill_a = sum(1 for r in post16 if r["alpaca_bars_in_membership"] > 0)
    print(f"missing members: {len(rows)}, approx member-days {tot}")
    print(f"members still in the index after 2016-01-01: {len(post16)}; alpaca has bars "
          f"in-membership for {fill_a}")
    print(f"alpaca returned data for {sum(1 for r in rows if r['alpaca_bars'])} symbols "
          f"(None means no keys/denied: {ap is None})")
    print(f"stooq sample: {sum(1 for t in st if st[t][0] > 0)}/{len(st)} with rows")
    for r in rows[:15]:
        print(" ", r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
