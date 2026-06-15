/* =====================================================================
   IgnitionScan — Financial Modeling Prep proxy (Vercel serverless)
   ---------------------------------------------------------------------
   The browser NEVER sees your FMP key. It lives as a Vercel environment
   variable and is only used here, server-side — same security model as
   the Alpaca proxy.

   Required env var (Vercel → Project → Settings → Environment Variables):
     FMP_API_KEY   your Financial Modeling Prep API key (free tier is fine)

   Frontend calls this with GET, e.g.
     /api/fmp?fn=quote&symbols=BJDX,MASK
     /api/fmp?fn=profile&symbol=BJDX
     /api/fmp?fn=income&symbol=BJDX&limit=4

   Only a fixed allow-list of read-only endpoints is proxied, and symbols
   are sanitized, so this can't be used as an open proxy for your key.
   Responses are cached in-memory per warm instance to respect the free
   tier's rate limit (quotes 60s, fundamentals 12h).
   ===================================================================== */

const BASE = "https://financialmodelingprep.com/api/v3/";
const cache = new Map(); // path -> { at, data }
const TTL_QUOTE = 60 * 1000;
const TTL_FUND = 12 * 60 * 60 * 1000;

const clampInt = (v, lo, hi, d) => {
  const n = parseInt(v, 10);
  return Number.isFinite(n) ? Math.max(lo, Math.min(hi, n)) : d;
};
const clean = (s) =>
  String(s || "").toUpperCase().replace(/[^A-Z0-9.\-,]/g, "").slice(0, 200);

function buildPath(fn, q) {
  const sym = clean(q.symbol);
  const syms = clean(q.symbols);
  switch (fn) {
    case "quote":      return syms ? `quote/${syms}` : null;
    case "profile":    return sym ? `profile/${sym}` : null;
    case "income":     return sym ? `income-statement/${sym}?period=annual&limit=${clampInt(q.limit,1,8,4)}` : null;
    case "balance":    return sym ? `balance-sheet-statement/${sym}?period=annual&limit=${clampInt(q.limit,1,8,2)}` : null;
    case "cash":       return sym ? `cash-flow-statement/${sym}?period=annual&limit=${clampInt(q.limit,1,8,4)}` : null;
    case "ratios":     return sym ? `ratios/${sym}?period=annual&limit=${clampInt(q.limit,1,8,1)}` : null;
    case "keymetrics": return sym ? `key-metrics/${sym}?period=annual&limit=${clampInt(q.limit,1,8,1)}` : null;
    default:           return null;
  }
}

export default async function handler(req, res) {
  const KEY = process.env.FMP_API_KEY;
  if (!KEY) {
    return res.status(500).json({
      error: "FMP_API_KEY not configured. Set it in Vercel env vars to enable live data.",
    });
  }

  const q = req.query || {};
  const fn = String(q.fn || "");
  const path = buildPath(fn, q);
  if (!path) return res.status(400).json({ error: "Bad or missing fn / symbol." });

  const ttl = fn === "quote" ? TTL_QUOTE : TTL_FUND;
  const hit = cache.get(path);
  if (hit && Date.now() - hit.at < ttl) {
    res.setHeader("x-cache", "HIT");
    return res.status(200).json(hit.data);
  }

  try {
    const url = BASE + path + (path.includes("?") ? "&" : "?") + "apikey=" + encodeURIComponent(KEY);
    const r = await fetch(url);
    const data = await r.json();
    if (!r.ok) return res.status(r.status).json({ error: "FMP upstream error", detail: data });
    cache.set(path, { at: Date.now(), data });
    res.setHeader("x-cache", "MISS");
    return res.status(200).json(data);
  } catch (e) {
    return res.status(502).json({ error: "Upstream fetch failed: " + e.message });
  }
}
