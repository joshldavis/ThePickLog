# Adding your Alpaca keys (so the scanner pulls live data)

A one-time setup. Takes about 5 minutes. No coding.

This lets ThePickLog's daily scanner get its market data from **Alpaca** instead of
Yahoo. You'll (1) turn on the data plan, (2) copy two keys, (3) paste them into GitHub.

---

## Step 1 — Turn on the data plan (once)

1. Go to **alpaca.markets** and log in.
2. Open your **Dashboard**, find the **market data** plan page.
3. Subscribe to **"Algo Trader Plus" ($99/month)**.

> Why: the free plan only sees one small exchange and misses the low-priced stocks we
> scan. Algo Trader Plus gives the full market ("SIP"), which is what the scanner needs.

## Step 2 — Copy your two keys

1. In the Alpaca dashboard, find **API Keys** (on the home/overview page).
2. Click **Generate New Key** (or view your existing keys).
3. Copy these two values somewhere safe for a moment:
   - **Key ID** — a short code (starts with `PK` or `AK`)
   - **Secret Key** — a long code. ⚠️ It's shown **only once** — copy it now.

## Step 3 — Paste them into GitHub

1. Go to **github.com/joshldavis/ignitionscan**
2. Click **Settings** (top menu).
3. In the left menu: **Secrets and variables → Actions**.
4. Click **New repository secret**, then add the first one:
   - **Name:** `ALPACA_KEY_ID`
   - **Secret:** paste your **Key ID** → click **Add secret**
5. Click **New repository secret** again, and add the second one:
   - **Name:** `ALPACA_SECRET_KEY`
   - **Secret:** paste your **Secret Key** → click **Add secret**

That's it — the keys are saved and hidden. ✅

## Step 4 — Flip it on

Tell me "switch the scanner to Alpaca," or set these two scanner settings:
`DATA_PROVIDER=alpaca` and `ALPACA_DATA_FEED=sip`. The next daily scan then runs on Alpaca.

---

### Good to know
- **Same keys as the trading panel.** These are the same two Alpaca keys already used for
  the trading panel (those live in Vercel). You can reuse the exact same values here —
  GitHub is just a second place they need to be, for the daily scanner.
- **Keep them private.** Never paste keys into the public website or share them. GitHub
  secrets keep them hidden — even you can't read them back after saving.
- **Two different homes:** trading keys → Vercel (already done); data keys → GitHub (this
  page). Same values, two places.
