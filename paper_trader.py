#!/usr/bin/env python3
"""
paper_trader.py — H-V3-PAPER instrumentation (HYPOTHESES.md, registered 2026-07-13).

Trades the H-V3-EX1 rule (+10% target over a 5-trading-day hold) mechanically on
published v0.3 picks in an Alpaca PAPER account, so the fills-at-level proxy used by
every exit hypothesis can be compared against actual (paper) fills. This is
MEASUREMENT, not a strategy endorsement: the registered prior for the exit family is
skeptical, and nothing here touches real money.

SAFETY: the endpoint is HARDCODED to paper-api.alpaca.markets. There is no flag,
env var, or code path that reaches a live account. Live keys fail here (403).

Modes (each run is idempotent — safe to re-run):
  enter   (premarket)   buy today's published v0.3-yf picks: OPG market order
                        (fills at the opening auction = the hypothesis's entry),
                        fixed notional (PAPER_NOTIONAL, default $200), whole shares.
                        Skips picks already entered and symbols already held
                        (no overlapping holds of the same name — H-DEDUP spirit).
  arm     (~9:40am ET)  for filled entries without a take-profit: place a GTC
                        limit sell at fill_price × 1.10. The few minutes between
                        the open and arming are a DISCLOSED gap — a touch inside
                        it is missed, which can only understate the paper arm.
  manage  (~3:45pm ET)  time-exit: when ≥5 trading sessions have elapsed since
                        entry (Alpaca calendar, entry day = session 0), cancel the
                        resting limit and close the remaining position at market
                        (~the 5-day close, 15 min early — disclosed). Also
                        snapshots order statuses into the event log.

Every action appends to paper_trades.csv (forward-only event log, committed by the
Action) so a stranger can replay the account's history. NOT INVESTMENT ADVICE.
"""
import csv, json, math, os, sys, urllib.request, urllib.error
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "paper_trades.csv")
PICKS = os.path.join(HERE, "picks.csv")
BASE = "https://paper-api.alpaca.markets/v2"   # PAPER ONLY — never live (see docstring)
COHORT = "v0.3-yf"
TARGET = 0.10           # H-V3-EX1 (+10%)
HOLD_SESSIONS = 5       # entry day = session 0; exit on session 5 (the "5-day close")
NOTIONAL = float(os.environ.get("PAPER_NOTIONAL", "200"))
ET = ZoneInfo("America/New_York")

FIELDS = ["ts_utc", "mode", "pick_id", "ticker", "event", "qty", "price",
          "order_id", "status", "note"]


def _keys():
    k, s = os.environ.get("ALPACA_KEY_ID"), os.environ.get("ALPACA_SECRET_KEY")
    if not k or not s:
        print("ALPACA_KEY_ID / ALPACA_SECRET_KEY not set — paper trader skipped.")
        sys.exit(0)
    return k, s


def _req(method, path, body=None):
    k, s = _keys()
    req = urllib.request.Request(BASE + path, method=method,
                                 data=json.dumps(body).encode() if body else None)
    req.add_header("APCA-API-KEY-ID", k)
    req.add_header("APCA-API-SECRET-KEY", s)
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            t = r.read().decode()
            return (json.loads(t) if t else {}), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:200]}"
    except Exception as e:  # noqa: BLE001 — logged, never crashes the workflow
        return None, str(e)


def _log_rows():
    if not os.path.exists(LOG):
        return []
    return list(csv.DictReader(open(LOG)))


def _append(rows):
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        for r in rows:
            r.setdefault("ts_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"))
            w.writerow({k: r.get(k, "") for k in FIELDS})
            print("log:", r.get("event"), r.get("ticker"), r.get("note", ""))


def _round_px(px):
    return round(px, 4) if px < 1 else round(px, 2)


def _picks_today():
    today = datetime.now(ET).date().isoformat()
    out = []
    for r in csv.DictReader(open(PICKS)):
        if r.get("model_version") == COHORT and r.get("trading_date") == today:
            out.append(r)
    return out


def _positions():
    pos, err = _req("GET", "/positions")
    return {p["symbol"]: p for p in (pos or [])}, err


def enter(mode="enter"):
    done = {r["pick_id"] for r in _log_rows() if r["event"] == "entry_submitted"}
    held, err = _positions()
    if err:
        _append([{"mode": mode, "event": "error", "note": f"positions: {err}"}]); return
    rows = []
    for p in _picks_today():
        pid, sym = p["pick_id"], p["ticker"]
        if pid in done:
            continue
        if sym in held:
            rows.append({"mode": mode, "pick_id": pid, "ticker": sym, "event": "entry_skip",
                         "note": "symbol already held (no overlapping holds)"})
            continue
        try:
            px = float(p["price_at_screen"])
        except (TypeError, ValueError):
            px = 0
        if px <= 0:
            rows.append({"mode": mode, "pick_id": pid, "ticker": sym, "event": "entry_skip",
                         "note": "no screen price"})
            continue
        qty = max(1, math.floor(NOTIONAL / px))
        o, err = _req("POST", "/orders", {
            "symbol": sym, "qty": str(qty), "side": "buy", "type": "market",
            "time_in_force": "opg", "client_order_id": f"plog-{pid}"[:48]})
        if err:
            rows.append({"mode": mode, "pick_id": pid, "ticker": sym, "event": "entry_reject",
                         "qty": qty, "note": err})
        else:
            rows.append({"mode": mode, "pick_id": pid, "ticker": sym, "event": "entry_submitted",
                         "qty": qty, "order_id": o.get("id", ""), "status": o.get("status", "")})
    _append(rows or [{"mode": mode, "event": "noop", "note": "no new v0.3 picks today"}])


def arm(mode="arm"):
    log = _log_rows()
    entries = {r["pick_id"]: r for r in log if r["event"] == "entry_submitted"}
    armed = {r["pick_id"] for r in log if r["event"] in ("tp_submitted", "time_exit")}
    rows = []
    for pid, e in entries.items():
        if pid in armed:
            continue
        o, err = _req("GET", f"/orders:by_client_order_id?client_order_id=plog-{pid}"[:200])
        if err or not o:
            rows.append({"mode": mode, "pick_id": pid, "ticker": e["ticker"],
                         "event": "arm_error", "note": err or "order not found"})
            continue
        if o.get("status") != "filled":
            rows.append({"mode": mode, "pick_id": pid, "ticker": e["ticker"],
                         "event": "entry_status", "status": o.get("status", ""),
                         "note": "not filled yet — will retry next run"})
            continue
        fill = float(o["filled_avg_price"])
        qty = o["filled_qty"]
        tp_px = _round_px(fill * (1 + TARGET))
        tp, err = _req("POST", "/orders", {
            "symbol": e["ticker"], "qty": qty, "side": "sell", "type": "limit",
            "limit_price": str(tp_px), "time_in_force": "gtc",
            "client_order_id": f"plogtp-{pid}"[:48]})
        if err:
            rows.append({"mode": mode, "pick_id": pid, "ticker": e["ticker"],
                         "event": "tp_reject", "price": tp_px, "note": err})
        else:
            rows.append({"mode": mode, "pick_id": pid, "ticker": e["ticker"],
                         "event": "tp_submitted", "qty": qty, "price": tp_px,
                         "order_id": tp.get("id", ""), "status": tp.get("status", ""),
                         "note": f"entry fill {fill}"})
    _append(rows or [{"mode": mode, "event": "noop", "note": "nothing to arm"}])


def _sessions_since(entry_date):
    cal, err = _req("GET", f"/calendar?start={entry_date}&end={date.today().isoformat()}")
    if err or not cal:
        return None
    return len(cal) - 1   # entry day = session 0


def manage(mode="manage"):
    log = _log_rows()
    entries = {r["pick_id"]: r for r in log if r["event"] == "entry_submitted"}
    exited = {r["pick_id"] for r in log if r["event"] == "time_exit"}
    entry_day = {}
    for r in log:   # entry trading day = ET date of the entry_submitted row
        if r["event"] == "entry_submitted":
            entry_day[r["pick_id"]] = datetime.fromisoformat(r["ts_utc"]).astimezone(ET).date().isoformat()
    held, err = _positions()
    if err:
        _append([{"mode": mode, "event": "error", "note": f"positions: {err}"}]); return
    rows = []
    for pid, e in entries.items():
        if pid in exited:
            continue
        sess = _sessions_since(entry_day.get(pid, ""))
        if sess is None or sess < HOLD_SESSIONS:
            continue
        sym = e["ticker"]
        # cancel the resting take-profit (if any), then close whatever remains
        tp, _ = _req("GET", f"/orders:by_client_order_id?client_order_id=plogtp-{pid}"[:200])
        if tp and tp.get("status") in ("new", "accepted", "partially_filled"):
            _req("DELETE", f"/orders/{tp['id']}")
        if sym in held:
            c, err = _req("DELETE", f"/positions/{sym}")
            note = f"session {sess} time exit" + (f" | close error: {err}" if err else "")
            rows.append({"mode": mode, "pick_id": pid, "ticker": sym, "event": "time_exit",
                         "qty": held[sym].get("qty", ""), "note": note})
        else:
            rows.append({"mode": mode, "pick_id": pid, "ticker": sym, "event": "time_exit",
                         "note": f"session {sess}: no position left (target filled or entry never filled)"})
    # snapshot fills of take-profits so the log shows realized exits
    for r in log:
        if r["event"] == "tp_submitted" and r["pick_id"] not in \
                {x["pick_id"] for x in log if x["event"] == "tp_filled"}:
            o, _ = _req("GET", f"/orders:by_client_order_id?client_order_id=plogtp-{r['pick_id']}"[:200])
            if o and o.get("status") == "filled":
                rows.append({"mode": mode, "pick_id": r["pick_id"], "ticker": r["ticker"],
                             "event": "tp_filled", "qty": o.get("filled_qty", ""),
                             "price": o.get("filled_avg_price", "")})
    _append(rows or [{"mode": mode, "event": "noop", "note": "nothing due"}])


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "manage"
    {"enter": enter, "arm": arm, "manage": manage}[m]()
