# ThePickLog → Alpaca paper trading — setup

This adds in-app **Buy/Sell** to the scanner. Orders go through a tiny server-side
proxy (`api/alpaca.js`) so your Alpaca keys live in Vercel and never touch the browser.
It starts in **paper (fake money)** mode.

## What was added
- `api/alpaca.js` — Vercel serverless function. Holds keys, talks to Alpaca, handles `account` / `positions` / `order`.
- `package.json` — marks the project as ESM so the function runs cleanly on Vercel.
- `index.html` — a **Trade** column (qty + Buy/Sell per ticker), a **Test connection** button, and toast confirmations.

## Step 1 — Get Alpaca paper keys (2 min)
1. Sign in at **alpaca.markets** → **Paper Trading** account.
2. Open the **API Keys** panel (right side of the paper dashboard) → **Generate / View**.
3. Copy the **Key ID** and **Secret Key**. The secret is shown once — copy it now.

## Step 2 — Add the keys to Vercel
In your browser: **vercel.com** → the **ignitionscan** project → **Settings → Environment Variables**.
Add three (Production + Preview):

| Name | Value |
|------|-------|
| `ALPACA_KEY_ID` | your paper Key ID |
| `ALPACA_SECRET_KEY` | your paper Secret Key |
| `ALPACA_PAPER` | `true` |

Save, then **Deployments → ⋯ → Redeploy** so the new env vars load.

> The repo now has an `api/` folder, so Vercel auto-detects the serverless function. No build settings to change.

## Step 3 — Use it
1. Open your live `…vercel.app` site → **Watchlist** tab.
2. Click **Test connection** — you should see `✓ Connected (paper) · buying power $…`.
3. Set a share quantity on any row and click **Buy** or **Sell**. Confirm the dialog.
4. A toast shows the fill/acknowledgement. Verify it in the Alpaca paper dashboard too.

## How orders are placed
- **Market** order, **day** time-in-force, whole-share quantity from the row.
- Validated server-side (symbol present, qty > 0, side buy/sell) before hitting Alpaca.

## Going live (later, deliberately)
Set `ALPACA_PAPER` to `false` and swap in **live** API keys, then redeploy. The
"PAPER MODE" badge is hard-coded in the UI text — update it when you flip to live so
you don't fool yourself. **Live = real money on every click.**

## Portfolio tab (trade panel)
A **Portfolio** tab shows your live paper account:
- Account summary — equity, buying power, cash, today's P&L.
- **Positions** — symbol, qty, avg entry, current price, market value, unrealized P&L, plus a **Close** button (market-closes the whole position).
- **Open orders** — submitted time, symbol, side, qty, type, status, plus a **Cancel** button.

It loads on first open; hit **↻ Refresh** to update. All actions go through the same secure proxy.

## Notes / limits
- Markets must be open for market orders to fill (otherwise they queue as "new"/"accepted").
- Order *modify* isn't in the UI (cancel + re-place instead).
- Penny/low-float names: Alpaca may reject hard-to-borrow shorts or fractional qty; the toast surfaces Alpaca's reason.

## Automated paper trader (H-V3-PAPER, added 2026-07-13)

`paper_trader.py` + `.github/workflows/paper_trader.yml` mechanically trade the
**H-V3-EX1** rule (+10% target / 5-day hold) on published v0.3 picks — see the
H-V3-PAPER registration in HYPOTHESES.md. Purpose: measure real (paper) fill quality
against the fills-at-level proxy. The script is **hardcoded to
paper-api.alpaca.markets** — no code path reaches a live account.

**One-time setup (Josh):** add two GitHub repo secrets (Settings → Secrets and
variables → Actions): `ALPACA_KEY_ID` and `ALPACA_SECRET_KEY` — the same *paper*
keys already in Vercel. Until they exist, every run no-ops green. Optional:
`PAPER_NOTIONAL` env (default $200/pick).

**Daily cadence (UTC crons, shift 1h in winter):** ~8:00am ET `enter` (OPG market
buys for today's v0.3 picks, skip symbols already held), ~9:40am ET `arm` (+10% GTC
limit from each actual fill; the 10-minute gap after the open is a disclosed miss
window), ~3:45pm ET `manage` (cancel limit + market-close anything ≥5 sessions old;
snapshot filled take-profits). Every action appends to **`paper_trades.csv`**,
committed by the Action — the verifiable event log.
