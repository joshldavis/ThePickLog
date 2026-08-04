#!/usr/bin/env python3
"""ThePickLog patch10 — the homepage nav never linked the testing lab.

index.html uses a JS single-page tab bar built from <button data-view=...>, so
patch7's anchor-based nav insert (which looked for `<a href="experiments.html">`)
silently skipped it. Result: from the homepage there was no nav route to
Experiments, the field note, Method or the Vetting Guide — only in-body panels.

Also: experiments.html / experiment-01.html / experiment-02.html carry
`<a href="experiments.html" class="on">`, which patch7's exact-string anchor
missed, so those three pages have no "Field notes" nav link either.

Fixes, minimally invasive:
  1. index.html desktop nav (#tabs) + mobile nav (#mobileMenu): add Experiments
     and Field notes as <button onclick="location.href=..."> so existing CSS
     applies and the delegated data-view handler ignores them (no JS change).
  2. index.html: rename the SPA tab "Guide" (data-view="scoring") to "Scoring"
     — it collided with the Vetting Guide (guide.html), which is a different page.
  3. Add the missing "Field notes" nav link to the three experiment pages.
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


# ------------------------------------------------- 1. index.html desktop nav
s = rd("index.html")

NAV_MARK = 'id="navExperiments"'
if NAV_MARK in s:
    skipped.append("index.html desktop nav (already applied)")
else:
    anchor = '<button data-view="watchlist">Watchlist</button>'
    if s.count(anchor) < 1:
        skipped.append("index.html desktop nav (anchor not found)")
    else:
        NEW = ('<button id="navExperiments" onclick="location.href=\'experiments.html\'">Experiments</button>'
               '<button id="navFieldNotes" onclick="location.href=\'split-adjustment-trap.html\'">Field notes</button>'
               + anchor)
        # first occurrence is the desktop #tabs nav
        s = s.replace(anchor, NEW, 1)
        done.append("index.html desktop nav +Experiments +Field notes")

# ------------------------------------------------- 2. index.html mobile menu
if 'id="mnavExperiments"' in s:
    skipped.append("index.html mobile menu (already applied)")
else:
    anchor2 = '<button data-view="watchlist">Watchlist</button>'
    if anchor2 not in s:
        skipped.append("index.html mobile menu (anchor not found)")
    else:
        NEW2 = ('<button id="mnavExperiments" onclick="location.href=\'experiments.html\'">Experiments</button>\n'
                '    <button id="mnavFieldNotes" onclick="location.href=\'split-adjustment-trap.html\'">Field notes</button>\n'
                '    ' + anchor2)
        # after the desktop insert above, the remaining occurrence is the mobile menu
        s = s.replace(anchor2, NEW2, 1)
        done.append("index.html mobile menu +Experiments +Field notes")

# --------------------------- 3. rename SPA "Guide" tab -> "Scoring" (collision)
n = s.count('<button data-view="scoring">Guide</button>')
if n == 0:
    skipped.append('index.html "Guide"->"Scoring" rename (already applied or not found)')
else:
    s = s.replace('<button data-view="scoring">Guide</button>',
                  '<button data-view="scoring">Scoring</button>')
    done.append('index.html renamed SPA tab "Guide" -> "Scoring" (%d place(s))' % n)

wr("index.html", s)

# ------------------- 4. Field notes nav link on the three experiment pages
for p in ["experiments.html", "experiment-01.html", "experiment-02.html"]:
    if not os.path.exists(p):
        skipped.append("nav %s (missing)" % p)
        continue
    t = rd(p)
    if 'href="split-adjustment-trap.html">Field notes' in t:
        skipped.append("nav %s (already applied)" % p)
        continue
    m = re.search(r'<a href="experiments\.html"(?: class="on")?>Experiments</a>', t)
    if not m:
        skipped.append("nav %s (no Experiments anchor)" % p)
        continue
    a = m.group(0)
    t = t.replace(a, a + '\n      <a href="split-adjustment-trap.html">Field notes</a>', 1)
    wr(p, t)
    done.append("nav %s +Field notes" % p)

print("APPLIED:")
for d in done:
    print("  +", d)
print("SKIPPED:")
for k in skipped:
    print("  -", k)
