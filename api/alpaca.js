/* =====================================================================
   IgnitionScan — Alpaca trading proxy (Vercel serverless function)
   ---------------------------------------------------------------------
   The browser NEVER sees your Alpaca keys. They live as Vercel
   environment variables and are only used here, server-side.

   Required env vars (set in Vercel → Project → Settings → Environment Variables):
     ALPACA_KEY_ID       your Alpaca API key id
     ALPACA_SECRET_KEY   your Alpaca API secret
     ALPACA_PAPER        "true" (default) for paper, "false" for live money

   Frontend calls this with POST JSON, e.g.
     { "action": "account" }
     { "action": "positions" }
     { "action": "order", "symbol": "BJDX", "qty": 10, "side": "buy" }
   ===================================================================== */

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed. Use POST." });
  }

  const KEY = process.env.ALPACA_KEY_ID;
  const SECRET = process.env.ALPACA_SECRET_KEY;
  const PAPER = (process.env.ALPACA_PAPER ?? "true").toLowerCase() !== "false";

  if (!KEY || !SECRET) {
    return res.status(500).json({
      error:
        "Alpaca keys not configured. Set ALPACA_KEY_ID and ALPACA_SECRET_KEY in Vercel env vars.",
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

      if (!symbol) return res.status(400).json({ error: "Missing symbol." });
      if (!(qty > 0)) return res.status(400).json({ error: "Quantity must be a positive number." });
      if (side !== "buy" && side !== "sell")
        return res.status(400).json({ error: "Side must be 'buy' or 'sell'." });

      const order = {
        symbol,
        qty,
        side,
        type: "market",
        time_in_force: "day",
      };

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
