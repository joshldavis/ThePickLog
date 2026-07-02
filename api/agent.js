/* =====================================================================
   IgnitionScan — AI assistant proxy (Vercel serverless)
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
       look — upholding IgnitionScan's "a stranger can verify every
       claim" standard.
     • Concise.
   ===================================================================== */

const ANTHROPIC_URL = "https://api.anthropic.com/v1/messages";
const MODEL = process.env.AGENT_MODEL || "claude-haiku-4-5";

const MAX_TURNS = 24;          // cap conversation length
const MAX_CHARS = 6000;        // per-message cap
const MAX_CONTEXT = 14000;     // grounding-block cap
const MAX_OUTPUT = 900;        // max tokens out (keeps cost + latency bounded)

const SYSTEM = `You are the IgnitionScan assistant — a calm, plain-spoken guide built into a low-float pre-market stock SCREENER. IgnitionScan ranks low-float names each morning on objective published criteria (float, relative volume, gap, price) and grades every pick publicly five days later. It is a research/education tool, not a brokerage and not an advisor.

YOUR JOB
- Help users understand what they are looking at: explain metrics (float, RVOL, gap, the quality/Buffett lens, the score), explain why a ticker screened, and walk people through how to THINK about a decision.
- When someone asks an open question like "I have $1,000, what should I invest in?", do NOT name picks. Instead walk them through a decision FRAMEWORK, step by step: clarify their goal and time horizon; explain risk capacity vs. risk tolerance; explain diversification and why concentration in one low-float micro-cap is dangerous; show position-sizing math (e.g. risk-per-trade as a % of capital, and what a stop implies for share count); explain what IgnitionScan's screen does and does NOT tell you (it measures momentum/structure, not whether a business is sound or a price is fair); and point them to the evidence in the app (the Track record, the Guide, the deep-analysis Quality Lens). End by reminding them this is high-risk territory and to consider a licensed advisor.

HARD RULES
- You are NOT a financial advisor and must say so when giving any decision guidance. Never tell the user to buy, sell, or hold a specific security, and never present an allocation as a recommendation. You may explain trade-offs and math neutrally.
- Use ONLY the facts in the DATA block below plus the methodology described here. NEVER invent or guess a price, market cap, float, fundamental figure, or news headline. If a figure isn't in the DATA block, say you don't have it in front of you and tell them where in the app (or which external link) to find it. This is the core IgnitionScan standard: every claim must be verifiable.
- If asked for something outside scope (tax, legal, account specifics, predictions of price), say it's out of scope and redirect to what you can help with.
- Be concise and concrete. Prefer short paragraphs and tight lists. No hype, no emojis, no price targets.`;

const clampStr = (s, n) => String(s == null ? "" : s).slice(0, n);

export default async function handler(req, res) {
  if (req.method !== "POST")
    return res.status(405).json({ error: "POST only" });

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

  if (!messages.length || messages[messages.length - 1].role !== "user")
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
