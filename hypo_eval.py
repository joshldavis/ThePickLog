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
import csv, json, os, random, re, statistics as st, sys
from datetime import date

# ------------------------------------------------------------------ log I/O
def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

def load_log(picks_path="picks.csv", outs_path="outcomes.csv", cohort=None):
    # COHORT SEAL (H-UNIV1, 2026-07-08): rules registered against the v0.2 fixed-16
    # record evaluate the v0.2 cohort ONLY. Batch #4 (2026-07-13) introduced
    # per-hypothesis "cohort" (e.g. "v0.3") — each rule is scored strictly against
    # its own cohort's picks; cohorts are never mixed on one card.
    # Research override: PICKLOG_COHORT=all|v0.3.
    coh = cohort or os.environ.get("PICKLOG_COHORT", "v0.2")
    keep = (lambda r: True) if coh == "all" else (
        lambda r: (r.get("model_version") or "").startswith(coh))
    picks = {r["pick_id"]: r for r in csv.DictReader(open(picks_path)) if keep(r)}
    outs = [o for o in csv.DictReader(open(outs_path)) if o.get("pick_id") in picks]
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
    fn = any if selection.get("op") == "or" else all   # match ANY vs match ALL
    return fn(_test_pred(pick, p) for p in preds)

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
        if mfe is None or c5 is None:
            return None
        parts = exit_id.split("_")            # target_T  or  target_T_stop_S
        T = float(parts[1])
        if len(parts) >= 4 and parts[2] == "stop":
            S = float(parts[3])
            mae = _f(o.get("mae_5d"))
            if mae is None:
                return None
            # Path order is unknown from MFE/MAE alone. When BOTH the +T target and
            # the -S stop are reached in the window, assume the STOP fired first —
            # conservative, so a stop rule can never over-credit itself. 2% haircut.
            if mae <= -S:
                return -(S + 2.0)             # stopped out at -S, net of cost
            if mfe >= T:
                return T - 2.0                # +T limit, net of cost
            return c5
        return (T - 2.0) if mfe >= T else c5   # plain +T target, net of cost
    raise ValueError(f"unknown exit {exit_id!r}")

_SLIP = "slippage: +T% fills assumed exact; on thin floats limits gap through, so live results run worse than this proxy"
_STOP_ORDER = "stop ordering unknown from MFE/MAE: when both the +T target and -S stop are reached, the stop is assumed to trigger first (conservative)"

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


# ---------------------------------------------------------------------------
# H-IND1 (pre-registered 2026-07-08): effective-sample-size / independence
# correction. The scan universe is a fixed ~16-ticker list and the same names
# recur daily with overlapping 5-day paths, so pooled iid resampling OVERSTATES
# precision. Every verdict must ALSO report (a) a cluster bootstrap by ticker
# and (b) a per-ticker sign count; a pooled win that fails BOTH is "not
# established," not a win. These operate on ticker-tagged observations.
# ---------------------------------------------------------------------------
def _group_by_ticker(items):
    """items: list of (ticker, value) -> {ticker: [values]}."""
    g = {}
    for t, v in items:
        g.setdefault(t, []).append(v)
    return g


def _cluster_paired_ci(paired_items, iters, rng):
    """Cluster bootstrap by ticker for the mean paired diff (exit kind).
    Resample TICKERS with replacement (not picks), pool the drawn tickers'
    diffs, take the mean. Wider than the pooled CI because effective N is the
    number of names, not the number of overlapping daily rows."""
    g = _group_by_ticker(paired_items)
    tickers = list(g)
    if len(tickers) < 2:
        return None
    out = []
    for _ in range(iters):
        sample = []
        for _ in tickers:
            sample += g[tickers[rng.randrange(len(tickers))]]
        if sample:
            out.append(_mean(sample))
    if len(out) < 2:
        return None
    out.sort()
    return [round(out[int(.025 * len(out))], 1), round(out[int(.975 * len(out))], 1)]


def _cluster_two_sample_ci(kept_items, base_items, iters, rng):
    """Cluster bootstrap by ticker for mean(kept) - mean(base) (filter/question).
    Resample the SAME ticker set for both arms so each drawn name contributes
    both its kept and its base returns."""
    kb = _group_by_ticker(kept_items)
    bb = _group_by_ticker(base_items)
    tickers = list(bb)
    if len(tickers) < 2:
        return None
    out = []
    for _ in range(iters):
        ka, ba = [], []
        for _ in tickers:
            t = tickers[rng.randrange(len(tickers))]
            ka += kb.get(t, [])
            ba += bb.get(t, [])
        if ka and ba:
            out.append(_mean(ka) - _mean(ba))
    if len(out) < 2:
        return None
    out.sort()
    return [round(out[int(.025 * len(out))], 1), round(out[int(.975 * len(out))], 1)]


def _ticker_signs_paired(paired_items):
    """Per-ticker sign of the mean paired diff. Returns (favor, against, signed)."""
    g = _group_by_ticker(paired_items)
    favor = sum(1 for v in g.values() if _mean(v) > 0)
    against = sum(1 for v in g.values() if _mean(v) < 0)
    return favor, against, len(g)


def _ticker_signs_two_sample(kept_items, base_items):
    """Per-ticker sign of mean(kept_t) - mean(base_t), over tickers that have
    BOTH kept and base observations. Returns (favor, against, signed)."""
    kb = _group_by_ticker(kept_items)
    bb = _group_by_ticker(base_items)
    favor = against = signed = 0
    for t, kv in kb.items():
        bv = bb.get(t)
        if not bv:
            continue
        signed += 1
        d = _mean(kv) - _mean(bv)
        if d > 0:
            favor += 1
        elif d < 0:
            against += 1
    return favor, against, signed


def _cluster_card(ci, favor, against, signed, pooled_sig):
    """Assemble the H-IND1 fields + the pre-registered 'established' verdict.
    established = pooled win that does NOT fail BOTH the cluster CI and the
    per-ticker majority (spec: fail both => 'not established')."""
    cluster_sig = bool(ci) and (ci[0] > 0 or ci[1] < 0)
    ticker_majority = signed > 0 and favor > against
    established = bool(pooled_sig) and (cluster_sig or ticker_majority)
    return {
        "cluster_ci95": ci,
        "cluster_significant": cluster_sig,
        "n_tickers": signed,
        "ticker_favor": favor,
        "ticker_against": against,
        "ticker_majority": ticker_majority,
        "established": established,
    }

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
        kept_items, base_items = [], []   # (ticker, return) for the cluster bootstrap
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
                tk = p.get("ticker", "")
                base_items.append((tk, r))
                if keep:
                    kept_post.append(r)
                    kept_items.append((tk, r))
        ci = _two_sample_ci(kept_post, base_post, iters, rng)
        delta = round(_mean(kept_post) - _mean(base_post), 1) if kept_post and base_post else None
        cluster = _cluster_two_sample_ci(kept_items, base_items, iters, rng)
        favor, against, signed = _ticker_signs_two_sample(kept_items, base_items)
        card = _card(rule, kept_post, base_post, delta, ci, cfg, asof, kind)
        card.update(_cluster_card(cluster, favor, against, signed, card["significant"]))
        card["kept_n_all"] = len(kept_all)
        return card

    if kind == "exit":
        pairs, base_post, arm_post = [], [], []
        paired_items = []   # (ticker, diff) for the cluster bootstrap
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
            paired_items.append((picks.get(o["pick_id"], {}).get("ticker", ""), alt - base))
        ci = _paired_ci(pairs, iters, rng)
        delta = round(_mean(pairs), 1) if pairs else None
        cluster = _cluster_paired_ci(paired_items, iters, rng)
        favor, against, signed = _ticker_signs_paired(paired_items)
        card = _card(rule, arm_post, base_post, delta, ci, cfg, asof, kind)
        card.update(_cluster_card(cluster, favor, against, signed, card["significant"]))
        card["caveats"] = [_SLIP] + ([_STOP_ORDER] if "_stop_" in rule["exit"] else [])
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
            "op": (rule.get("selection") or {}).get("op", "and"),
            "predicates": (rule.get("selection") or {}).get("predicates", []),
        },
    }

_CMP_STR = {">=": "≥", ">": ">", "<=": "≤", "<": "<", "==": "=", "!=": "≠",
            "in": "∈", "not_in": "∉"}

def exit_label(ex):
    """Human-readable exit description (plain +T target and +T/-S stop-loss)."""
    if ex == "same_day_close":
        return "same-day close"
    parts = ex.split("_")
    if parts[0] == "target":
        T = parts[1]
        base = f"mfe_5d ≥ +{T}% → +{float(T)-2:g}% net"
        if len(parts) >= 4 and parts[2] == "stop":
            S = parts[3]
            return f"{base}; else mae_5d ≤ −{S}% → −{float(S)+2:g}% net; else 5d close"
        return f"{base}, else 5d close"
    return ex

def rule_to_str(rule):
    if rule["kind"] == "exit":
        return "exit: " + exit_label(rule["exit"])
    parts = []
    for p in rule["selection"]["predicates"]:
        v = p["value"]
        v = "{" + ", ".join(map(str, v)) + "}" if isinstance(v, list) else (
            f"{v:,.0f}" if isinstance(v, (int, float)) and v >= 1000 else v)
        parts.append(f"{p['field']} {_CMP_STR[p['cmp']]} {v}")
    body = (" ∨ " if rule["selection"].get("op") == "or" else " ∧ ").join(parts)
    if rule["kind"] == "question":
        return f"ask: does keeping [{body}] help or hurt?"
    return "keep: " + body

# ------------------------------------------------------------------ user rules (Phase 1)
# Pick-time field whitelist (defence-in-depth; mirrors the SQL register RPC). A user
# rule may only select on fields KNOWN AT PICK TIME — never outcome columns — so no
# hypothesis can reference the future. Anything else is dropped, not trusted.
_USER_FIELDS = {"price_at_screen", "float_shares", "gap_pct", "rvol", "short_interest_pct", "tier"}
# same_day_close, target_T (T=1..50), or target_T_stop_S (S=1..90) — bounded so a rule
# can't smuggle absurd thresholds. Mirrors the SQL register RPC's regex.
_EXIT_RE = re.compile(r"^(same_day_close|target_([1-9]|[1-4][0-9]|50)(_stop_([1-9]|[1-8][0-9]|90))?)$")

def _exit_ok(ex):
    return bool(_EXIT_RE.match(ex or ""))

def _map_user_rule(row):
    """Map one Supabase is_hypotheses row to the evaluator's hypothesis shape, or
    None if it fails validation (malformed, disallowed field/exit, retired)."""
    try:
        if row.get("status", "active") != "active":
            return None
        kind = row["kind"]
        if kind not in ("filter", "exit", "question"):
            return None
        exit_id = row.get("exit_id", "same_day_close")
        if not _exit_ok(exit_id):
            return None
        sel = row.get("rule_json") or {"op": "and", "predicates": []}
        preds = sel.get("predicates", []) if isinstance(sel, dict) else []
        op = sel.get("op", "and") if isinstance(sel, dict) else "and"
        if op not in ("and", "or"):
            op = "and"
        for p in preds:
            if p.get("field") not in _USER_FIELDS:   # any bad field => reject whole rule
                return None
        if kind in ("filter", "question") and not preds:   # both select a subset
            return None
        return {
            "id": "U-" + str(row["id"])[:8],
            "title": (row.get("title") or "untitled").strip()[:80],
            "author": (row.get("author_name") or row.get("author")
                       or (row.get("is_profiles") or {}).get("display_name") or "anon"),
            "registered_at": str(row["registered_at"])[:10],
            "kind": kind,
            "selection": {"op": op, "predicates": preds},
            "exit": exit_id,
            # A 'question' makes no directional claim — its honesty range (CI) is the answer.
            "claim": {"metric": "expectancy",
                      "direction": "two_sided" if kind == "question" else "beats_baseline"},
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

# ------------------------------------------------------------------ stability history
# A weekly-only, append-only record of each rule's delta sign over time. Persisted so
# "does the edge's sign hold?" (Gate 1) becomes a fact anyone can read, not a vibe.
_STABILITY_MIN = 3   # weekly snapshots (incl. current) needed before judging stability

def _load_snapshots(path):
    try:
        d = json.load(open(path))
        return d if isinstance(d, list) else []
    except (FileNotFoundError, ValueError):
        return []

def _stability(rule_id, cur_delta, snaps):
    """stable = last ≥3 weekly deltas (incl. current) share one nonzero sign;
    mixed = they don't; building = fewer than 3 data points yet."""
    seq = [s.get("rules", {}).get(rule_id) for s in snaps]      # oldest→newest, past only
    seq = [d for d in seq if d is not None] + ([cur_delta] if cur_delta is not None else [])
    if len(seq) < _STABILITY_MIN:
        return "building"
    signs = [1 if d > 0 else (-1 if d < 0 else 0) for d in seq[-_STABILITY_MIN:]]
    return "stable" if all(s == signs[0] and s != 0 for s in signs) else "mixed"

def append_snapshot(rows, path, when):
    """Append one weekly snapshot of every rule's delta_post (append-only, immutable).
    Called ONLY by the weekly report (SNAPSHOT=1), never the daily rebuild."""
    snaps = _load_snapshots(path)
    if snaps and snaps[-1].get("date") == str(when):
        return                                                  # idempotent per day
    snaps.append({"date": str(when),
                  "rules": {r["id"]: r["delta_post"] for r in rows}})
    json.dump(snaps, open(path, "w"), indent=0, ensure_ascii=False)

# ------------------------------------------------------------------ registry
def evaluate_registry(registry_path="hypotheses/registry.json",
                      picks_path="picks.csv", outs_path="outcomes.csv", asof=None,
                      user_path=None, snapshots_path="hypotheses/snapshots.json"):
    reg = json.load(open(registry_path))
    cfg = reg["config"]
    picks, outs = load_log(picks_path, outs_path)
    asof = asof or date.today()
    users = load_user_hypotheses(user_path) if user_path else []
    # Per-hypothesis cohort (Batch #4, 2026-07-13): a rule carrying "cohort": "v0.3"
    # is evaluated against v0.3 picks/outcomes only; everything else stays sealed to
    # v0.2. Logs are loaded once per cohort and never mixed within a card.
    _logs = {"v0.2": (picks, outs)}
    def _log_for(h):
        coh = h.get("cohort", "v0.2")
        if coh not in _logs:
            _logs[coh] = load_log(picks_path, outs_path, cohort=coh)
        return _logs[coh]
    rows = []
    for h in (reg["hypotheses"] + users):
        hp, ho = _log_for(h)
        r = evaluate(h, hp, ho, cfg, asof)
        r["cohort"] = h.get("cohort", "v0.2")
        rows.append(r)

    # Only claimed edges (filter/exit) get a rank; a 'question' makes no directional
    # claim, so it's listed but never ranked as if higher were better.
    ranked = sorted([r for r in rows if r["state"] == "ranked" and r.get("kind") != "question"],
                    key=lambda r: (r["delta_post"] is None, -(r["delta_post"] or 0)))
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    for r in rows:
        r.setdefault("rank", None)

    # Stability: does each rule's delta sign hold across the weekly snapshots?
    # (MONETIZATION-GATE Gate 1: "sign holds across ≥3 consecutive weekly snapshots".)
    snaps = _load_snapshots(snapshots_path)
    for r in rows:
        r["stability"] = _stability(r["id"], r["delta_post"], snaps)

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
        # graded = outcomes with a REAL realized return; void rows (phantom/holiday
        # scans) carry no return and must not inflate the count. Matches the Track
        # record + Validation dashboard (both show finite-return grades only).
        "log": {"picks": len(picks),
                "graded": sum(1 for o in outs if _f(o.get("ret_open_close_net")) is not None)},
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
    """Parity gate: evaluate()'s point stats for the six house rules must match an
    INDEPENDENT recomputation done here (no shared keep/exit helpers), on whatever the
    current CSVs hold. Data-robust by construction — it recomputes the reference from
    the live log rather than pinning stale constants — so it catches logic regressions
    without falsely aborting as the sample grows or an edge eventually clears. Aborts on drift."""
    picks, outs = load_log()
    cfg = {"min_n": 30, "min_keep_frac": 0.15, "boot_iters": 200, "seed": 7}
    asof = date.today()
    by_id = {h["id"]: h for h in json.load(open("hypotheses/registry.json"))["hypotheses"]}
    REG_F, REG_EX = "2026-06-22", "2026-06-23"     # frozen house registration dates

    def _n(d, k):
        try: return float(d.get(k))
        except (TypeError, ValueError): return None
    def keeps(p):                                   # independent house-filter predicates
        pr, fl, gp = _n(p, "price_at_screen"), _n(p, "float_shares"), _n(p, "gap_pct")
        ti = (p.get("tier") or "").strip()
        K = {"H-F1": pr is None or pr >= 1.0, "H-F2": fl is None or fl < 3000000,
             "H-F3": gp is None or gp < 20, "H-F4": ti not in ("A", "B")}
        K["H-CLEAN"] = all(K[x] for x in ("H-F1", "H-F2", "H-F3", "H-F4"))
        return K
    def scc(o): return _n(o, "ret_open_close_net")
    def ex1(o):                                     # independent target_10 net return
        c5, mfe = _n(o, "ret_open_5dclose_net"), _n(o, "mfe_5d")
        if mfe is None or c5 is None or scc(o) is None: return None
        return 8.0 if mfe >= 10 else c5
    def _stats(arm, diffs, base):
        n = len(arm)
        return (n,
                round(100 * sum(1 for x in arm if x > 0) / n) if n else None,
                round(sum(arm) / n, 1) if n else None,
                (round(sum(diffs) / len(diffs), 1) if diffs else None) if diffs is not None
                else (round(sum(arm) / n - sum(base) / len(base), 1) if n and base else None))
    def ref_filter(hid):
        kept, base = [], []
        for o in outs:
            p = picks.get(o["pick_id"]); r = scc(o)
            if not p or r is None or not (p.get("trading_date", "") > REG_F): continue
            base.append(r)
            if keeps(p)[hid]: kept.append(r)
        return _stats(kept, None, base)
    def ref_ex1():
        arm, diffs = [], []
        for o in outs:
            p = picks.get(o["pick_id"])
            if not p or not (p.get("trading_date", "") > REG_EX): continue
            a, b = ex1(o), scc(o)
            if a is None or b is None: continue
            arm.append(a); diffs.append(a - b)
        return _stats(arm, diffs, None)

    for hid in ("H-F1", "H-F2", "H-F3", "H-F4", "H-CLEAN"):
        c = evaluate(by_id[hid], picks, outs, cfg, asof)
        got, want = (c["n_post"], c["win_post"], c["avg_post"], c["delta_post"]), ref_filter(hid)
        assert got == want, f"PARITY FAIL {hid}: evaluate {got} vs independent ref {want}"
    c = evaluate(by_id["H-EX1"], picks, outs, cfg, asof)
    got, want = (c["n_post"], c["win_post"], c["avg_post"], c["delta_post"]), ref_ex1()
    assert got == want, f"PARITY FAIL H-EX1: evaluate {got} vs independent ref {want}"
    c2 = evaluate(by_id["H-EX1"], picks, outs, cfg, asof)   # determinism
    assert (c2["n_post"], c2["avg_post"], c2["delta_post"]) == (c["n_post"], c["avg_post"], c["delta_post"]), \
        "non-deterministic evaluate()"

    # ---- H-IND1 cluster bootstrap unit tests (independent of live data) ----
    rng = random.Random(7)
    # (a) One dominant ticker drives a "positive" pooled result: 30 rows of +5 all
    #     from ticker AAA, 2 tickers slightly negative. Pooled mean is +; the per-ticker
    #     sign count must show the majority of NAMES do NOT favor the arm.
    dom = [("AAA", 5.0)] * 30 + [("BBB", -1.0), ("CCC", -1.0)]
    fav, ag, sg = _ticker_signs_paired(dom)
    assert (fav, ag, sg) == (1, 2, 3), (fav, ag, sg)          # 1 name favors, 2 against
    cl = _cluster_paired_ci(dom, 400, rng)
    assert cl is not None and cl[0] <= 0 <= cl[1], cl          # cluster CI spans 0 (not established)
    # (b) Broad, consistent effect across many names: cluster CI should exclude 0.
    broad = [(f"T{i}", 3.0) for i in range(16)] + [(f"T{i}", 4.0) for i in range(16)]
    cb = _cluster_paired_ci(broad, 400, rng)
    assert cb is not None and cb[0] > 0, cb
    fb, ab, sb = _ticker_signs_paired(broad)
    assert (fb, ab, sb) == (16, 0, 16), (fb, ab, sb)
    # (c) verdict assembly: pooled win that fails BOTH cluster + majority => not established
    v = _cluster_card([-0.5, 2.0], favor=1, against=2, signed=3, pooled_sig=True)
    assert v["established"] is False and v["cluster_significant"] is False, v
    v2 = _cluster_card([0.3, 2.0], favor=10, against=2, signed=12, pooled_sig=True)
    assert v2["established"] is True and v2["ticker_majority"] is True, v2
    # (d) determinism of the cluster CI under a fixed seed
    assert _cluster_paired_ci(dom, 400, random.Random(7)) == _cluster_paired_ci(dom, 400, random.Random(7))
    # (e) evaluate() now emits the H-IND1 fields on the live H-EX1 card
    for k in ("cluster_ci95", "cluster_significant", "n_tickers", "ticker_favor",
              "ticker_against", "ticker_majority", "established"):
        assert k in c, f"evaluate() missing H-IND1 field {k}"
    assert c["n_tickers"] >= 1

    print(f"hypo_eval self-test: PARITY OK (6/6 vs independent reference, {len(outs)} outcomes) "
          f"+ H-IND1 cluster bootstrap OK", file=sys.stderr)

if __name__ == "__main__":
    import os
    _selftest()
    # The Action writes fetched Supabase rows to this file (see report.yml); absent
    # locally => house rules only. Never fatal: a bad/missing file yields no user rows.
    user_path = os.environ.get("USER_RULES_PATH", "hypotheses/user_rules.json")
    if not os.path.exists(user_path):
        user_path = None
    asof = date.today()
    board = evaluate_registry(asof=asof, user_path=user_path)
    json.dump(board, open("leaderboard.json", "w"), indent=2, ensure_ascii=False)
    # Append a stability snapshot ONLY on the weekly report run (SNAPSHOT=1), so the
    # history stays weekly (daily rebuilds recompute stability but don't add points).
    if os.environ.get("SNAPSHOT") == "1":
        append_snapshot(board["rows"], "hypotheses/snapshots.json", asof)
        print("appended weekly stability snapshot", file=sys.stderr)
    n_user = sum(1 for r in board["rows"] if str(r["id"]).startswith("U-"))
    print(f"wrote leaderboard.json — {board['summary']['n_live']} hypotheses "
          f"({n_user} user), {board['summary']['n_significant']} significant, "
          f"baseline {board['baseline']['avg_post']}% (n={board['baseline']['n_post']})")
