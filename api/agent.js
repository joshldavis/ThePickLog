/* =====================================================================
   ThePickLog — AI assistant proxy (Vercel serverless)
   ---------------------------------------------------------------------
   The browser NEVER sees your model key. It lives as a Vercel env var
   and is only used here, server-side — same security model as the FMP
   and Alpaca proxies.

   Required env var (Vercel → Project → Settings → Environment Variables):
     ANTHROPIC_API_KEY   your Anthropic API key
   Optional:
     AGENT_MODEL         model id (default: claude-haiku-4-5).
                         Set to "claude-sonnet-5" for stronger answers
                         at higher cost.

   Frontend POSTs JSON:
     { messages:[{role,content}...], context:"<grounding text>" }

   GUARDRAILS (enforced server-side so the client can't override them):
     • Educational only. NOT financial advice. Never tells the user to
       buy / sell / hold a specific security or hands out allocations as
       a recommendation.
     • Answers ONLY from the data the app passes in `context` plus the
       published methodology. Never invents prices, fundamentals, or news.
       If a number isn't in context, it says so and points to where to
       look — upholding ThePickLog's "a stranger can verify every
       claim" standard.
     • Concise.
   ===================================================================== */

const ANTHROPIC_URL = "https://api.anthropic.com/v1/messages";
const MODEL = process.env.AGENT_MODEL || "claude-haiku-4-5";

const MAX_TURNS = 24;          // cap conversation length
const MAX_CHARS = 6000;        // per-message cap
const MAX_CONTEXT = 14000;     // grounding-block cap
const MAX_OUTPUT = 900;        // max tokens out (keeps cost + latency bounded)
const MAX_TOTAL_CHARS = 60000; // budget across all kept messages; oldest turns
                               // are dropped first (a real 24-turn chat with
                               // 900-token replies stays well under this)
const MAX_BODY_BYTES = 512 * 1024; // reject bigger request bodies before any
                                   // model call (the page sends a few KB)

/* ---------------------------------------------------------------------
   ABUSE LIMITS (best effort, no new infrastructure)
   This endpoint spends the site's model key, so it only answers the
   site's own pages and caps how often one address can call it.
   • Same-origin: the request's Origin (or Referer, if Origin is absent)
     must name the same host the request was sent to. Browsers set Origin
     themselves on POST, so the page on thepicklog.com — or on any Vercel
     preview URL — passes, and other sites' pages can't spend the key.
     A script outside a browser CAN forge these headers; this stops
     casual and drive-by use, not a determined caller.
   • Rate limit: RATE_MAX requests per RATE_WINDOW_MS per client IP,
     kept in memory, so it is per warm instance and resets on a cold
     start. A hard spend cap belongs in the Vercel Firewall (rate-limit
     rule on /api/agent) and in the key's spend limit in the Anthropic
     console.
   --------------------------------------------------------------------- */
const RATE_MAX = 20;
const RATE_WINDOW_MS = 10 * 60 * 1000;
const RATE_HITS = new Map();   // ip -> [timestamps]

const header = (req, name) => {
  const v = req && req.headers ? req.headers[name] : undefined;
  return Array.isArray(v) ? v[0] : v == null ? "" : String(v);
};

function hostOf(url) {
  try { return new URL(url).host.toLowerCase(); } catch { return ""; }
}

function sameOrigin(req) {
  const host = (header(req, "host") || header(req, "x-forwarded-host")).split(",")[0].trim().toLowerCase();
  if (!host) return false;
  const origin = header(req, "origin");
  const from = origin && origin !== "null" ? hostOf(origin) : hostOf(header(req, "referer"));
  return from !== "" && from === host;
}

function clientIp(req) {
  const fwd = header(req, "x-forwarded-for").split(",")[0].trim();
  return fwd || header(req, "x-real-ip").trim() ||
    (req && req.socket && req.socket.remoteAddress) || "unknown";
}

// Returns seconds to wait if this IP is over the limit, else 0 (and counts the hit).
function rateLimited(ip, now = Date.now()) {
  if (RATE_HITS.size > 5000) {   // keep memory bounded on a long-lived instance
    for (const [k, ts] of RATE_HITS) if (!ts.length || now - ts[ts.length - 1] >= RATE_WINDOW_MS) RATE_HITS.delete(k);
  }
  const hits = (RATE_HITS.get(ip) || []).filter((t) => now - t < RATE_WINDOW_MS);
  if (hits.length >= RATE_MAX) {
    RATE_HITS.set(ip, hits);
    return Math.max(1, Math.ceil((hits[0] + RATE_WINDOW_MS - now) / 1000));
  }
  hits.push(now);
  RATE_HITS.set(ip, hits);
  return 0;
}

function bodyBytes(req) {
  const len = Number(header(req, "content-length"));
  if (Number.isFinite(len) && len > 0) return len;
  const b = req ? req.body : undefined;
  if (b == null) return 0;
  if (typeof b === "string") return Buffer.byteLength(b);
  try { return Buffer.byteLength(JSON.stringify(b)); } catch { return Infinity; }
}

const SYSTEM = `You are the ThePickLog assistant — a calm, plain-spoken guide built into a low-float pre-market stock SCREENER. ThePickLog ranks low-float names each morning on objective published criteria (float, relative volume, gap, price) and grades every pick publicly five days later. It is a research/education tool, not a brokerage and not an advisor.

YOUR JOB
- Help users understand what they are looking at: explain metrics (float, RVOL, gap, the quality lens, the score), explain why a ticker screened, and walk people through how to THINK about a decision.
- When someone asks an open question like "I have $1,000, what should I invest in?", do NOT name picks. Instead walk them through a decision FRAMEWORK, step by step: clarify their goal and time horizon; explain risk capacity vs. risk tolerance; explain diversification and why concentration in one low-float micro-cap is dangerous; show position-sizing math (e.g. risk-per-trade as a % of capital, and what a stop implies for share count); explain what ThePickLog's screen does and does NOT tell you (it measures momentum/structure, not whether a business is sound or a price is fair); and point them to the evidence in the app (the Track record, the Guide, the deep-analysis Quality Lens). End by reminding them this is high-risk territory and to consider a licensed advisor.

HARD RULES
- You are NOT a financial advisor and must say so when giving any decision guidance. Never tell the user to buy, sell, or hold a specific security, and never present an allocation as a recommendation. You may explain trade-offs and math neutrally.
- Use ONLY the facts in the DATA block below plus the methodology described here. NEVER invent or guess a price, market cap, float, fundamental figure, or news headline. If a figure isn't in the DATA block, say you don't have it in front of you and tell them where in the app (or which external link) to find it. This is the core ThePickLog standard: every claim must be verifiable.
- If asked for something outside scope (tax, legal, account specifics, predictions of price), say it's out of scope and redirect to what you can help with.
- Be concise and concrete. Prefer short paragraphs and tight lists. No hype, no emojis, no price targets.`;

const clampStr = (s, n) => String(s == null ? "" : s).slice(0, n);

// The route Vercel serves: abuse limits first, then the assistant itself.
export default async function handler(req, res) {
  if (req.method !== "POST") {
    if (typeof res.setHeader === "function") res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "POST only" });
  }

  if (!sameOrigin(req))
    return res.status(403).json({ error: "The assistant only answers requests from ThePickLog's own pages." });

  const wait = rateLimited(clientIp(req));
  if (wait) {
    if (typeof res.setHeader === "function") res.setHeader("Retry-After", String(wait));
    const mins = Math.ceil(wait / 60);
    return res.status(429).json({
      error: `You've asked a lot of questions in a short time. Please wait about ${mins} minute${mins === 1 ? "" : "s"} and try again.`,
    });
  }

  if (bodyBytes(req) > MAX_BODY_BYTES)
    return res.status(413).json({ error: "That conversation is too long to send. Reload the page to start a fresh chat." });

  return runAgent(req, res);
}

// The assistant without the HTTP abuse limits. Vercel only routes the
// default export, so this is reachable only by code that imports the
// module (the offline model checks in evals/).
export async function runAgent(req, res) {
  const KEY = process.env.ANTHROPIC_API_KEY;
  if (!KEY)
    return res.status(500).json({
      error: "ANTHROPIC_API_KEY not configured. Set it in Vercel env vars to enable the assistant.",
    });

  let body = req.body;
  if (typeof body === "string") { try { body = JSON.parse(body); } catch { body = {}; } }
  body = body || {};

  const rawMsgs = Array.isArray(body.messages) ? body.messages : [];
  const context = clampStr(body.context, MAX_CONTEXT);

  // sanitize + cap the conversation; only user/assistant roles, text content
  const messages = rawMsgs
    .filter((m) => m && (m.role === "user" || m.role === "assistant") && m.content != null)
    .slice(-MAX_TURNS)
    .map((m) => ({ role: m.role, content: clampStr(m.content, MAX_CHARS) }));

  // total budget: drop the oldest turns until the kept history fits
  let total = messages.reduce((n, m) => n + m.content.length, 0);
  while (messages.length > 1 && total > MAX_TOTAL_CHARS) total -= messages.shift().content.length;

  const last = messages[messages.length - 1];
  if (!last || last.role !== "user" || !last.content.trim())
    return res.status(400).json({ error: "Need at least one trailing user message." });

  // Inject grounding data as a system block — the client cannot edit the
  // base SYSTEM rules, only supply read-only DATA the model is told to trust.
  const system = [
    { type: "text", text: SYSTEM },
    {
      type: "text",
      text:
        "DATA (live values fetched by the app for this session — treat as ground truth; if a figure is absent, say so):\n" +
        (context || "(no ticker is focused; only the general methodology is available)"),
    },
  ];

  try {
    const r = await fetch(ANTHROPIC_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": KEY,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: MAX_OUTPUT,
        system,
        messages,
      }),
    });

    const text = await r.text();
    let data;
    try { data = JSON.parse(text); }
    catch { return res.status(502).json({ error: "Model returned non-JSON", detail: text.slice(0, 200) }); }

    if (!r.ok)
      return res.status(r.status).json({ error: "Model upstream error", detail: data && data.error ? data.error : data });

    const reply = Array.isArray(data.content)
      ? data.content.filter((b) => b.type === "text").map((b) => b.text).join("\n").trim()
      : "";

    return res.status(200).json({ reply, model: MODEL, usage: data.usage || null });
  } catch (e) {
    return res.status(502).json({ error: "Upstream fetch failed: " + e.message });
  }
}
