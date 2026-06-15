/* =====================================================================
   IgnitionScan — Financial Modeling Prep proxy (Vercel serverless)
   ---------------------------------------------------------------------
   The browser NEVER sees your FMP key. It lives as a Vercel environment
   variable and is only used here, server-side — same security model as
   the Alpaca proxy.

   Required env var (Vercel → Project → Settings → Environment Variables):
     FMP_API_KEY   your Financial Modeling Prep API key (free tier is fine)

   Frontend calls this with GET, e.g.
     /api/fmp?fn=profile&symbol=BJDX
     /api/fmp?fn=quote&symbol=BJDX
     /api/fmp?fn=income&symbol=BJDX&limit=4

   Uses FMP's "stable" API (the legacy /api/v3 endpoints were retired for
   accounts created after Aug 31, 2025). Only a fixed allow-list of
   read-only endpoints is proxied and symbols are sanitized, so this can't
   be used as an open proxy for your key. Responses are cached in-memory
   per warm instance to respect the free tier (price data 60s, statements 12h).
   ===================================================================== */

const BASE = "https://financialmodelingprep.com/stable/";
const cache = new Map(); // path -> { at, data }
const TTL_PRICE = 60 * 1000;
const TTL_FUND = 12 * 60 * 60 * 1000;
const SHORT_TTL = new Set(["profile", "quote"]); // price-bearing → refresh often

const clampInt = (v, lo, hi, d) => {
  const n = parseInt(v, 10);
  return Number.isFinite(n) ? Math.max(lo, Math.min(hi, n)) : d;
};
const clean = (s) =>
  String(s || "").toUpperCase().replace(/[^A-Z0-9.\-]/g, "").slice(0, 12);

function buildPath(fn, q) {
  const sym = clean(q.symbol);
  if (!sym) return null;
  switch (fn) {
    case "profile": return `profile?symbol=${sym}`;
    case "quote":   return `quote?symbol=${sym}`;
    // NOTE: period/limit are premium params on FMP — omit them so the free
    // tier returns its default (~4 years of annual statements).
    case "income":  return `income-statement?symbol=${sym}`;
    case "balance": return `balance-sheet-statement?symbol=${sym}`;
    case "cash":    return `cash-flow-statement?symbol=${sym}`;
    default:        return null;
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

  const ttl = SHORT_TTL.has(fn) ? TTL_PRICE : TTL_FUND;
  const hit = cache.get(path);
  if (hit && Date.now() - hit.at < ttl) {
    res.setHeader("x-cache", "HIT");
    return res.status(200).json(hit.data);
  }

  try {
    const url = BASE + path + (path.includes("?") ? "&" : "?") + "apikey=" + encodeURIComponent(KEY);
    const r = await fetch(url);
    const text = await r.text();
    let data;
    try { data = JSON.parse(text); }
    catch { // FMP returns plaintext for paywalled/invalid requests (e.g. "Premium ...")
      return res.status(502).json({ error: "FMP non-JSON response (often a premium-only endpoint)", detail: text.slice(0, 160) });
    }
    if (!r.ok || (data && data["Error Message"]))
      return res.status(r.ok ? 502 : r.status).json({ error: "FMP upstream error", detail: data });
    cache.set(path, { at: Date.now(), data });
    res.setHeader("x-cache", "MISS");
    return res.status(200).json(data);
  } catch (e) {
    return res.status(502).json({ error: "Upstream fetch failed: " + e.message });
  }
}
