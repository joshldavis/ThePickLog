/* =====================================================================
   ThePickLog — SEC EDGAR fundamentals proxy (Vercel serverless)
   ---------------------------------------------------------------------
   Free, official fundamentals for ANY SEC filer — including the micro/
   small-caps that FMP's free tier paywalls. Maps ticker -> CIK, pulls the
   XBRL "companyfacts" feed, and returns normalized annual statements.

   No API key needed. SEC requires a descriptive User-Agent with contact
   info (requests without one get 403), and asks for <10 req/s — both
   handled here, plus in-memory caching (ticker map 24h, facts 12h).

   Frontend: /api/edgar?symbol=CODX
   ===================================================================== */

const UA = { "User-Agent": "ThePickLog/1.0 (research tool; contact davis1163@gmail.com)" };
const TICKERS_URL = "https://www.sec.gov/files/company_tickers.json";
const factsCache = new Map();         // cik -> { at, data }
const FACTS_TTL = 12 * 60 * 60 * 1000;
// [QA M2] Companyfacts payloads are large (100s of KB each) — bound the
// per-warm-instance cache (FIFO eviction; Map preserves insertion order).
const FACTS_MAX = 100;
let tickerMap = null, tickerAt = 0;
const TICKER_TTL = 24 * 60 * 60 * 1000;

const clean = (s) => String(s || "").toUpperCase().replace(/[^A-Z0-9.\-]/g, "").slice(0, 12);
const pad = (c) => String(c).padStart(10, "0");

async function getTickerMap() {
  if (tickerMap && Date.now() - tickerAt < TICKER_TTL) return tickerMap;
  const r = await fetch(TICKERS_URL, { headers: UA });
  if (!r.ok) throw new Error("ticker list HTTP " + r.status);
  const j = await r.json();
  const map = {};
  for (const o of Object.values(j)) map[String(o.ticker).toUpperCase()] = { cik: pad(o.cik_str), title: o.title };
  tickerMap = map; tickerAt = Date.now();
  return map;
}

async function getFacts(cik) {
  const hit = factsCache.get(cik);
  if (hit && Date.now() - hit.at < FACTS_TTL) return hit.data;
  const r = await fetch(`https://data.sec.gov/api/xbrl/companyfacts/CIK${cik}.json`, { headers: UA });
  if (r.status === 404) throw new Error("no XBRL facts for CIK " + cik);
  if (!r.ok) throw new Error("companyfacts HTTP " + r.status);
  const data = await r.json();
  if (factsCache.size >= FACTS_MAX) factsCache.delete(factsCache.keys().next().value);
  factsCache.set(cik, { at: Date.now(), data });
  return data;
}

/* Merge annual (10-K, fp=FY) values across a priority list of us-gaap tags
   into a { fiscalYear: value } map. Earlier tags win for a given year. */
function fyMap(G, tags) {
  const out = {};
  for (const tag of tags) {
    const n = G[tag];
    if (!n || !n.units) continue;
    const unit = n.units.USD ? "USD" : (n.units.shares ? "shares" : Object.keys(n.units)[0]);
    for (const p of (n.units[unit] || [])) {
      // 10-K (domestic), 20-F / 40-F (foreign private issuers) = annual reports
      if (!/^(10-K|20-F|40-F)/.test(p.form || "") || p.fp !== "FY") continue;
      const fy = p.fy || (p.end ? +p.end.slice(0, 4) : null);
      if (fy == null) continue;
      if (out[fy] == null || p.end > out[fy].end) out[fy] = { val: p.val, end: p.end };
    }
  }
  const m = {};
  for (const k of Object.keys(out)) m[k] = out[k].val;
  return m;
}

export default async function handler(req, res) {
  const sym = clean((req.query || {}).symbol);
  if (!sym) return res.status(400).json({ error: "Missing symbol." });

  try {
    const map = await getTickerMap();
    const hit = map[sym];
    if (!hit) return res.status(404).json({ error: `No SEC CIK for ${sym} (may be foreign/OTC or not an SEC filer).` });

    const facts = await getFacts(hit.cik);
    const G = (facts.facts && facts.facts["us-gaap"]) || {};

    const REV   = fyMap(G, ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax"]);
    const NI    = fyMap(G, ["NetIncomeLoss", "ProfitLoss"]);
    const OI    = fyMap(G, ["OperatingIncomeLoss"]);
    const GP    = fyMap(G, ["GrossProfit"]);
    const COST  = fyMap(G, ["CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfGoodsSold"]);
    const DA    = fyMap(G, ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "DepreciationAmortizationAndAccretionNet"]);
    const SH    = fyMap(G, ["WeightedAverageNumberOfDilutedSharesOutstanding", "WeightedAverageNumberOfSharesOutstandingBasic"]);
    const OCF   = fyMap(G, ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"]);
    const CAPEX = fyMap(G, ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"]);
    const CASH  = fyMap(G, ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"]);
    const EQ    = fyMap(G, ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]);
    const CA    = fyMap(G, ["AssetsCurrent"]);
    const CL    = fyMap(G, ["LiabilitiesCurrent"]);
    const LTD   = fyMap(G, ["LongTermDebtNoncurrent", "LongTermDebt"]);
    const STD   = fyMap(G, ["LongTermDebtCurrent", "DebtCurrent", "ShortTermBorrowings"]);

    const years = Object.keys(REV).map(Number).sort((a, b) => b - a).slice(0, 4);
    if (!years.length) return res.status(422).json({ error: `No annual revenue in EDGAR for ${sym}.` });

    const arr = (m) => years.map((y) => (m[y] != null ? m[y] : null));
    const grossProfit = years.map((y) => GP[y] != null ? GP[y] : (REV[y] != null && COST[y] != null ? REV[y] - COST[y] : null));
    const ebitda = years.map((y) => (OI[y] != null && DA[y] != null) ? OI[y] + DA[y] : null);
    const freeCashFlow = years.map((y) => (OCF[y] != null && CAPEX[y] != null) ? OCF[y] - CAPEX[y] : (OCF[y] != null ? OCF[y] : null));
    const y0 = years[0];
    const debt0 = (LTD[y0] != null || STD[y0] != null) ? (LTD[y0] || 0) + (STD[y0] || 0) : null;

    const out = {
      symbol: sym, cik: hit.cik, name: facts.entityName || hit.title || sym,
      fiscalYears: years,
      revenue: arr(REV), grossProfit, operatingIncome: arr(OI), netIncome: arr(NI), ebitda,
      shares: arr(SH), operatingCashFlow: arr(OCF), freeCashFlow,
      totalDebt: debt0, cash: (CASH[y0] ?? null), equity: (EQ[y0] ?? null),
      currentAssets: (CA[y0] ?? null), currentLiabilities: (CL[y0] ?? null),
      source: "edgar"
    };
    res.setHeader("x-cache", factsCache.has(hit.cik) ? "WARM" : "MISS");
    return res.status(200).json(out);
  } catch (e) {
    return res.status(502).json({ error: "EDGAR fetch failed: " + e.message });
  }
}
