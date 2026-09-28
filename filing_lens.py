#!/usr/bin/env python3
"""
filing_lens.py — text-level reading of a screened ticker's recent SEC filings via Jev
(TypeSafe AI's System One decision model). GATE 1: offline core only.

WHAT THIS ADDS (and what edgar_lens.py already does)
----------------------------------------------------
edgar_lens.classify_filings() classifies filings by FORM CODE and date only
(424B* -> "offering", S-3* -> "shelf", 8-K -> "8K"). It never opens the document,
so an 8-K that says "1-for-20 reverse split effective Monday" is indistinguishable
from one announcing a new CFO. This module reads the document text and asks a
FIXED set of six schema-bound questions:

    reverse_split, split_ratio, listing_status, dilution_event,
    going_concern, other_material

Jev returns a typed answer per question with a calibrated probability. It cannot
write free text, so nothing it emits can put an unverifiable sentence on the site.

PURPOSE: data integrity first (reverse-split guard, halt/delisting second-reason
on stale-quote echoes), risk-gating second (text-confirmed dilution for a future
H-DIL3). NOT a selection signal — nothing here changes which tickers are picked.

DESIGN RULES (same discipline as edgar_lens / quote_integrity)
  • FORWARD-ONLY, NON-FATAL, VERIFIABLE (see the spec doc for the logging fields).
  • PINNED MODEL: the live caller refuses to run unless JEV_MODEL is set to an exact
    version. A response carrying any other version is DISCARDED as version drift.
  • ITEM-CODE PREFILTER FIRST: the free SEC submissions block already lists each
    8-K's items. Only 8-Ks carrying 1.01 / 3.01 / 3.02 / 3.03 / 5.03 / 8.01 within
    EIGHTK_WINDOW, plus priced-offering / shelf forms within OFFERING_WINDOW, are
    read at all. Everything else is never sent anywhere.
  • THE CLASSIFIER NEVER ACTS ALONE: route() returns auto / review / ignore. "auto"
    means "hand this to an existing, independently verifiable check" — it does not
    void a row or change a count by itself.
  • THRESHOLDS live in one place (THRESHOLDS) and are versioned with the questions
    (QUESTIONS_SHA256) and the model. Each calibrated entry cites its run; the rest
    are still placeholders, and shadow mode (gate 3) only logs their routing.

GATES
  1. (this file) pure core + --selftest, no network, no key.
  2. calibration run on ~400 hand-labeled filings; thresholds set from the curve.
  3. shadow mode: wired into edgar_lens.snapshot(), logs only, no routing action.
  4. live.

USAGE
  python3 filing_lens.py --selftest              # offline logic test (no network)
  python3 filing_lens.py --ticker JAGX --dry-run # SEC only: which filings WOULD be read
  python3 filing_lens.py --shadow                # gate 3: read today's logged picks, log only
NOT INVESTMENT ADVICE.
"""
import argparse
import hashlib
import html as _html
import json
import os
import re
import sys
import time
from datetime import date, datetime, timezone
from html.parser import HTMLParser

__version__ = "0.2.0-gate2"

# ---------------------------------------------------------------------------
# Tunables (explicit, auditable)
# ---------------------------------------------------------------------------
EIGHTK_WINDOW    = 30    # days: an 8-K older than this cannot be "the reason the quote froze this week"
OFFERING_WINDOW  = 180   # days: matches edgar_lens.OFFERING_WINDOW — active dilution pressure
PREFILTER_ITEMS  = ("1.01", "3.01", "3.02", "3.03", "5.03", "8.01")   # 8-K items worth reading
# 3.03 added 2026-09-28: the split-v2 test population was 8-Ks with 5.03 OR 3.03, and a
# split can be reported under 3.03 alone; without it those filings were never read.
# Jev's 32k budget is the STATE PLUS THE LONGEST QUESTION (docs.typesafe.ai/models,
# 2026-09-23), not the text alone. The longest question here is split_ratio at ~1.5k
# tokens; the state wrapper adds a few hundred. So the filing text gets 30k.
MAX_TOKENS       = 30_000          # text budget inside Jev's 32k state+longest-question limit
CHARS_PER_TOKEN  = 3.2             # conservative: SEC tables/numbers tokenize denser than prose
MAX_CHARS        = int(MAX_TOKENS * CHARS_PER_TOKEN)   # 96,000 characters
MAX_FILINGS_PER_TICKER = 6         # politeness cap on SEC document fetches per scan

# The model version is PINNED by the environment at gate 2; never "jev-latest".
JEV_MODEL    = os.environ.get("JEV_MODEL", "")
JEV_ENDPOINT = os.environ.get("JEV_ENDPOINT", "https://api.typesafe.ai/v1/systemone")  # docs.typesafe.ai/api
JEV_API_KEY  = os.environ.get("JEV_API_KEY", "")


def _is_offering(form):   # priced offering / prospectus supplement (mirror edgar_lens)
    return form.startswith("424B") or form in ("FWP",)
def _is_shelf(form):
    return form.startswith(("S-3", "S-1", "F-3", "F-1"))
def _is_8k(form):
    return form.startswith("8-K")


def _d(s):
    if isinstance(s, date):
        return s
    return date(int(s[0:4]), int(s[5:7]), int(s[8:10]))


# ---------------------------------------------------------------------------
# QUESTIONS — the fixed, schema-bound question block. Criteria describe
# SITUATIONS (what the document says happened), not degrees. Any edit here
# changes QUESTIONS_SHA256, which invalidates the calibration result.
# ---------------------------------------------------------------------------
# Every integer ratio 1-for-2 .. 1-for-250 (249 + none + other = 251 <= Jev's 255-choice cap).
# The first calibration pull found 15 of 40 real splits at ratios a short list would have
# thrown into "other" (1-for-6, 1-for-12, 1-for-35, ...), so the list is exhaustive.
SPLIT_RATIOS = [f"1-for-{n}" for n in range(2, 251)]

QUESTIONS = {
    "reverse_split": {
        "type": "choice",
        "instructions": "Does this filing report a reverse stock split of the registrant's common stock as one of its events, and if so has it taken effect?",
        "criteria": {
            "none": "No reverse split is mentioned, or only a forward split, or shareholders authorized a range of ratios and the board has not chosen one",
            "announced": "The board has fixed a specific ratio and the filing says the split will become effective on a stated future date or on a date not yet set",
            "effective": "The filing reports, as one of its own events or recent developments, that the reverse split has become effective or became effective on a stated date",
            "historical": "A reverse split completed in the past is mentioned only as background, for example to explain that share counts or prices have been retroactively adjusted",
        },
    },
    "split_ratio": {
        "type": "choice",
        "instructions": "If the filing states a specific reverse split ratio (announced, effective, or historical), which one? The ratio may be written as '1-for-15', 'one-for-fifteen', or 'every fifteen (15) shares reclassified into one (1) share'. A range approved by shareholders with no ratio chosen is 'none'.",
        "criteria": {"none": "No specific ratio stated", **{r: "" for r in SPLIT_RATIOS},
                     "other": "A specific ratio not listed here"},
    },
    "listing_status": {
        "type": "choice",
        "instructions": "What does this filing say about the registrant's exchange listing? If trading was halted or suspended, choose halt even when a delisting determination is also described; a halt that has already been lifted with compliance restored is regained_compliance.",
        "criteria": {
            "none": "Listing is not discussed, or only a voluntary transfer between exchanges or tiers",
            "deficiency_notice": "The exchange notified the company it is out of compliance (bid price, equity, filing delinquency) and a cure period is running",
            "delisting_determination": "The exchange has determined to delist, or the company will be moved to OTC, or an appeal was denied",
            "halt": "Trading in the stock has been halted or suspended by the exchange or the SEC",
            "regained_compliance": "The company states it has regained compliance with a listing rule",
        },
    },
    "dilution_event": {
        "type": "choice",
        "instructions": "Does this filing describe a transaction that issues or will issue new common shares or equivalents?",
        "criteria": {
            "none": "No new share issuance described",
            "priced_offering": "A registered public offering or prospectus supplement with a stated price per share and share count",
            "private_placement": "A securities purchase agreement, PIPE, or unregistered sale to named investors",
            "atm_or_equity_line": "An at-the-market program, equity line, or standby purchase agreement",
            "convertible_or_warrants": "Convertible notes, preferred, or warrant issuance or exercise",
        },
    },
    "going_concern": {
        "type": "noul",
        "instructions": "Does the filing state that there is substantial doubt about the company's ability to continue as a going concern?",
    },
    "other_material": {
        "type": "choice",
        "instructions": "What is the single most important other event in this filing?",
        "criteria": {
            "none": "Routine or none of the below",
            "auditor_change": "Change in or resignation of the independent auditor",
            "officer_departure": "CEO or CFO resigned or was terminated",
            "bankruptcy": "Chapter 11 or 7 filing, receivership, or assignment for benefit of creditors",
            "restatement": "Prior financial statements should no longer be relied upon",
            "merger_or_acquisition": "Definitive agreement to be acquired, merge, or acquire another company",
        },
    },
}
QUESTION_ORDER = list(QUESTIONS.keys())


def _sha(s):
    return hashlib.sha256(s.encode("utf-8") if isinstance(s, str) else s).hexdigest()


def _qsha(qs):
    return _sha(json.dumps(qs, sort_keys=True, separators=(",", ":")))


# ---- question versions ------------------------------------------------------
# v1 = the block used by calibration runs 1 (2026-09-23) and 2 (2026-09-25); kept
# verbatim so those results re-score exactly from cache.
# v2 (registered 2026-09-28, REGISTRATION-split-v2.md) changes ONLY reverse_split: run 2
# showed its misses were filings that recite an already-completed split; v1's question
# never said that counts as "historical". Every other question is byte-identical.
import copy as _copy
QUESTIONS_V1 = _copy.deepcopy(QUESTIONS)
QUESTIONS_V2 = _copy.deepcopy(QUESTIONS)
QUESTIONS_V2["reverse_split"] = {
    "type": "choice",
    "instructions": ("Is a reverse stock split of the registrant's common stock one of the events THIS filing reports, "
                     "and if so, does it take effect before or after the filing date? A split that the filing mentions "
                     "as already completed and reported earlier (for example 'as previously disclosed', a recap of recent "
                     "developments, or an explanation of adjusted share counts) is historical, not effective."),
    "criteria": {
        "none": "No reverse split is mentioned; or only a forward split; or shareholders approved a range of ratios and no specific ratio has been fixed",
        "announced": "This filing reports that a specific ratio has been fixed and the split takes effect after the filing date, or on a date not yet set",
        "effective": "This filing reports the split as its own event, and the split took effect on or before the filing date, including earlier the same day",
        "historical": "The filing mentions a reverse split that was completed and reported before this filing, as background or a recap",
    },
}
QUESTIONS_BY_VERSION = {"v1": QUESTIONS_V1, "v2": QUESTIONS_V2}
QUESTIONS_VERSION = os.environ.get("FILING_LENS_QUESTIONS", "v2")
QUESTIONS = QUESTIONS_BY_VERSION[QUESTIONS_VERSION]
QUESTIONS_SHA256 = _qsha(QUESTIONS)

# ---------------------------------------------------------------------------
# THRESHOLDS. (question, value) -> (auto_floor, review_floor).
#   CALIBRATED (cited below): reverse_split/effective, listing_status/halt,
#   listing_status/delisting_determination. Everything else is still a PLACEHOLDER.
# A value not listed routes "ignore" whatever its probability ("none" answers,
# regained_compliance, etc.). always_review overrides the band.
# ---------------------------------------------------------------------------
THRESHOLDS = {
    # split-v2 test, REGISTRATION-split-v2.md, labels frozen 945e3ad before any call:
    # 24/24 precision at 0.90 on 196 held-out 2024 8-Ks (30 labeled effective), 0 of 30
    # re-asks changed. Auto ONLY for 8-Ks carrying Item 5.03/3.03 (SPLIT_AUTO_ITEMS),
    # review below 0.90 (run 2 measured up to 0.10 of run-to-run drift; the registered
    # [0.80, 0.90) band is inside [0.60, 0.90), and 2 of the 6 true effectives it
    # missed sat at 0.60 and 0.79, so a higher review floor would drop real splits).
    ("reverse_split", "effective"):             (0.90, 0.60),
    ("reverse_split", "announced"):             (0.90, 0.60),
    # calibration run 2 (2026-09-25, 543 filings, calibration/run_jev-1.13.0_2026-09-25/
    # result.json): halt 20/21 = 0.952 at 0.90 (0.95 reached from 0.79 up);
    # delisting 10/10 at 0.90 (from 0.56 up). Auto floor kept at 0.90, above both
    # measured floors by the 0.10 drift margin; below it everything is review.
    ("listing_status", "halt"):                 (0.90, 0.60),
    ("listing_status", "delisting_determination"): (0.90, 0.60),
    # PLACEHOLDER. Run 2 measured 0.911 precision at 0.85 (0.95 only from 0.94 up).
    ("listing_status", "deficiency_notice"):    (0.85, 0.60),
    ("dilution_event", "priced_offering"):      (0.85, 0.60),
    ("dilution_event", "private_placement"):    (0.85, 0.60),
    ("dilution_event", "atm_or_equity_line"):   (0.85, 0.60),
    ("dilution_event", "convertible_or_warrants"): (0.85, 0.60),
    ("going_concern", "yes"):                   (0.85, 0.60),
    ("other_material", "bankruptcy"):           (0.90, 0.60),   # + always_review below
    ("other_material", "restatement"):          (0.85, 0.60),
    ("other_material", "auditor_change"):       (0.85, 0.60),
}
ALWAYS_REVIEW = {("other_material", "bankruptcy")}
# reverse_split FAILED its registered bar in calibration run 2 (v1 question: effective
# precision 0.833 at 0.90 vs 0.95). The v2 question PASSED its pre-registered test, so
# "effective" may route auto, but only under the v2 question block and only for 8-Ks
# with Item 5.03/3.03 (the population it was tested on). Every other split answer,
# including "announced", can at most put a filing in the review queue.
NO_AUTO = {"reverse_split"}
SPLIT_AUTO_ITEMS = {"5.03", "3.03"}
SPLIT_AUTO_QUESTIONS = {"v2"}


def _split_auto_ok(value, filing):
    if value != "effective" or not filing or QUESTIONS_VERSION not in SPLIT_AUTO_QUESTIONS:
        return False
    form = str(filing.get("form", ""))
    return form in ("8-K", "8-K/A") and bool(set(_items_of(filing.get("items", ""))) & SPLIT_AUTO_ITEMS)
THRESHOLDS_VERSION = os.environ.get("FILING_LENS_SHA", "")   # git short SHA, set by the Action


def route(question, value, p, truncated=False, filing=None):
    """auto / review / ignore for one answer. Pure. `filing` (form, items) is needed
    only for the scoped reverse_split auto route; without it splits never auto."""
    key = (question, value)
    if truncated and value not in ("none", "no"):
        return "review"                                  # partial text, never auto
    if question == "split_ratio":
        return "review" if value == "other" else "ignore"   # the ratio rides with reverse_split
    if key in ALWAYS_REVIEW:
        return "review"
    if key not in THRESHOLDS:
        return "ignore"
    auto_floor, review_floor = THRESHOLDS[key]
    try:
        p = float(p)
    except (TypeError, ValueError):
        return "review"
    if p >= auto_floor:
        if question in NO_AUTO and not (question == "reverse_split" and _split_auto_ok(value, filing)):
            return "review"
        return "auto"
    if p >= review_floor:
        return "review"
    return "ignore"


# ---------------------------------------------------------------------------
# PREFILTER — which filings get read at all. Pure. Input is the SEC submissions
# "recent" block (parallel arrays) exactly as edgar_lens.submissions_recent()
# returns it.
# ---------------------------------------------------------------------------
def _items_of(s):
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def select_filings(recent, asof, eightk_window=EIGHTK_WINDOW,
                   offering_window=OFFERING_WINDOW, cap=MAX_FILINGS_PER_TICKER):
    """-> list of {form, filingDate, items, accession, primaryDocument, reason}, newest first.
    Skips anything filed after asof (not knowable at screen time)."""
    asof = _d(asof)
    forms = recent.get("form") or []
    dates = recent.get("filingDate") or []
    items = recent.get("items") or [""] * len(forms)
    accs  = recent.get("accessionNumber") or [""] * len(forms)
    docs  = recent.get("primaryDocument") or [""] * len(forms)
    out = []
    for form, fds, its, acc, doc in zip(forms, dates, items, accs, docs):
        form = (form or "").strip()
        if not form or len(fds or "") < 10:
            continue
        try:
            fd = _d(fds)
        except Exception:
            continue
        age = (asof - fd).days
        if age < 0:
            continue
        reason = ""
        if _is_8k(form) and age <= eightk_window:
            hit = [i for i in _items_of(its) if i in PREFILTER_ITEMS]
            if hit:
                reason = "8k_items:" + "+".join(hit)
        elif (_is_offering(form) or _is_shelf(form)) and age <= offering_window:
            reason = "offering" if _is_offering(form) else "shelf"
        if not reason:
            continue
        if not doc:
            reason += ";no_primary_doc"       # recorded, but cannot be read
        out.append({"form": form, "filingDate": fd.isoformat(), "items": its or "",
                    "accession": acc or "", "primaryDocument": doc or "", "reason": reason})
    out.sort(key=lambda r: r["filingDate"], reverse=True)
    return out[:cap]


def doc_url(cik, accession, primary_document):
    cik_int = str(int(str(cik)))
    return (f"https://www.sec.gov/Archives/edgar/data/{cik_int}/"
            f"{accession.replace('-', '')}/{primary_document}")


# ---------------------------------------------------------------------------
# TEXT — HTML/iXBRL -> plain text, capped to Jev's single-question limit. Pure.
# ---------------------------------------------------------------------------
class _Stripper(HTMLParser):
    _SKIP = {"script", "style", "head", "title", "ix:header"}
    _BLOCK = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "td", "th"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in self._SKIP:
            self._skip += 1
        elif t in self._BLOCK:
            self.parts.append("\n" if t != "td" and t != "th" else " ")

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in self._SKIP and self._skip:
            self._skip -= 1
        elif t in self._BLOCK:
            self.parts.append("\n" if t != "td" and t != "th" else " ")

    def handle_data(self, data):
        if not self._skip:
            # source-formatting newlines inside a tag are not paragraph breaks; block tags are
            self.parts.append(re.sub(r"\s+", " ", data))


def strip_html(raw):
    """HTML or iXBRL -> whitespace-normalized text. Plain text passes through."""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    if "<" not in raw:
        text = raw
    else:
        p = _Stripper()
        try:
            p.feed(raw)
            p.close()
        except Exception:
            text = re.sub(r"<[^>]+>", " ", raw)
        else:
            text = "".join(p.parts)
    text = _html.unescape(text).replace("\xa0", " ")
    text = text.translate(str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'}))
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def cap_text(text, max_chars=MAX_CHARS):
    """-> (text, truncated). Over the cap: skip the cover page (start after the first
    'TABLE OF CONTENTS' if it appears early), then keep the first max_chars."""
    if len(text) <= max_chars:
        return text, False
    m = re.search(r"TABLE OF CONTENTS", text[: max_chars // 4], re.I)
    if m:
        text = text[m.end():].lstrip()
    return text[:max_chars], True


def est_tokens(text):
    import math
    return math.ceil(len(text) / CHARS_PER_TOKEN)


# ---------------------------------------------------------------------------
# REQUEST / RESPONSE — pure builders and parsers around the Jev call shape
#   request:  {"model", "state": {...}, "questions": {...}}
#   response: {"model", "answers": {q: {"choice"|"noul", "probabilities", "confidence"}}, "usage"}
# ---------------------------------------------------------------------------
def build_request(filing, text, model=None, questions=None):
    model = model or JEV_MODEL
    return {
        "model": model,
        "state": {
            "form": filing.get("form", ""),
            "items": filing.get("items", ""),
            "filing_date": filing.get("filingDate", ""),
            "text": text,
        },
        "questions": questions if questions is not None else QUESTIONS,
    }


class VersionDrift(Exception):
    pass


def parse_answers(resp, expected_model=None):
    """Normalize a Jev response -> {q: {"value", "p", "confidence", "probabilities"}}.
    Raises VersionDrift if the response model differs from expected_model."""
    got = str(resp.get("model") or "")
    if expected_model and got != expected_model:
        raise VersionDrift(f"expected {expected_model}, got {got}")
    answers = resp.get("answers") or {}
    out = {}
    for q in QUESTION_ORDER:
        a = answers.get(q) or {}
        spec = QUESTIONS[q]
        if spec["type"] == "noul":
            try:
                n = float(a.get("noul"))
            except (TypeError, ValueError):
                out[q] = {"value": "", "p": "", "confidence": "", "probabilities": {}}
                continue
            yes = n >= 0.5
            out[q] = {"value": "yes" if yes else "no", "p": round(n if yes else 1.0 - n, 4),
                      "confidence": a.get("confidence", ""), "probabilities": {"yes": n, "no": 1.0 - n}}
        else:
            choice = a.get("choice", "")
            probs = a.get("probabilities") or {}
            if choice not in spec["criteria"]:
                choice = ""                      # never accept a value outside the schema
            p = probs.get(choice, "") if choice else ""
            out[q] = {"value": choice, "p": (round(float(p), 4) if p != "" else ""),
                      "confidence": a.get("confidence", ""), "probabilities": probs}
    return out


def route_all(answers, truncated=False, filing=None):
    return {q: route(q, a["value"], a["p"], truncated, filing) for q, a in answers.items()}


# ---------------------------------------------------------------------------
# SIDECAR SUMMARY — per-ticker columns for edgar_snapshot.csv (gate 3 wiring).
# One ticker may have several read filings; per question we keep the non-"none"
# answer with the highest probability (ties -> newest filing) and record where it
# came from. The jsonl log keeps everything; this is only the summary.
# ---------------------------------------------------------------------------
FL_FIELDS = []
for _q in QUESTION_ORDER:
    FL_FIELDS += [f"fl_{_q}", f"fl_{_q}_p", f"fl_{_q}_route"]
FL_FIELDS += ["fl_source_accession", "fl_filings_read", "fl_truncated", "fl_model", "fl_note"]
FL_BLANK = {k: "" for k in FL_FIELDS}


def aggregate(results):
    """results: list of per-filing dicts {filing, answers, routing, truncated}."""
    out = dict(FL_BLANK)
    if not results:
        return out
    out["fl_filings_read"] = len(results)
    out["fl_truncated"] = int(any(r.get("truncated") for r in results))
    out["fl_model"] = results[0].get("model", "")
    src = set()
    ordered = sorted(results, key=lambda r: r["filing"].get("filingDate", ""), reverse=True)
    for q in QUESTION_ORDER:
        best = None
        for r in ordered:
            a = r["answers"].get(q) or {}
            v = a.get("value", "")
            if v in ("", "none", "no"):
                continue
            pv = a.get("p") or 0.0
            if best is None or pv > best[0]:
                best = (pv, v, r["routing"].get(q, "ignore"), r["filing"].get("accession", ""))
        if best:
            out[f"fl_{q}"], out[f"fl_{q}_p"], out[f"fl_{q}_route"] = best[1], best[0], best[2]
            src.add(best[3])
        else:
            # every filing said none/no: report the newest filing's "none" with its p
            a = ordered[0]["answers"].get(q) or {}
            out[f"fl_{q}"] = a.get("value", "")
            out[f"fl_{q}_p"] = a.get("p", "")
            out[f"fl_{q}_route"] = "ignore"
    out["fl_source_accession"] = ";".join(sorted(src))
    return out


# ---------------------------------------------------------------------------
# LOG RECORD — one jsonl line per Jev call. Everything a stranger needs to
# re-run the same document through the same model and get the same answer.
# ---------------------------------------------------------------------------
def log_record(pick_id, ticker, cik, filing, text, request, response, answers, routing,
               truncated, latency_ms=None):
    return {
        "pick_id": pick_id, "ticker": ticker, "cik": cik,
        "accession": filing.get("accession", ""), "form": filing.get("form", ""),
        "items": filing.get("items", ""), "filing_date": filing.get("filingDate", ""),
        "doc_url": doc_url(cik, filing["accession"], filing["primaryDocument"])
                   if cik and filing.get("accession") and filing.get("primaryDocument") else "",
        "prefilter_reason": filing.get("reason", ""),
        "text_sha256": _sha(text), "text_tokens": est_tokens(text), "truncated": int(bool(truncated)),
        "model": str(response.get("model", "")),
        "questions_sha256": QUESTIONS_SHA256,
        "thresholds_version": THRESHOLDS_VERSION,
        "lens_version": __version__,
        "answers": response.get("answers") or {},      # raw, nothing summarized away
        "routing": routing,
        "latency_ms": latency_ms,
        "input_tokens": (response.get("usage") or {}).get("input_tokens"),
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "human_label": None, "labeled_at": None,
    }


# ---------------------------------------------------------------------------
# CLASSIFY ONE FILING — pure given an injectable `call(request) -> response`.
# ---------------------------------------------------------------------------
def classify_filing(filing, raw_doc, call, model=None, pick_id="", ticker="", cik=""):
    model = model or JEV_MODEL
    text, truncated = cap_text(strip_html(raw_doc))
    request = build_request(filing, text, model)
    t0 = time.time()
    response = call(request)
    latency = int((time.time() - t0) * 1000)
    answers = parse_answers(response, expected_model=model)     # raises VersionDrift
    routing = route_all(answers, truncated, filing)
    rec = log_record(pick_id, ticker, cik, filing, text, request, response, answers, routing,
                     truncated, latency)
    return {"filing": filing, "text": text, "truncated": truncated, "model": model,
            "request": request, "response": response, "answers": answers,
            "routing": routing, "record": rec}


# ---------------------------------------------------------------------------
# NETWORK (gate 3) — SEC document fetch via the audited helper, and the Jev call.
# Not exercised by --selftest. Fully non-fatal at the snapshot() level.
# ---------------------------------------------------------------------------
class ConfigError(Exception):
    pass


def fetch_doc(url, _retries=2):
    import urllib.request, gzip
    from asof_grader import UA
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    last = None
    for attempt in range(_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                if raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return raw
        except Exception as e:
            last = e
            if attempt < _retries:
                time.sleep(1.5 * (attempt + 1))
    raise last


def call_jev(request):
    """POST the request to JEV_ENDPOINT. Refuses to run unpinned."""
    import urllib.request
    if not JEV_MODEL or JEV_MODEL.endswith("latest"):
        raise ConfigError("JEV_MODEL must be an exact pinned version (never 'latest')")
    if not JEV_ENDPOINT or not JEV_API_KEY:
        raise ConfigError("JEV_ENDPOINT and JEV_API_KEY are required")
    body = json.dumps(request).encode("utf-8")
    req = urllib.request.Request(JEV_ENDPOINT, data=body, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {JEV_API_KEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def snapshot(ticker, cik, recent, asof, pick_id="", call=call_jev, fetch=fetch_doc,
             log_path="filing_events.jsonl", dry_run=False):
    """Per-ticker orchestration for edgar_lens.snapshot() (gate 3). NON-FATAL: any
    failure degrades to blanks with a note. dry_run: select + fetch nothing, call nothing."""
    out = dict(FL_BLANK)
    notes = []
    try:
        selected = select_filings(recent, asof)
    except Exception as e:
        out["fl_note"] = f"select_err:{type(e).__name__}"
        return out
    if dry_run:
        out["fl_filings_read"] = len(selected)
        out["fl_note"] = "dry_run:" + ",".join(f"{f['form']}@{f['filingDate']}({f['reason']})" for f in selected)
        return out
    results = []
    for f in selected:
        if not f.get("primaryDocument"):
            notes.append(f"no_doc:{f['accession']}")
            continue
        try:
            raw = fetch(doc_url(cik, f["accession"], f["primaryDocument"]))
            time.sleep(0.15)                                   # SEC fair-use pacing
        except Exception as e:
            notes.append(f"doc_err:{type(e).__name__}")
            continue
        try:
            r = classify_filing(f, raw, call, pick_id=pick_id, ticker=ticker, cik=cik)
        except VersionDrift as e:
            notes.append("jev_version_drift")
            continue
        except ConfigError as e:
            notes.append("jev_unconfigured")
            break
        except Exception as e:
            notes.append(f"jev_err:{type(e).__name__}")
            continue
        results.append(r)
        try:
            with open(log_path, "a") as fh:
                fh.write(json.dumps(r["record"], sort_keys=True) + "\n")
        except Exception as e:
            notes.append(f"log_err:{type(e).__name__}")
    out.update(aggregate(results))
    out["fl_note"] = ";".join(notes)
    return out


# ---------------------------------------------------------------------------
# SELFTEST — three canned filings through a FAKE Jev. The fake is a plumbing
# stand-in (it pattern-matches the text), NOT a model; it proves the prefilter,
# the stripper, the cap, the parser, the routing, the aggregation and the log
# record — the parts a calibration run then sits on top of.
# ---------------------------------------------------------------------------
_CANNED = {
    "split": """<html><head><title>8-K</title><style>p{}</style></head><body>
      <ix:header>hidden xbrl junk</ix:header>
      <p><b>Item 5.03 Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year.</b></p>
      <p>On September 15, 2026, Example Therapeutics, Inc. filed a Certificate of Amendment to effect a
      1-for-20 reverse stock split of its common stock. The reverse stock split became effective at
      12:01 a.m. Eastern Time on September 17, 2026, and the common stock began trading on a
      split-adjusted basis on The Nasdaq Capital Market at the open on that date.</p>
      <p>Item 9.01 Financial Statements and Exhibits.</p></body></html>""",
    "deficiency": """<html><body><div>Item 3.01 Notice of Delisting or Failure to Satisfy a Continued Listing
      Rule or Standard.</div><div>On September 18, 2026, the Company received a written notice from the
      Listing Qualifications Department of The Nasdaq Stock Market LLC indicating that the bid price of
      the Company&#8217;s common stock had closed below $1.00 for 30 consecutive business days and that
      the Company is not in compliance with Nasdaq Listing Rule 5550(a)(2). The Company has a compliance
      period of 180 calendar days to regain compliance.</div></body></html>""",
    "routine": """<html><body><p>Item 5.02 Departure of Directors or Certain Officers.</p>
      <p>On September 10, 2026, the Board appointed Jane Doe as Vice President of Marketing. There are
      no arrangements or understandings between Ms. Doe and any other person.</p></body></html>""",
}


def _fake_jev(request):
    """Deterministic pattern-matcher standing in for Jev. Returns the real response shape."""
    t = request["state"]["text"].lower()
    def choice(v, p, opts):
        rest = (1.0 - p) / max(1, len(opts) - 1)
        return {"choice": v, "probabilities": {o: (p if o == v else round(rest, 4)) for o in opts},
                "confidence": p}
    opts = {q: list(QUESTIONS[q]["criteria"]) for q in QUESTION_ORDER if QUESTIONS[q]["type"] == "choice"}
    a = {}
    if "reverse stock split" in t and "became effective" in t:
        a["reverse_split"] = choice("effective", 0.94, opts["reverse_split"])
        m = re.search(r"1-for-(\d+)", t)
        r = f"1-for-{m.group(1)}" if m else "other"
        a["split_ratio"] = choice(r if r in SPLIT_RATIOS else "other", 0.97, opts["split_ratio"])
    else:
        a["reverse_split"] = choice("none", 0.98, opts["reverse_split"])
        a["split_ratio"] = choice("none", 0.99, opts["split_ratio"])
    if "not in compliance" in t and "compliance period" in t:
        a["listing_status"] = choice("deficiency_notice", 0.91, opts["listing_status"])
    else:
        a["listing_status"] = choice("none", 0.97, opts["listing_status"])
    a["dilution_event"] = choice("none", 0.96, opts["dilution_event"])
    a["going_concern"] = {"noul": 0.03}
    a["other_material"] = choice("none", 0.95, opts["other_material"])
    return {"model": request["model"], "answers": a,
            "usage": {"input_tokens": est_tokens(request["state"]["text"]), "output_tokens": 0}}


def _selftest():
    asof = "2026-09-22"
    MODEL = "jev-0.0.0-selftest"

    # --- prefilter over a realistic submissions "recent" block ---------------
    recent = {
        "form":            ["8-K",       "8-K",       "8-K",       "424B5",     "S-3",       "10-Q",      "8-K",       "8-K"],
        "filingDate":      ["2026-09-17","2026-09-18","2026-09-10","2026-08-01","2025-11-01","2026-08-14","2026-06-01","2026-09-25"],
        "items":           ["5.03,9.01", "3.01",      "5.02",      "",          "",          "",          "3.01",      "5.03"],
        "accessionNumber": ["0001-26-1", "0001-26-2", "0001-26-3", "0001-26-4", "0001-25-5", "0001-26-6", "0001-26-7", "0001-26-8"],
        "primaryDocument": ["a.htm",     "b.htm",     "c.htm",     "d.htm",     "e.htm",     "f.htm",     "g.htm",     "h.htm"],
    }
    sel = select_filings(recent, asof)
    got = [(f["form"], f["filingDate"], f["reason"]) for f in sel]
    assert ("8-K", "2026-09-17", "8k_items:5.03") in got, got
    assert ("8-K", "2026-09-18", "8k_items:3.01") in got, got
    only303 = {"form": ["8-K"], "filingDate": ["2026-09-20"], "items": ["3.03,9.01"],
               "accessionNumber": ["0001-26-9"], "primaryDocument": ["z.htm"]}
    assert [f["reason"] for f in select_filings(only303, "2026-09-22")] == ["8k_items:3.03"], "3.03-only 8-K is read"
    assert ("424B5", "2026-08-01", "offering") in got, got
    assert not any(d == "2026-09-10" for _, d, _ in got), "5.02-only 8-K must NOT be read"
    assert not any(d == "2025-11-01" for _, d, _ in got), "S-3 older than OFFERING_WINDOW must NOT be read"
    assert not any(d == "2026-06-01" for _, d, _ in got), "8-K older than EIGHTK_WINDOW must NOT be read"
    assert not any(d == "2026-09-25" for _, d, _ in got), "future-dated filing must NOT be read"
    assert got[0][1] == "2026-09-18", "newest first"
    assert doc_url("0001234567", "0001-26-1", "a.htm") == "https://www.sec.gov/Archives/edgar/data/1234567/0001261/a.htm"

    # --- stripper: drops script/style/ix:header, unescapes, keeps item text --------
    txt = strip_html(_CANNED["split"])
    assert "hidden xbrl junk" not in txt and "p{}" not in txt and "Item 5.03" in txt, txt[:200]
    assert "Company's" in strip_html(_CANNED["deficiency"]), "entity &#8217; must unescape"
    assert strip_html("plain text only") == "plain text only"

    # --- cap: over-limit text truncates after the cover page and flags it ----------
    big = "COVER PAGE " * 50 + "TABLE OF CONTENTS " + ("body " * (MAX_CHARS // 4))
    capped, trunc = cap_text(big)
    assert trunc and len(capped) <= MAX_CHARS and not capped.startswith("COVER"), (trunc, capped[:30])
    assert cap_text("short")[1] is False

    # --- question block is stable and hashed ------------------------------------
    assert len(QUESTIONS_SHA256) == 64 and set(QUESTION_ORDER) == set(QUESTIONS)
    assert len(QUESTIONS["split_ratio"]["criteria"]) <= 255 and len(QUESTIONS["split_ratio"]["criteria"]) == len(SPLIT_RATIOS) + 2 == 251

    # --- three canned filings through the fake ----------------------------------
    F = {}
    F["split"]      = sel[1]   # 09-17 5.03
    F["deficiency"] = sel[0]   # 09-18 3.01
    F["routine"]    = {"form": "8-K", "filingDate": "2026-09-10", "items": "5.02",
                       "accession": "0001-26-3", "primaryDocument": "c.htm", "reason": "manual"}
    res = {k: classify_filing(F[k], _CANNED[k], _fake_jev, model=MODEL,
                              pick_id="2026-09-22-EXMP", ticker="EXMP", cik="0001234567")
           for k in ("split", "deficiency", "routine")}

    s = res["split"]
    assert s["answers"]["reverse_split"]["value"] == "effective" and s["answers"]["reverse_split"]["p"] == 0.94, s["answers"]
    assert s["answers"]["split_ratio"]["value"] == "1-for-20", s["answers"]["split_ratio"]
    exp = "auto" if QUESTIONS_VERSION in SPLIT_AUTO_QUESTIONS else "review"
    assert s["routing"]["reverse_split"] == exp, s["routing"]   # 8-K 5.03, p 0.94: scoped auto under v2
    assert s["routing"]["split_ratio"] == "ignore" and s["routing"]["going_concern"] == "ignore", s["routing"]
    assert s["answers"]["going_concern"] == {"value": "no", "p": 0.97, "confidence": "", "probabilities": {"yes": 0.03, "no": 0.97}}

    d = res["deficiency"]
    assert d["answers"]["listing_status"]["value"] == "deficiency_notice" and d["routing"]["listing_status"] == "auto", d["routing"]
    assert d["answers"]["reverse_split"]["value"] == "none" and d["routing"]["reverse_split"] == "ignore"

    r = res["routine"]
    assert all(v == "ignore" for v in r["routing"].values()), r["routing"]

    # --- routing bands + special cases ------------------------------------------
    assert route("reverse_split", "effective", 0.95) == "review", "no filing context -> split never auto"
    k503 = {"form": "8-K", "items": "5.03,9.01"}
    assert route("reverse_split", "effective", 0.95, filing=k503) == ("auto" if QUESTIONS_VERSION in SPLIT_AUTO_QUESTIONS else "review")
    assert route("reverse_split", "effective", 0.85, filing=k503) == "review", "drift band [0.80, 0.90) is review"
    assert route("reverse_split", "effective", 0.95, filing={"form": "8-K", "items": "8.01"}) == "review", "outside tested scope"
    assert route("reverse_split", "effective", 0.95, filing={"form": "10-Q", "items": ""}) == "review", "outside tested scope"
    assert route("reverse_split", "announced", 0.99, filing=k503) == "review", "announced never auto"
    assert route("reverse_split", "effective", 0.95, truncated=True, filing=k503) == "review"
    assert route("listing_status", "halt", 0.95) == "auto"
    assert route("reverse_split", "effective", 0.75) == "review"
    assert route("reverse_split", "effective", 0.40) == "ignore"
    assert route("reverse_split", "effective", 0.95, truncated=True) == "review", "truncated never auto"
    assert route("reverse_split", "none", 0.99) == "ignore"
    assert route("other_material", "bankruptcy", 0.99) == "review", "bankruptcy always review"
    assert route("split_ratio", "other", 0.99) == "review"
    assert route("listing_status", "regained_compliance", 0.99) == "ignore"
    assert route("going_concern", "yes", 0.90) == "auto" and route("going_concern", "no", 0.99) == "ignore"
    assert route("reverse_split", "effective", "not-a-number") == "review"

    # --- schema safety: an out-of-schema choice is never accepted -----------------
    bad = _fake_jev(build_request(F["routine"], "x", MODEL))
    bad["answers"]["listing_status"]["choice"] = "delisted_forever"
    pa = parse_answers(bad, MODEL)
    assert pa["listing_status"]["value"] == "" and pa["listing_status"]["p"] == ""

    # --- version drift is fatal for the filing, not for the scan ------------------
    drift = _fake_jev(build_request(F["routine"], "x", MODEL)); drift["model"] = "jev-9.9.9"
    try:
        parse_answers(drift, MODEL); raise AssertionError("drift not detected")
    except VersionDrift:
        pass

    # --- aggregation: best non-none per question, sources recorded ---------------
    agg = aggregate([res["split"], res["deficiency"], res["routine"]])
    assert agg["fl_reverse_split"] == "effective" and agg["fl_split_ratio"] == "1-for-20", agg
    assert agg["fl_listing_status"] == "deficiency_notice" and agg["fl_listing_status_route"] == "auto", agg
    assert agg["fl_dilution_event"] == "none" and agg["fl_dilution_event_route"] == "ignore", agg
    assert agg["fl_filings_read"] == 3 and agg["fl_truncated"] == 0 and agg["fl_model"] == MODEL, agg
    assert set(agg["fl_source_accession"].split(";")) == {"0001-26-1", "0001-26-2"}, agg["fl_source_accession"]
    assert set(agg) == set(FL_FIELDS)
    assert aggregate([]) == FL_BLANK

    # --- log record carries everything a stranger needs ---------------------------
    rec = s["record"]
    for k in ("pick_id", "ticker", "cik", "accession", "form", "items", "filing_date", "doc_url",
              "text_sha256", "text_tokens", "truncated", "model", "questions_sha256",
              "thresholds_version", "answers", "routing", "latency_ms", "input_tokens",
              "captured_at", "human_label", "labeled_at"):
        assert k in rec, k
    assert rec["doc_url"].endswith("/1234567/0001261/a.htm") and rec["model"] == MODEL
    assert rec["text_sha256"] == _sha(s["text"]) and rec["questions_sha256"] == QUESTIONS_SHA256
    assert rec["answers"]["reverse_split"]["choice"] == "effective", "raw answers, not summarized"
    json.dumps(rec)                                  # must serialize as one jsonl line

    # --- snapshot() orchestration, injected fetch + call, no network ---------------
    docs = {"a.htm": _CANNED["split"], "b.htm": _CANNED["deficiency"], "d.htm": "<p>Prospectus supplement. No events.</p>"}
    fetched = []
    def fake_fetch(url):
        fetched.append(url); return docs[url.rsplit("/", 1)[1]]
    import tempfile
    with tempfile.NamedTemporaryFile("r", suffix=".jsonl", delete=False) as tmp:
        path = tmp.name
    global JEV_MODEL
    saved = JEV_MODEL; JEV_MODEL = MODEL
    try:
        snap = snapshot("EXMP", "0001234567", recent, asof, pick_id="2026-09-22-EXMP",
                        call=_fake_jev, fetch=fake_fetch, log_path=path)
    finally:
        JEV_MODEL = saved
    assert len(fetched) == 3 and snap["fl_reverse_split"] == "effective" and snap["fl_filings_read"] == 3, (fetched, snap)
    with open(path) as fh:
        lines = [json.loads(l) for l in fh if l.strip()]
    os.unlink(path)
    assert len(lines) == 3 and {l["accession"] for l in lines} == {"0001-26-1", "0001-26-2", "0001-26-4"}

    # non-fatal paths: fetch error, drift, unconfigured
    def bad_fetch(url): raise OSError("boom")
    snap2 = snapshot("EXMP", "0001234567", recent, asof, call=_fake_jev, fetch=bad_fetch, log_path=os.devnull)
    assert snap2["fl_filings_read"] == "" and snap2["fl_note"].count("doc_err:OSError") == 3, snap2
    def drift_call(req): r = _fake_jev(req); r["model"] = "jev-9.9.9"; return r
    JEV_MODEL = MODEL
    try:
        snap3 = snapshot("EXMP", "0001234567", recent, asof, call=drift_call, fetch=fake_fetch, log_path=os.devnull)
    finally:
        JEV_MODEL = saved
    assert "jev_version_drift" in snap3["fl_note"] and snap3["fl_reverse_split"] == "", snap3
    snap4 = snapshot("EXMP", "0001234567", recent, asof, fetch=fake_fetch, log_path=os.devnull)  # real call_jev, unpinned
    assert "jev_unconfigured" in snap4["fl_note"], snap4
    snap5 = snapshot("EXMP", "0001234567", recent, asof, dry_run=True)
    assert snap5["fl_filings_read"] == 3 and snap5["fl_note"].startswith("dry_run:"), snap5

    # --- gate 3 shadow: idempotent, capped, logs only -------------------------------
    import tempfile, csv as _csv
    td = tempfile.mkdtemp()
    pp, lp = os.path.join(td, "picks.csv"), os.path.join(td, "ev.jsonl")
    with open(pp, "w", newline="") as fh:
        w = _csv.writer(fh); w.writerow(["pick_id", "trading_date", "ticker"])
        w.writerows([["p1", "2026-09-22", "EXMP"], ["p2", "2026-09-22", "NOCIK"], ["p3", "2026-09-21", "EXMP"]])
    rec = {"form": [sel[1]["form"]], "filingDate": [sel[1]["filingDate"]], "items": [sel[1]["items"]],
           "accessionNumber": [sel[1]["accession"]], "primaryDocument": [sel[1]["primaryDocument"]]}
    kw = dict(picks_path=pp, log_path=lp, call=_fake_jev, fetch=lambda u: _CANNED["split"],
              recent_of=lambda c: rec, cik_of=lambda t: "" if t == "NOCIK" else "0001234567")
    JEV_MODEL = MODEL
    try:
        s1 = shadow("2026-09-22", **kw)
        lines = [json.loads(l) for l in open(lp)]
        s2 = shadow("2026-09-22", **kw)
        s3 = shadow("2026-09-22", max_reads=0, **dict(kw, log_path=os.path.join(td, "e2.jsonl")))
    finally:
        JEV_MODEL = saved
    assert (s1["picks"], s1["read"], s1["no_cik"], s1["errors"]) == (2, 1, 1, 0), s1
    assert len(lines) == 1 and lines[0]["pick_id"] == "p1" and lines[0]["model"] == MODEL, [l["pick_id"] for l in lines]
    assert s2["skipped_logged"] == 1 and s2["read"] == 0 and len(open(lp).readlines()) == 1, "idempotent"
    assert s3["cap_reached"] and not os.path.exists(os.path.join(td, "e2.jsonl")), s3

    print(f"filing_lens selftest OK  (lens {__version__}, questions sha {QUESTIONS_SHA256[:12]}, "
          f"{len(QUESTION_ORDER)} questions, {len(FL_FIELDS)} sidecar fields)")


# ---------------------------------------------------------------------------
# GATE 3 — SHADOW MODE. Runs as its own workflow step AFTER the scan has logged and
# committed nothing yet depends on it: it reads picks.csv for one trading date, reads
# each pick's prefiltered filings through Jev, and appends to filing_events.jsonl.
# LOGS ONLY. Nothing here writes picks.csv / edgar_snapshot.csv, and no routing value
# acts on anything; the log is what a later gate is judged on. It runs outside the scan
# on purpose: the pre-open rule must never wait on an outside model.
# ---------------------------------------------------------------------------
def shadow(trading_date, picks_path="picks.csv", log_path="filing_events.jsonl", max_reads=40,
           call=None, fetch=None, recent_of=None, cik_of=None):
    """-> summary dict. Idempotent: a pick_id already in the log is never re-read, so a
    re-run or a retried workflow cannot double-log or double-spend."""
    import csv
    summary = {"trading_date": trading_date, "picks": 0, "skipped_logged": 0, "read": 0,
               "no_cik": 0, "errors": 0, "cap_reached": False, "notes": []}
    if not (JEV_API_KEY and JEV_MODEL) and call is None:
        summary["notes"].append("no_key: shadow skipped")
        return summary
    call = call or call_jev
    fetch = fetch or fetch_doc
    if recent_of is None:
        from edgar_lens import submissions_recent as recent_of
    if cik_of is None:
        from asof_grader import ticker_to_cik as cik_of
    done = set()
    if os.path.exists(log_path):
        for line in open(log_path):
            try:
                done.add(json.loads(line).get("pick_id", ""))
            except ValueError:
                continue
    rows = [r for r in csv.DictReader(open(picks_path)) if r.get("trading_date") == trading_date]
    summary["picks"] = len(rows)
    for r in rows:
        if r["pick_id"] in done:
            summary["skipped_logged"] += 1
            continue
        if summary["read"] >= max_reads:
            summary["cap_reached"] = True
            break
        try:
            cik = cik_of(r["ticker"])
            if not cik:
                summary["no_cik"] += 1
                continue
            recent = recent_of(cik)
            out = snapshot(r["ticker"], cik, recent, trading_date, pick_id=r["pick_id"],
                           call=call, fetch=fetch, log_path=log_path)
            summary["read"] += int(out.get("fl_filings_read") or 0)
            if out.get("fl_note"):
                summary["notes"].append(f"{r['ticker']}:{out['fl_note'][:80]}")
        except Exception as e:                      # one ticker never stops the rest
            summary["errors"] += 1
            summary["notes"].append(f"{r['ticker']}:{type(e).__name__}")
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--ticker")
    ap.add_argument("--asof", default=date.today().isoformat())
    ap.add_argument("--dry-run", action="store_true", help="SEC only: list the filings that would be read")
    ap.add_argument("--shadow", action="store_true", help="gate 3: read the picks logged for --date, log only")
    ap.add_argument("--date", default=None, help="trading date for --shadow (default: today, America/New_York)")
    ap.add_argument("--max-reads", type=int, default=int(os.environ.get("FILING_LENS_MAX_READS", "40")))
    args = ap.parse_args()
    if args.selftest:
        _selftest(); return
    if args.shadow:
        d = args.date
        if not d:
            try:
                from zoneinfo import ZoneInfo
                d = datetime.now(ZoneInfo("America/New_York")).date().isoformat()
            except Exception:
                d = date.today().isoformat()
        try:
            s = shadow(d, max_reads=args.max_reads)
        except Exception as e:                      # shadow mode can never fail a run
            s = {"trading_date": d, "fatal": f"{type(e).__name__}: {str(e)[:120]}"}
        print("filing_lens shadow:", json.dumps(s)); return
    if args.ticker:
        from edgar_lens import submissions_recent
        from asof_grader import ticker_to_cik
        cik = ticker_to_cik(args.ticker)
        if not cik:
            print(f"{args.ticker}: no CIK"); return
        recent = submissions_recent(cik)
        snap = snapshot(args.ticker, cik, recent, args.asof, dry_run=args.dry_run)
        print(json.dumps(snap, indent=2)); return
    ap.print_help()


if __name__ == "__main__":
    main()
