/**
 * promptfoo provider that runs the real assistant handler (api/agent.js) with
 * a fake request and response, so the suite tests the real SYSTEM prompt,
 * DATA block, caps and reply clean-up rather than a copy of them.
 *
 * Each provider entry pins one model. agent.js reads AGENT_MODEL once, when the
 * module loads, so the handler is imported once per model (a query string on
 * the import URL gives each model its own copy of the module). The model
 * "default" means AGENT_MODEL unset: whatever default agent.js ships with.
 *
 * Offline dry runs only: when EVALS_MOCK_URL is set (it must point at
 * 127.0.0.1 or localhost), calls to https://api.anthropic.com are sent to that
 * mock instead. Nothing in api/ changes; see evals/README.md.
 */

const AGENT_URL = new URL("../api/agent.js", import.meta.url).href;
const ANTHROPIC_ORIGIN = "https://api.anthropic.com";

function redirectToMock() {
  const mock = (process.env.EVALS_MOCK_URL || "").trim().replace(/\/+$/, "");
  if (!mock || globalThis.__picklogEvalFetchPatched) return;
  const { protocol, hostname } = new URL(mock);
  if (protocol !== "http:" || !["127.0.0.1", "localhost"].includes(hostname))
    throw new Error("EVALS_MOCK_URL must be http://127.0.0.1:<port> or http://localhost:<port>");
  const realFetch = globalThis.fetch;
  globalThis.fetch = (input, init) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    if (url.startsWith(ANTHROPIC_ORIGIN + "/")) return realFetch(mock + url.slice(ANTHROPIC_ORIGIN.length), init);
    return realFetch(input, init);
  };
  globalThis.__picklogEvalFetchPatched = true;
}

const handlers = new Map();
async function loadHandler(model) {
  if (!handlers.has(model)) {
    if (model === "default") delete process.env.AGENT_MODEL;
    else process.env.AGENT_MODEL = model;
    const mod = await import(`${AGENT_URL}?model=${encodeURIComponent(model)}`);
    handlers.set(model, mod.default);
  }
  return handlers.get(model);
}

function fakeRes() {
  return {
    statusCode: 200,
    body: undefined,
    status(code) { this.statusCode = code; return this; },
    json(obj) { this.body = obj; return this; },
  };
}

const parse = (v) => (typeof v === "string" ? JSON.parse(v) : v);

export default class PickLogAgentProvider {
  constructor(options = {}) {
    const cfg = options.config || {};
    const fromEnv = cfg.modelEnv ? process.env[cfg.modelEnv] : undefined;
    this.model = String(cfg.model || fromEnv || "").trim();
  }

  id() {
    return `picklog-agent:${this.model || "unset"}`;
  }

  async callApi(_prompt, context) {
    if (!this.model) return { error: "No model pinned. Set BASELINE_MODEL / CANDIDATE_MODEL (see evals/README.md)." };
    const vars = (context && context.vars) || {};
    const messages = vars.messages
      ? parse(vars.messages)
      : [{ role: "user", content: String(vars.question ?? "") }];
    try {
      redirectToMock();
      const handler = await loadHandler(this.model);
      const res = fakeRes();
      await handler({ method: "POST", body: { messages, context: vars.context ?? "" } }, res);
      const out = res.body || {};
      if (res.statusCode !== 200)
        return { error: `api/agent.js answered ${res.statusCode}: ${JSON.stringify(out).slice(0, 400)}` };
      const u = out.usage || {};
      return {
        output: out.reply,
        metadata: { model: out.model },
        tokenUsage: {
          prompt: u.input_tokens || 0,
          completion: u.output_tokens || 0,
          total: (u.input_tokens || 0) + (u.output_tokens || 0),
        },
      };
    } catch (e) {
      return { error: e instanceof Error ? e.message : String(e) };
    }
  }
}
