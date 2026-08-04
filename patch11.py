#!/usr/bin/env python3
"""ThePickLog patch11 — repair patch10's misplaced mobile-menu insert.

patch10 inserted the desktop pair BEFORE the Watchlist anchor, which left the
anchor's first occurrence still inside #tabs. The second replace therefore also
landed in the desktop nav: #tabs ended up with four buttons (two duplicates) and
#mobileMenu got none.

This removes the mnav* pair wherever it currently sits and inserts it inside the
#mobileMenu block only, located by slice rather than by global first-match.
"""
import io, os, re

R = os.path.expanduser("~/Documents/AMD Ventures/stock screener/Archive-IgnitionScan-2026-06-28/ignitionscan")
os.chdir(R)
done, skipped = [], []


def rd(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def wr(p, s):
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(s)


s = rd("index.html")
before = s

# 1. strip every mnav* button, wherever patch10 put it
s, n_removed = re.subn(r'\s*<button id="mnav(?:Experiments|FieldNotes)"[^>]*>[^<]*</button>', "", s)
if n_removed:
    done.append("removed %d stray mnav button(s) from the desktop nav" % n_removed)
else:
    skipped.append("no stray mnav buttons found")

# 2. sanity: desktop nav must now hold exactly one Experiments + one Field notes
m = re.search(r'<nav class="tabs" id="tabs">.*?</nav>', s, re.S)
if not m:
    skipped.append("desktop #tabs nav not found — aborting mobile insert")
else:
    tabs = m.group(0)
    if tabs.count("navExperiments") != 1 or tabs.count("navFieldNotes") != 1:
        skipped.append("desktop nav has %d Experiments / %d Field notes — expected 1 each, aborting"
                       % (tabs.count("navExperiments"), tabs.count("navFieldNotes")))
    else:
        done.append("desktop nav verified: 1 Experiments + 1 Field notes")

        # 3. insert into #mobileMenu, located by slice
        mm = re.search(r'<div id="mobileMenu"[^>]*>(.*?)</div>', s, re.S)
        if not mm:
            skipped.append("#mobileMenu block not found")
        elif "mnavExperiments" in mm.group(1):
            skipped.append("mobile menu (already applied)")
        else:
            block = mm.group(0)
            anchor = '<button data-view="watchlist">Watchlist</button>'
            if anchor not in block:
                skipped.append("mobile menu (Watchlist anchor not found in block)")
            else:
                NEW = ('<button id="mnavExperiments" onclick="location.href=\'experiments.html\'">Experiments</button>\n'
                       '    <button id="mnavFieldNotes" onclick="location.href=\'split-adjustment-trap.html\'">Field notes</button>\n'
                       '    ' + anchor)
                newblock = block.replace(anchor, NEW, 1)
                s = s.replace(block, newblock, 1)
                done.append("mobile menu +Experiments +Field notes")

if s != before:
    wr("index.html", s)

print("APPLIED:")
for d in done:
    print("  +", d)
print("SKIPPED:")
for k in skipped:
    print("  -", k)
