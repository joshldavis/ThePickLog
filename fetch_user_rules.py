#!/usr/bin/env python3
"""fetch_user_rules.py — pull active user-registered hypotheses from Supabase into
hypotheses/user_rules.json, for hypo_eval.py to merge into the Test-mode leaderboard.

Public anon read only (the board is public); the legacy anon JWT below is the same
key already shipped in the frontend. Non-fatal by design: on ANY error it writes an
empty list so the leaderboard still builds from the house rules. Stdlib only.

Run by the daily + weekly Actions before `python hypo_eval.py`.
"""
import json, urllib.request

# Legacy anon JWT — public (PostgREST accepts it for the anon-readable is_hypotheses
# table; the newer sb_publishable_ key is rejected by REST). Not a secret.
ANON = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFrZGdpamlvdHh4bmRyZmFnZXhyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMwNzIxNjMsImV4cCI6MjA4ODY0ODE2M30."
        "nnpHKZDzA8IAN6vO2HP-73kpZT4Je7Sl2DYwIxHaTa4")
URL = ("https://qkdgijiotxxndrfagexr.supabase.co/rest/v1/is_hypotheses"
       "?status=eq.active"
       "&select=id,author_name,title,kind,rule_json,exit_id,registered_at,status")
OUT = "hypotheses/user_rules.json"

def main():
    try:
        req = urllib.request.Request(URL, headers={"apikey": ANON, "Authorization": "Bearer " + ANON})
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8")
        rows = json.loads(body)                       # validate it parses
        if not isinstance(rows, list):
            raise ValueError("expected a JSON array")
        with open(OUT, "w") as f:
            json.dump(rows, f)
        print(f"fetched {len(rows)} active user rule(s) -> {OUT}")
    except Exception as e:                             # never block the Action
        with open(OUT, "w") as f:
            f.write("[]")
        print(f"user-rule fetch failed (non-fatal), wrote []: {e}")

if __name__ == "__main__":
    main()
