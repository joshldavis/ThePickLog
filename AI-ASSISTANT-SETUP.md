# ThePickLog AI Assistant — setup

Adds three things, all built on the data sources the app already uses (so every
claim stays verifiable):

1. **Ticker info drawer** — click any ticker symbol → slide-in panel with
   Google Finance / Yahoo / Finviz / SEC links, live quote + screen metrics,
   detailed fundamentals (SEC EDGAR → FMP fallback), and trending-news links.
   *No API key, no LLM — fully deterministic.*
2. **Q&A assistant** — new **Assistant** tab + floating "⛓ Ask" button. Chat
   that answers from the live screen data + published method only.
3. **Decision walkthrough** — same assistant; e.g. "I have $1,000 — walk me
   through how to think about it" runs an educational, step-by-step framework.
   It never names picks or gives advice.

## What you must set in Vercel (the assistant needs this)

Project → Settings → Environment Variables:

| Variable | Value | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | your Anthropic API key | **yes** — assistant is dark without it |
| `AGENT_MODEL` | model id (default `claude-haiku-4-5`) | optional — set to `claude-sonnet-5` for stronger answers at higher cost |

The key lives server-side only (`/api/agent`), same model as the FMP/Alpaca
proxies — the browser never sees it. Until it's set, the ticker drawer works
fully; the chat shows a clear "ANTHROPIC_API_KEY may not be set" message instead
of failing silently.

## Guardrails (enforced server-side in `/api/agent.js`)

- Educational only; explicitly **not financial advice**, never says buy/sell/hold
  or hands out allocations as a recommendation.
- Uses **only** the data the app passes in (live screen rows + the focused
  ticker's fetched fundamentals + the published method). Told never to invent a
  price, fundamental, or headline — if a figure isn't present it says so and
  points to the source. This is the "a stranger can verify every claim" standard.
- Output and conversation length are capped to bound cost/latency.

## Deploy

Push to `main` (Vercel auto-deploys). Files changed:
`api/agent.js` (new), `index.html` (drawer + chat + Assistant tab).
