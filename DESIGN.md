---
version: alpha
name: ThePickLog
description: Dark, data-dense research log for an openly graded stock-pick record. One teal accent, system fonts, monospace numbers, colour used for state rather than decoration.
colors:
  primary: "#1f6f6b"          # --a (buttons, tier A, logo gradient start)
  primary-text: "#31b3aa"     # --a-text (teal used as text/hover on dark; --a is too dark for text)
  primary-soft: "#1f6f6b22"   # --a-soft (active tab, tier C, chips)
  brand-highlight: "#8fd0cb"  # logo .spark gradient end, favicon.svg stop
  background: "#0a0e14"       # --bg
  surface: "#121826"          # --panel
  surface-2: "#0f1521"        # --panel-2 / --panel2 (inputs, stats, inset blocks)
  border: "#1f2937"           # --line
  text: "#e6edf3"             # --text / --tx
  muted: "#8b97a7"            # --muted / --dim
  success: "#2ec27e"          # --green (positive returns, live dot, buy)
  success-soft: "#2ec27e22"   # --green-soft
  danger: "#f0506e"           # --red (negative returns, errors, sell)
  danger-soft: "#f0506e22"    # --red-soft
  warning: "#f5b14c"          # --amber (prototype badge, notes, sample-data dot)
  info: "#4c9ff5"             # --blue (links, focus ring)
  on-primary: "#ffffff"       # .btn text
typography:
  display:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 40px
    letterSpacing: -0.02em
  h1:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 30px
    letterSpacing: -0.02em
  h1-article:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 36px
    lineHeight: 1.12
    letterSpacing: -0.025em
  h2:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 20px
    letterSpacing: -0.01em
  h3:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 16px
  body:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 14px
    lineHeight: 1.5
  body-article:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 16px
    lineHeight: 1.68
  small:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 12.5px
  label:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 11px
    fontWeight: 600
    letterSpacing: 0.08em
  mono-figure:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: 26px
    fontWeight: 800
  mono:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: 13px
spacing:
  xxs: 2px
  xs: 4px
  sm: 8px
  md: 10px
  lg: 12px
  xl: 14px
  2xl: 18px
  3xl: 26px
  gutter: 18px
  container: 1080px
  container-header: 1280px
  container-article: 760px
  container-doc: 820px
rounded:
  xs: 5px
  sm: 7px
  md: 9px
  btn: 10px
  stat: 12px
  lg: 14px
  modal: 16px
  pill: 999px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body}"
    fontWeight: 700
    padding: 9px 16px
    rounded: "{rounded.btn}"
  button-secondary:
    backgroundColor: "#ffffff0d"
    textColor: "{colors.text}"
    border: "1px solid {colors.border}"
    padding: 9px 16px
    rounded: "{rounded.btn}"
  card:
    backgroundColor: "{colors.surface}"
    border: "1px solid {colors.border}"
    rounded: "{rounded.lg}"
    padding: 18px
  stat:
    backgroundColor: "{colors.surface-2}"
    border: "1px solid {colors.border}"
    rounded: "{rounded.stat}"
    padding: 14px 16px
    label: "{typography.label}"
    value: "{typography.mono-figure}"
  input:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.text}"
    border: "1px solid {colors.border}"
    rounded: "{rounded.md}"
    padding: 9px 10px
    focus: "2px solid {colors.info}"
  nav:
    background: "rgba(10,14,20,.86) + backdrop-filter blur(10px)"
    borderBottom: "1px solid {colors.border}"
    height: 60px
    linkColor: "{colors.muted}"
    linkActiveBackground: "{colors.primary-soft}"
    linkRounded: "{rounded.md}"
  pill:
    rounded: "{rounded.pill}"
    padding: 2px 8px
    typography: "{typography.label}"
  badge-prototype:
    textColor: "{colors.warning}"
    border: "1px solid #f5b14c44"
    backgroundColor: "#f5b14c11"
    rounded: "{rounded.pill}"
---

## Overview

ThePickLog is a public, honestly graded log of screened low-float stock picks, built so a stranger can re-derive every number from the committed CSVs. The look serves that: a dark, quiet, terminal-like surface where numbers are set in monospace, colour means state (gain, loss, warning, link) and almost nothing is decorative. The audience is skeptical retail traders and researchers who came to check claims, not to be sold to. Pages should read as evidence: plain labels, the downside shown next to the upside, and "unvalidated" wherever the data has not cleared its bar.

## Colors

There is no shared stylesheet. Every page declares its own `:root` custom properties inside its `<style>` block (`index.html` line ~18, `experiment-01.html`, `method.html` and so on), and the server-rendered pages keep a `THEME` object in `api/receipt.js`, `api/profile.js` and `api/og.js`. A token change therefore has to be made in every HTML file's `:root` and in those `THEME` objects, not in one place.

The tokens above are the homepage set (`index.html`), which most article pages share. Roles:
- **Primary teal `#1f6f6b`** for filled buttons, tier A and the logo; **`#31b3aa`** whenever teal is used as text or hover on dark (the darker teal fails contrast as text).
- **Green / red** only for signed outcomes (positive / negative net return, buy / sell, live / error). **Amber** for caveats, the prototype badge and "sample data". **Blue** for links and the focus ring.
- Translucent white overlays (`#ffffff05`, `#ffffff08`, `#ffffff0d`, `#ffffff10`) are the standard hover and ghost fills.

A second palette is in use on the doc/tool pages (`dashboard.html`, `calculator.html`, `disclaimer.html`, `gate.html`, `guide.html`, `method.html`, `privacy.html`, `scorecard.html`, `terms.html`, `trust.html`): bg `#0e1116`, panel `#161b22`, panel2 `#1c2230`, line `#2a3240`, dim `#8b98a8`, blue `#5aa0ff`. A third is in `api/*.js`: bg `#0c0f14`, panel `#0e1420`, text `#e8e8e8`. See Do's and Don'ts.

## Typography

System fonts only; there are no web-font imports anywhere. Sans: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif` (`--sans` in `index.html`). Mono: `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace` (`--mono`); article pages inline a shorter `ui-monospace, Menlo, monospace`.

- Every figure (returns, prices, tickers, scores, counts, pick ids) is monospace: `.num`, `.tick`, `.stat .v`, `.exp-meta`.
- Headings use negative letter-spacing and the browser's default bold (no explicit weight is set); the logo is 18px / 800, stat figures 800.
- Labels and table heads are small uppercase with wide tracking (11px, `.06em` to `.08em`) in muted.
- Three body scales exist by page type: app (`index.html`, 14px tables / 1.5), long-form articles (`experiment-*.html`, `split-adjustment-trap.html`, `late-cohorts.html`: 16px / 1.68, h1 36px, h2 23px, h3 17.5px, standfirst 18.5px), and doc pages (`method.html` etc.: 15px / 1.6, h1 26px, h2 16px). Match the page type you are editing.

## Layout

- Containers: app `.wrap` max 1080px with 18px side padding; header `.top-in` max 1280px; articles 760px; doc pages 820px.
- Sticky top bar (60px on `index.html`, 56px elsewhere), translucent background with `backdrop-filter: blur(10px)` and a bottom border.
- One canonical nav across pages (UI audit 2026-08-19, commented in each page): desktop `nav.tabs`, collapsing to a `.menu-btn` + `#mobileMenu` at 880–980px depending on page. Active tab uses `.active` or `.on`; both are styled.
- Grids use `display:grid` with gaps of 8, 10, 12 or 14px. Stat rows are 4 columns, dropping to 2 below 820px; two-column layouts drop to 1 below 820px.
- Breakpoints in use: 720, 820, 880, 900, 980px. Reuse one of these rather than adding a new one.
- Footer: top border, muted 12.5px text, disclaimer line, and on `index.html` / `guide.html` / `trust.html` a `__BUILDSTAMP__` token that `scripts/stamp-build.mjs` fills at deploy.

## Elevation & Depth

Depth comes from surface steps and borders, not shadows: background `#0a0e14` → panel `#121826`, with `surface-2` `#0f1521` for inset blocks and inputs, all edged with a 1px `--line` border. Shadows are reserved for things that float over the page:
- toast `0 8px 30px #0008`
- mobile menu `0 18px 40px #000a`
- modal `0 20px 60px #000a`, over a `#0008` backdrop with a 2px blur
- info drawer `-18px 0 50px #000a`

A featured card is marked with a teal border and `box-shadow: 0 0 0 1px var(--a) inset`, not a lift.

## Shapes

Rounded but not soft. Radii in use: 999px for pills, chips and badges; 16px modal; 14px panels and boxes (`--radius`); 12px stats; 10px buttons; 9px inputs and nav links; 7px tier squares, small trade buttons and the logo spark; 5px inline `code`. Status dots are 8px circles. Bars (`.scorebar`, weight bars) are 6–10px tall with 4–6px radius on a `#ffffff10` track.

## Components

- **Buttons**: `.btn` (teal fill, white 700 14px text, 9px 16px, radius 10) and `.btn.ghost` (`#ffffff0d` fill, border line). Hover is `filter: brightness(1.05)`. Small trade buttons `.tbtn.buy/.sell/.flat` use the soft green/red fills with a 55-alpha border.
- **Cards**: `.panel` (surface, border, radius 14, padding 18); article `.box` and `.next` (radius 14, padding 18px 20px).
- **Stats**: `.stat` with `.k` label and `.v` mono figure.
- **Tables**: full width, collapsed borders, uppercase muted `th`, `.num` right-aligned mono cells, row hover `#ffffff05`.
- **Tier chips**: `.tier.A`–`.D` are a single-hue teal heat ramp (A hottest). This is deliberate: tiers measure momentum intensity, and the log shows hotter tiers draw down deeper, so tiers must never be green = good.
- **Conviction chips / pills**: `.cvtag.hot` (amber), `.cvtag.cool` (muted), `.pill`; never styled as a buy signal.
- **Notes and callouts**: `.note` (amber text on `#f5b14c10`), `.why` (dashed border on surface-2), article `.pull` (3px teal left rule), `.callout` (3px amber left rule).
- **Verdict box** (experiment pages): `#241318` fill, `#5a2a33` border, `#ffb3c0` heading.
- **Inputs**: surface-2 fill, border line, radius 9, `font: inherit`; focus is a 2px blue outline.
- **Accessibility baseline** (each page, "UI audit 2026-08-19"): `.skip` link, global `:focus-visible` blue outline, 24px footer touch targets, opaque `#mobileMenu` with z-index 60.

## Do's and Don'ts

Do:
- Use the existing custom properties (`var(--a)`, `var(--panel)`, `var(--line)` …) instead of raw hex, and add a new token to every page's `:root` if one is truly needed.
- Set numbers in monospace and show the downside (MAE, losses, negative returns) as prominently as the upside.
- Label best-case excursion as not an achievable return, and keep "unvalidated" labels visible.
- Use `--a-text` (`#31b3aa`) for teal text; keep the focus ring and skip link on new pages.
- Copy an existing page of the same type (app, article, doc) when making a new one, so nav, footer and a11y blocks come with it.

Don't:
- Don't add web fonts, a CSS framework or a shared stylesheet as part of an unrelated change; the site has none today.
- Don't colour tiers or scores green/red to imply quality.
- Don't use green, red or amber decoratively; they carry meaning.
- Don't remove the `__BUILDSTAMP__` token from the three footers.

Known inconsistencies (pick one deliberately when touching them; don't "fix" them silently in an unrelated change):
- Three dark palettes: homepage/article set, doc/tool-page set (`#0e1116` / `#161b22` / `#2a3240` / blue `#5aa0ff`), and `api/*.js` THEME (`#0c0f14` / `#0e1420` / text `#e8e8e8`).
- Variable names differ: `index.html` uses `--text`, `--muted`, `--panel-2`; other pages use `--tx`, `--dim`, `--panel2`.
- Muted grey is `#8b97a7` on some pages and `#8b98a8` on others.
- Header height is 60px on `index.html` and 56px elsewhere; the mobile-nav breakpoint varies from 880px to 980px.
- The mono stack is `--mono` on the homepage but a shorter inline stack on article pages.
- Active-tab fill varies (`--a-soft`, `#1f6f6b1f`, `#ffffff10`, `#ffffff14`).
