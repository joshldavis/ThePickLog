#!/usr/bin/env python3
"""
hypo_eval.py — generic evaluator for pre-registered hypotheses (Compete → Test mode, Phase 0).

Scores ANY declarative rule_json (see hypotheses/registry.json) against the immutable
pick log, returning an honest out-of-sample scorecard: expectancy delta vs the shared
same-day-close baseline, a bootstrap 95% CI on that delta, significance, and a
ranked/maturing state. Stdlib only. Deterministic (fixed seed).

This is the single source of truth the site's own hypotheses AND (Phase 1) user
hypotheses run through — same code, same math, applied evenhandedly.

Run directly:  python hypo_eval.py   -> writes leaderboard.json, runs self-tests.
"""
import csv, json, random, statistics as st, sys
from datetime import date

# ------------------------------------------------------------------ log I/O
def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

def load_log(picks_path="picks.csv", outs_path="outcomes.csv"):
    picks = {r["pick_id"]: r for r in csv.DictReader(open(picks_path))}
    outs = list(csv.DictReader(open(outs_path)))
    return picks, outs

# ------------------------------------------------------------------ predicates
_NUMERIC_CMP = {">=", ">", "<=", "<"}

def _test_pred(pick, pred):
    """One predicate. Missing/unparseable field => passes (matches weekly_report's
    `x is None or x >= v` convention: absent data never excludes a pick)."""
    raw = pick.get(pred["field"])
    cmp, val = pred["cmp"], pred["value"]
    if cmp in _NUMERIC_CMP:
        x = _f(raw)
        if x is None:
            return True
        return (x >= val if cmp == ">=" else x > val if cmp == ">"
                else x <= val if cmp == "<=" else x < val)
    s = (raw or "").strip()
    if cmp == "==":     return s == str(val)
    if cmp == "!=":     return s != str(val)
    if cmp == "in":     return s in set(map(str, val))
    if cmp == "not_in": return s not in set(map(str, val))
    raise ValueError(f"unknown cmp {cmp!r}")

def _keeps(pick, selection):
    preds = selection.get("predicates", [])
    if not preds:
        return True                      # no selection => all picks (exit-kind)
    return all(_test_pred(pick, p) for p in preds)   # op "and" (v1)

# ------------------------------------------------------------------ exits
def _exit_return(o, exit_id):
    """Realized return for one graded outcome under an exit rule, or None if the
    needed columns are absent. Maps onto grader outputs only — no new data."""
    scc = _f(o.get("ret_open_close_net"))
    if exit_id == "same_day_close":
        return scc
    c5, mfe = _f(o.get("ret_open_5dclose_net")), _f(o.get("mfe_5d"))
    if exit_id == "same_day_close":
        return scc
    if exit_id.startswith("target_"):
        T = 10.0 if exit_id == "target_10" else float(exit_id.split("_")[1])
        if mfe is None or c5 is None:
            return None
        return (T - 2.0) if mfe >= T else c5   # +T limit, minus 2% cost haircut
    raise ValueError(f"unknown exit {exit_id!r}")

_SLIP = "slippage: +T% fills assumed exact; on thin floats limits gap through, so live results run worse than this proxy"

# ------------------------------------------------------------------ stats
def _mean(xs):  return sum(xs) / len(xs)

def _two_sample_ci(a, b, iters, rng):
    """95% CI for mean(a) - mean(b), independent resampling (filter kind)."""
    if len(a) < 2 or len(b) < 2:
        return None
    d = []
    for _ in range(iters):
        sa = [a[rng.randrange(len(a))] for _ in a]
        sb = [b[rng.randrange(len(b))] for _ in b]
        d.append(_mean(sa) - _mean(sb))
    d.sort()
    return [round(d[int(.025 * iters)], 1), round(d[int(.975 * iters)], 1)]

def _paired_ci(diffs, iters, rng):
    """95% CI for the mean paired difference (exit kind: same picks, two exits)."""
    if len(diffs) < 2:
        return None
    d = []
    for _ in range(iters):
        s = [diffs[rng.randrange(len(diffs))] for _ in diffs]
        d.append(_mean(s))
    d.sort()
    return [round(d[int(.025 * iters)], 1), round(d[int(.975 * iters)], 1)]

def _state(kept_n, base_n, min_n, min_keep_frac):
    if base_n and kept_n / base_n < min_keep_frac:
        return "insufficient"
    if kept_n >= min_n:
        return "ranked"
    return "maturing" if kept_n >= 1 else "insufficient"

def _weeks(reg, asof):
    return round((asof - date.fromisoformat(reg)).days / 7, 1)

# ------------------------------------------------------------------ core
def evaluate(rule, picks, outs, cfg, asof):
    rng = random.Random(cfg["seed"])
    iters = cfg["boot_iters"]
    reg = rule["registered_at"]
    kind = rule["kind"]

    def post(o):
        p = picks.get(o["pick_id"])
        return p and p.get("trading_date", "") > reg

    if kind in ("filter", "question"):
        exit_id = rule.get("exit", "same_day_close")
        base_all, base_post, kept_all, kept_post = [], [], [], []
        for o in outs:
            p = picks.get(o["pick_id"])
            if not p:
                continue
            r = _exit_return(o, exit_id)
            if r is None:
                continue
            keep = _keeps(p, rule["selection"])
            base_all.append(r)
            if keep: kept_all.append(r)
            if post(o):
                base_post.append(r)
                if keep: kept_post.append(r)
        ci = _two_sample_ci(kept_post, base_post, iters, rng)
        delta = round(_mean(kept_post) - _mean(base_post), 1) if kept_post and base_post else None
        card = _card(rule, kept_post, base_post, delta, ci, cfg, asof, kind)
        card["kept_n_all"] = len(kept_all)
        return card

    if kind == "exit":
        pairs, base_post, arm_post = [], [], []
        for o in outs:
            if not post(o):
                continue
            alt = _exit_return(o, rule["exit"])
            base = _exit_return(o, "same_day_close")
            if alt is None or base is None:
                continue
            pairs.append(alt - base)
            arm_post.append(alt)
            base_post.append(base)
        ci = _paired_ci(pairs, iters, rng)
        delta = round(_mean(pairs), 1) if pairs else None
        card = _card(rule, arm_post, base_post, delta, ci, cfg, asof, kind)
        card["caveats"] = [_SLIP]
        return card

    raise ValueError(f"unknown kind {rule['kind']!r}")

def _card(rule, arm, base_post, delta, ci, cfg, asof, kind):
    n = len(arm)
    sig = bool(ci) and (ci[0] > 0 or ci[1] < 0)
    return {
        "id": rule["id"], "title": rule["title"], "author": rule["author"],
        "registered_at": rule["registered_at"], "kind": kind,
        "rule_str": rule_to_str(rule),
        "n_post": n,
        "win_post": round(100 * sum(1 for r in arm if r > 0) / n) if n else None,
        "avg_post": round(_mean(arm), 1) if n else None,
        "median_post": round(st.median(arm), 1) if n else None,
        "baseline_avg_post": round(_mean(base_post), 1) if base_post else None,
        "delta_post": delta,
        "ci95": ci,
        "significant": sig,
        "state": _state(n, len(base_post), cfg["min_n"], cfg["min_keep_frac"]),
        "stability": "unknown",     # set once weekly snapshot history exists
        "weeks_live": _weeks(rule["registered_at"], asof),
        "caveats": [],
        # Machine-readable spec so the browser can re-derive THIS rule from the raw
        # CSVs on the verify page (dashboard.html#verify=...). Pick-time fields only.
        "rule_spec": {
            "kind": kind,
            "exit": rule.get("exit", "same_day_close"),
            "registered_at": rule["registered_at"],
            "predicates": (rule.get("selection") or {}).get("predicates", []),
        },
    }

_CMP_STR = {">=": "≥", ">": ">", "<=": "≤", "<": "<", "==": "=", "!=": "≠",
            "in": "∈", "not_in": "∉"}

def rule_to_str(rule):
    if rule["kind"] == "exit":
        return {"target_10": "exit: mfe_5d ≥ +10% → +8% net, else 5d close"}.get(
            rule["exit"], f"exit: {rule['exit']}")
    parts = []
    for p in rule["selection"]["predicates"]:
        v = p["value"]
        v = "{" + ", ".join(map(str, v)) + "}" if isinstance(v, list) else (
            f"{v:,.0f}" if isinstance(v, (int, float)) and v >= 1000 else v)
        parts.append(f"{p['field']} {_CMP_STR[p['cmp']]} {v}")
    return "keep: " + " ∧ ".join(parts)

# ------------------------------------------------------------------ user rules (Phase 1)
# Pick-time field whitelist (defence-in-depth; mirrors the SQL register RPC). A user
# rule may only select on fields KNOWN AT PICK TIME — never outcome columns — so no
# hypothesis can reference the future. Anything else is dropped, not trusted.
_USER_FIELDS = {"price_at_screen", "float_shares", "gap_pct", "rvol", "short_interest_pct", "tier"}
_USER_EXITS  = {"same_day_close", "target_5", "target_10", "target_15", "target_20"}

def _map_user_rule(row):
    """Map one Supabase is_hypotheses row to the evaluator's hypothesis shape, or
    None if it fails validation (malformed, disallowed field/exit, retired)."""
    try:
        if row.get("status", "active") != "active":
            return None
        kind = row["kind"]
        if kind not in ("filter", "exit"):
            return None
        exit_id = row.get("exit_id", "same_day_close")
        if exit_id not in _USER_EXITS:
            return None
        sel = row.get("rule_json") or {"op": "and", "predicates": []}
        preds = sel.get("predicates", []) if isinstance(sel, dict) else []
        for p in preds:
            if p.get("field") not in _USER_FIELDS:   # any bad field => reject whole rule
                return None
        if kind == "filter" and not preds:
            return None
        return {
            "id": "U-" + str(row["id"])[:8],
            "title": (row.get("title") or "untitled").strip()[:80],
            "author": (row.get("author_name") or row.get("author")
                       or (row.get("is_profiles") or {}).get("display_name") or "anon"),
            "registered_at": str(row["registered_at"])[:10],
            "kind": kind,
            "selection": {"op": "and", "predicates": preds},
            "exit": exit_id,
            "claim": {"metric": "expectancy", "direction": "beats_baseline"},
        }
    except (KeyError, TypeError, AttributeError):
        return None

def load_user_hypotheses(path):
    """Read a JSON array of Supabase is_hypotheses rows (as fetched by the Action)
    and return validated evaluator-shape hypotheses. Missing/bad file => []."""
    try:
        raw = json.load(open(path))
    except (FileNotFoundError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    return [h for h in (_map_user_rule(r) for r in raw) if h]

# ------------------------------------------------------------------ registry
def evaluate_registry(registry_path="hypotheses/registry.json",
                      picks_path="picks.csv", outs_path="outcomes.csv", asof=None,
                      user_path=None):
    reg = json.load(open(registry_path))
    cfg = reg["config"]
    picks, outs = load_log(picks_path, outs_path)
    asof = asof or date.today()
    users = load_user_hypotheses(user_path) if user_path else []
    rows = [evaluate(h, picks, outs, cfg, asof) for h in (reg["hypotheses"] + users)]

    # rank the ranked ones by delta desc; maturing/insufficient listed after, unranked
    ranked = sorted([r for r in rows if r["state"] == "ranked"],
                    key=lambda r: (r["delta_post"] is None, -(r["delta_post"] or 0)))
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    for r in rows:
        r.setdefault("rank", None)

    n_live = len(rows)
    n_pos = sum(1 for r in rows if (r["delta_post"] or 0) > 0)
    n_sig = sum(1 for r in rows if r["significant"])
    # baseline shown on the board = post-reg same-day-close over the widest window (earliest reg)
    earliest = min(h["registered_at"] for h in reg["hypotheses"])
    base_ret = [_exit_return(o, "same_day_close") for o in outs
                if (p := picks.get(o["pick_id"])) and p.get("trading_date", "") > earliest]
    base_ret = [r for r in base_ret if r is not None]

    return {
        "generated_at": asof.isoformat(),
        "log": {"picks": len(picks), "graded": len(outs)},
        "baseline": {
            "n_post": len(base_ret),
            "win_post": round(100 * sum(1 for r in base_ret if r > 0) / len(base_ret)) if base_ret else None,
            "avg_post": round(_mean(base_ret), 1) if base_ret else None,
            "since": earliest,
        },
        "summary": {
            "n_live": n_live, "n_positive_point": n_pos, "n_significant": n_sig,
            "expected_positive_by_chance": round(0.5 * n_live, 1),
            "note": "under the null each rule has ~50% chance of a positive point estimate; "
                    "clearing the 95% CI is the real bar",
        },
        "rows": sorted(rows, key=lambda r: (r["rank"] is None, r["rank"] or 0,
                                            -(r["delta_post"] or -99))),
    }

# ------------------------------------------------------------------ self-test
def _selftest():
    """Golden-master parity gate: deterministic point stats must match the hand-coded
    weekly_report.py §4c/§4d numbers (and the Test-mode leaderboard). Aborts on drift."""
    picks, outs = load_log()
    cfg = {"min_n": 30, "min_keep_frac": 0.15, "boot_iters": 500, "seed": 7}
    asof = date(2026, 7, 5)
    reg = json.load(open("hypotheses/registry.json"))
    by_id = {h["id"]: h for h in reg["hypotheses"]}
    exp = {  # (n_post, win_post, avg_post, delta_post)
        "H-F1": (36, 42, -2.6, 0.2), "H-F2": (39, 41, -2.7, 0.1),
        "H-F3": (44, 39, -3.0, -0.2), "H-F4": (40, 35, -3.6, -0.8),
        "H-CLEAN": (29, 34, -3.7, -0.9), "H-EX1": (30, 60, -2.4, 1.7),
    }
    for hid, (n, win, avg, dl) in exp.items():
        c = evaluate(by_id[hid], picks, outs, cfg, asof)
        got = (c["n_post"], c["win_post"], c["avg_post"], c["delta_post"])
        assert got == (n, win, avg, dl), f"PARITY FAIL {hid}: got {got} want {(n, win, avg, dl)}"
    # every current hypothesis must be non-significant (0 clear the bar) — the honest state
    assert all(not evaluate(by_id[h], picks, outs, cfg, asof)["significant"] for h in exp), \
        "expected 0 significant hypotheses at current sample sizes"
    print("hypo_eval self-test: PARITY OK (6/6 match, 0 significant)", file=sys.stderr)

if __name__ == "__main__":
    import os
    _selftest()
    # The Action writes fetched Supabase rows to this file (see report.yml); absent
    # locally => house rules only. Never fatal: a bad/missing file yields no user rows.
    user_path = os.environ.get("USER_RULES_PATH", "hypotheses/user_rules.json")
    if not os.path.exists(user_path):
        user_path = None
    board = evaluate_registry(asof=date.today(), user_path=user_path)
    json.dump(board, open("leaderboard.json", "w"), indent=2, ensure_ascii=False)
    n_user = sum(1 for r in board["rows"] if str(r["id"]).startswith("U-"))
    print(f"wrote leaderboard.json — {board['summary']['n_live']} hypotheses "
          f"({n_user} user), {board['summary']['n_significant']} significant, "
          f"baseline {board['baseline']['avg_post']}% (n={board['baseline']['n_post']})")
