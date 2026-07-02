/* =====================================================================
   IgnitionScan — Alpaca trading proxy (Vercel serverless function)
   ---------------------------------------------------------------------
   The browser NEVER sees your Alpaca keys. They live as Vercel
   environment variables and are only used here, server-side.

   Required env vars (set in Vercel → Project → Settings → Environment Variables):
     ALPACA_KEY_ID       your Alpaca API key id
     ALPACA_SECRET_KEY   your Alpaca API secret
     ALPACA_PAPER        "true" (default) for paper, "false" for live money
     ALPACA_UI_TOKEN     owner-only gate — required before ANY action works;
                         the same value goes in the Watchlist → Alpaca panel

   Frontend calls this with POST JSON, e.g.
     { "action": "account" }
     { "action": "positions" }
     { "action": "order", "symbol": "BJDX", "qty": 10, "side": "buy" }
   ===================================================================== */

import { timingSafeEqual } from "crypto";

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed. Use POST." });
  }

  // ---- Owner gate [QA 2026-07-02 B2] -------------------------------------
  // This proxy fronts the OWNER'S personal Alpaca paper account. Without a
  // gate, any visitor to the public URL could place (paper) orders and read
  // balances/positions. Set ALPACA_UI_TOKEN in Vercel; the owner enters the
  // same token once in the Watchlist → Alpaca panel (stored in their own
  // browser's localStorage, sent as the x-owner-token header). Everyone else
  // is pointed to Compete mode (per-user $100k sim via Supabase).
  const OWNER_TOKEN = process.env.ALPACA_UI_TOKEN || "";
  if (!OWNER_TOKEN) {
    return res.status(403).json({
      error:
        "Alpaca access is owner-only and not armed: set ALPACA_UI_TOKEN in Vercel env vars, then enter the same token in the Watchlist → Alpaca panel. Visitors: sign in on the Compete tab to trade with play money.",
    });
  }
  const given = Buffer.from(String(req.headers["x-owner-token"] || ""));
  const expected = Buffer.from(OWNER_TOKEN);
  const tokenOk = given.length === expected.length && timingSafeEqual(given, expected);
  if (!tokenOk) {
    return res.status(401).json({
      error:
        "Owner token required — this Alpaca paper account belongs to the site owner. Sign in on the Compete tab to trade with $100,000 in play money instead.",
    });
  }

  // Accept the proxy's own names plus Alpaca's native names (APCA_*) and a few
  // common variants, so a reasonable env-var name choice just works.
  const KEY = process.env.ALPACA_KEY_ID || process.env.APCA_API_KEY_ID
    || process.env.ALPACA_API_KEY_ID || process.env.ALPACA_API_KEY || process.env.ALPACA_KEY;
  const SECRET = process.env.ALPACA_SECRET_KEY || process.env.APCA_API_SECRET_KEY
    || process.env.ALPACA_API_SECRET_KEY || process.env.ALPACA_SECRET;
  // Paper is the default AND the floor. Going live takes TWO deliberate signals:
  // ALPACA_PAPER=false AND ALPACA_ALLOW_LIVE=yes_i_understand. A single stray/typo'd
  // env var can no longer route real-money orders to the live endpoint. [QA M1]
  const wantsLive = (process.env.ALPACA_PAPER ?? "true").toLowerCase() === "false";
  const liveArmed = (process.env.ALPACA_ALLOW_LIVE ?? "").toLowerCase() === "yes_i_understand";
  const PAPER = !(wantsLive && liveArmed);

  if (!KEY || !SECRET) {
    return res.status(500).json({
      error:
        "Alpaca keys not configured. In Vercel set ALPACA_KEY_ID and ALPACA_SECRET_KEY (scope: Production), then redeploy.",
    });
  }

  const BASE = PAPER
    ? "https://paper-api.alpaca.markets"
    : "https://api.alpaca.markets";

  const headers = {
    "APCA-API-KEY-ID": KEY,
    "APCA-API-SECRET-KEY": SECRET,
    "Content-Type": "application/json",
  };

  // Vercel parses JSON bodies automatically; fall back to manual parse.
  let body = req.body;
  if (typeof body === "string") {
    try { body = JSON.parse(body); } catch { body = {}; }
  }
  body = body || {};
  const action = body.action;

  try {
    let alpacaRes, data;

    if (action === "account") {
      alpacaRes = await fetch(`${BASE}/v2/account`, { headers });
      data = await alpacaRes.json();
      return res.status(alpacaRes.status).json({ paper: PAPER, account: data });
    }

    if (action === "positions") {
      alpacaRes = await fetch(`${BASE}/v2/positions`, { headers });
      data = await alpacaRes.json();
      return res.status(alpacaRes.status).json({ paper: PAPER, positions: data });
    }

    if (action === "orders") {
      const status = ["open", "closed", "all"].includes(body.status) ? body.status : "open";
      alpacaRes = await fetch(`${BASE}/v2/orders?status=${status}&limit=50&nested=false`, { headers });
      data = await alpacaRes.json();
      return res.status(alpacaRes.status).json({ paper: PAPER, orders: data });
    }

    if (action === "cancel") {
      const id = String(body.id || "").trim();
      if (!id) return res.status(400).json({ error: "Missing order id." });
      alpacaRes = await fetch(`${BASE}/v2/orders/${encodeURIComponent(id)}`, {
        method: "DELETE",
        headers,
      });
      // 204 = success with no body
      data = alpacaRes.status === 204 ? { canceled: id } : await alpacaRes.json().catch(() => ({}));
      return res.status(alpacaRes.status === 204 ? 200 : alpacaRes.status).json({ paper: PAPER, cancel: data });
    }

    if (action === "close_position") {
      const symbol = String(body.symbol || "").toUpperCase().trim();
      if (!symbol) return res.status(400).json({ error: "Missing symbol." });
      alpacaRes = await fetch(`${BASE}/v2/positions/${encodeURIComponent(symbol)}`, {
        method: "DELETE",
        headers,
      });
      data = await alpacaRes.json().catch(() => ({}));
      return res.status(alpacaRes.status).json({ paper: PAPER, close: data });
    }

    if (action === "order") {
      const symbol = String(body.symbol || "").toUpperCase().trim();
      const qty = Number(body.qty);
      const side = String(body.side || "").toLowerCase();
      const type = ["market", "limit", "stop", "stop_limit"].includes(body.type) ? body.type : "market";
      const bracket = body.order_class === "bracket";

      if (!symbol) return res.status(400).json({ error: "Missing symbol." });
      if (!(qty > 0)) return res.status(400).json({ error: "Quantity must be a positive number." });
      if (side !== "buy" && side !== "sell")
        return res.status(400).json({ error: "Side must be 'buy' or 'sell'." });

      const num = (v) => (v === undefined || v === null || v === "" ? NaN : Number(v));
      const limit_price = num(body.limit_price);
      const stop_price = num(body.stop_price);

      // per-type price validation
      if ((type === "limit" || type === "stop_limit") && !(limit_price > 0))
        return res.status(400).json({ error: "Limit price required for a limit order." });
      if ((type === "stop" || type === "stop_limit") && !(stop_price > 0))
        return res.status(400).json({ error: "Stop price required for a stop order." });

      // bracket orders need GTC/day and a take-profit + stop-loss
      const order = {
        symbol,
        qty,
        side,
        type,
        time_in_force: bracket ? "gtc" : "day",
      };
      if (type === "limit" || type === "stop_limit") order.limit_price = limit_price;
      if (type === "stop" || type === "stop_limit") order.stop_price = stop_price;

      if (bracket) {
        const tp = num(body.take_profit_limit);
        const slStop = num(body.stop_loss_stop);
        const slLimit = num(body.stop_loss_limit);
        if (!(tp > 0)) return res.status(400).json({ error: "Bracket order needs a take-profit price." });
        if (!(slStop > 0)) return res.status(400).json({ error: "Bracket order needs a stop-loss price." });
        order.order_class = "bracket";
        order.take_profit = { limit_price: tp };
        order.stop_loss = slLimit > 0 ? { stop_price: slStop, limit_price: slLimit } : { stop_price: slStop };
      }

      alpacaRes = await fetch(`${BASE}/v2/orders`, {
        method: "POST",
        headers,
        body: JSON.stringify(order),
      });
      data = await alpacaRes.json();
      return res.status(alpacaRes.status).json({ paper: PAPER, order: data });
    }

    return res.status(400).json({
      error: "Unknown action. Use account | positions | orders | order | cancel | close_position.",
    });
  } catch (e) {
    return res.status(502).json({ error: "Alpaca request failed: " + (e?.message || String(e)) });
  }
}
