/* =====================================================================
   ThePickLog — Receipt page (Vercel serverless)
   ---------------------------------------------------------------------
   A shareable, timestamped, un-fakeable "receipt" for one call:
     • a PICK  (from picks.csv + outcomes.csv), or
     • a RULE  (a registered hypothesis, from leaderboard.json).

   Route (via vercel.json rewrite):  /r/:id  ->  /api/receipt?id=:id
   Accepts:  /r/H-EX1  /r/h-EX1  /r/p-<pick_uuid>  /r/<pick_uuid>

   The card asserts nothing the public log can't confirm. Every field is
   read live from the same files the whole site runs on, and the page
   links back to them ("Verify"). North Star: a stranger who lands here
   from a screenshot can check every claim in one click.

   Note: og:image (dynamic PNG via @vercel/og) is a follow-up. For now the
   link preview carries title + description text, which is self-verifying.
   ===================================================================== */

const THEME = {
  bg: "#0c0f14", panel: "#0e1420", line: "#2a3240",
  text: "#e8e8e8", muted: "#8b98a8", a: "#1f6f6b",
  green: "#2ec27e", red: "#f0506e", amber: "#f5b14c",
};

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const pct = (v) => {
  const n = Number(v);
  if (!isFinite(n)) return "—";
  return (n > 0 ? "+" : "") + n.toFixed(1) + "%";
};

const fmtDate = (s) => {
  if (!s) return "—";
  const d = new Date(s);
  if (isNaN(d)) return String(s);
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric", timeZone: "America/New_York" });
};
const fmtDateTime = (s) => {
  if (!s) return "—";
  const d = new Date(s);
  if (isNaN(d)) return String(s);
  return d.toLocaleString("en-US", { year: "numeric", month: "short", day: "numeric", hour: "numeric", minute: "2-digit", timeZone: "America/New_York" }) + " ET";
};

/* Tolerant CSV parser (handles optional double-quoted fields). */
function parseCSV(text) {
  const rows = [];
  let row = [], field = "", inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"') { if (text[i + 1] === '"') { field += '"'; i++; } else inQ = false; }
      else field += c;
    } else {
      if (c === '"') inQ = true;
      else if (c === ",") { row.push(field); field = ""; }
      else if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
      else if (c === "\r") { /* skip */ }
      else field += c;
    }
  }
  if (field.length || row.length) { row.push(field); rows.push(row); }
  if (!rows.length) return [];
  const header = rows.shift();
  return rows.filter(r => r.length && r.some(x => x !== "")).map(r => {
    const o = {};
    header.forEach((h, i) => { o[h] = r[i]; });
    return o;
  });
}

async function getText(base, path) {
  const r = await fetch(`${base}/${path}`, { headers: { "cache-control": "no-cache" } });
  if (!r.ok) throw new Error(`${path} ${r.status}`);
  return r.text();
}
async function getJSON(base, path) { return JSON.parse(await getText(base, path)); }

function page({ title, desc, url, bodyHTML, immutable }) {
  const cache = immutable
    ? "public, s-maxage=86400, stale-while-revalidate=604800"
    : "public, s-maxage=120, stale-while-revalidate=600";
  const image = `${url}/og.png`;
  return { cache, html: `<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)} · ThePickLog</title>
<meta name="description" content="${esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="ThePickLog">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(desc)}">
<meta property="og:url" content="${esc(url)}">
<meta property="og:image" content="${esc(image)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(desc)}">
<meta name="twitter:image" content="${esc(image)}">
<style>
  :root{--bg:${THEME.bg};--panel:${THEME.panel};--line:${THEME.line};--text:${THEME.text};--muted:${THEME.muted};--a:${THEME.a};--green:${THEME.green};--red:${THEME.red};--amber:${THEME.amber}}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    display:flex;flex-direction:column;align-items:center;padding:28px 16px 40px}
  a{color:var(--a)}
  .card{width:100%;max-width:600px;background:var(--panel);border:1px solid var(--line);border-radius:18px;overflow:hidden}
  .hd{display:flex;align-items:center;gap:8px;padding:16px 20px;border-bottom:1px solid var(--line);font-weight:700}
  .hd .site{color:var(--muted);font-weight:600;font-size:13px;margin-left:2px}
  .badge{margin-left:auto;font-size:11px;font-weight:800;letter-spacing:.08em;padding:4px 10px;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
  .bd{padding:20px}
  .claim{font-size:26px;font-weight:800;margin:2px 0 4px}
  .claim .sub{display:block;font-size:14px;font-weight:600;color:var(--muted);margin-top:4px}
  .stamps{display:flex;gap:22px;margin:18px 0 6px;flex-wrap:wrap}
  .stamp .k{font-size:11px;letter-spacing:.06em;color:var(--muted);text-transform:uppercase}
  .stamp .v{font-size:15px;font-weight:700}
  .frozen-note{font-size:12.5px;color:var(--muted);margin:6px 0 4px}
  .chip{display:inline-block;font-size:12px;font-weight:800;letter-spacing:.05em;padding:4px 12px;border-radius:999px;margin:12px 0 2px}
  .chip.win{background:#12271d;color:var(--green);border:1px solid #1e4433}
  .chip.miss{background:#2a1319;color:var(--red);border:1px solid #4a2028}
  .chip.live{background:#2a2410;color:var(--amber);border:1px solid #5a4a22}
  .chip.graded{background:#10202e;color:#5aa0ff;border:1px solid #24405a}
  .hero-num{font-size:40px;font-weight:800;margin:14px 0 2px;line-height:1.05}
  .hero-num .hero-lab{display:block;font-size:12.5px;font-weight:600;color:var(--muted);margin-top:4px}
  .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:16px 0 4px}
  .cell{background:#0b1119;border:1px solid var(--line);border-radius:12px;padding:12px}
  .cell .k{font-size:11px;color:var(--muted)}
  .cell .v{font-size:20px;font-weight:800;margin-top:3px}
  .pos{color:var(--green)}.neg{color:var(--red)}
  .row{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-top:1px solid var(--line);font-size:14px}
  .row .k{color:var(--muted)}
  .baseline{font-size:13px;color:var(--muted);margin-top:10px}
  .ft{padding:14px 20px;border-top:1px solid var(--line);display:flex;gap:10px;flex-wrap:wrap;align-items:center}
  .btn{display:inline-block;background:var(--a);color:#fff;text-decoration:none;font-weight:700;font-size:14px;padding:9px 16px;border-radius:10px}
  .btn.ghost{background:transparent;border:1px solid var(--line);color:var(--text)}
  .disc{max-width:600px;font-size:12px;color:var(--muted);margin:14px 4px 0;text-align:center}
  .ns{font-size:12px;color:var(--amber);margin-top:8px}
</style></head><body>
${bodyHTML}
<p class="disc">Simulated (paper) trading · research, not investment advice. Nothing here is a recommendation to buy or sell any security. Many names studied are low-float microcaps that are volatile and illiquid.</p>
</body></html>`};
}

function chipFor(state) {
  const s = String(state || "").toLowerCase();
  if (s === "win") return `<span class="chip win">✅ WIN</span>`;
  if (s === "miss") return `<span class="chip miss">✕ MISS</span>`;
  if (s === "live") return `<span class="chip live">◷ LIVE — grading pending</span>`;
  return `<span class="chip graded">GRADED</span>`;
}

/* ---- PICK receipt ------------------------------------------------- */
function renderPick(pick, oc, base, url) {
  const graded = oc && oc.graded_at;
  const won = graded && String(oc.win) === "1";
  const state = !graded ? "live" : (won ? "win" : "miss");
  const ticker = pick.ticker || oc?.ticker || "—";
  const rule = `low-float ignition · tier ${esc(pick.tier || "?")} · score ${esc(pick.score || "?")}`;

  const cls = (n) => (n > 0 ? "pos" : n < 0 ? "neg" : "");
  let outcome = "";
  if (graded) {
    const sameday = Number(oc.ret_open_close_net);
    const peak = Number(oc.mfe_5d), close5 = Number(oc.ret_open_5dclose_net), dip = Number(oc.mae_5d);
    outcome = `
      <div class="hero-num ${cls(sameday)}">${pct(sameday)}<span class="hero-lab">same-day open→close (net 2% haircut) — the graded result</span></div>
      <div class="grid">
        <div class="cell"><div class="k">Peaked at (5d)</div><div class="v ${cls(peak)}">${pct(peak)}</div></div>
        <div class="cell"><div class="k">If held 5 days</div><div class="v ${cls(close5)}">${pct(close5)}</div></div>
        <div class="cell"><div class="k">Worst dip (5d)</div><div class="v ${cls(dip)}">${pct(dip)}</div></div>
      </div>
      <div class="baseline">Peak is the best it ever touched — not what you'd have kept. The full 5-day path is shown so nothing's cherry-picked.</div>`;
  } else {
    outcome = `<div class="baseline">This call is frozen and waiting to be graded. Check back after the 5-day window — the result posts here automatically, win or lose.</div>`;
  }

  const title = graded
    ? `${ticker}: ${pct(oc.ret_open_close_net)} same-day (peaked ${pct(oc.mfe_5d)}, then faded to ${pct(oc.ret_open_5dclose_net)} by day 5)`
    : `${ticker}: a call frozen ${fmtDate(pick.published_at)}, grading pending`;
  const desc = graded
    ? `Frozen ${fmtDate(pick.published_at)} before the result — nobody can edit it. Same-day ${pct(oc.ret_open_close_net)}; peaked ${pct(oc.mfe_5d)}, worst dip ${pct(oc.mae_5d)}, ${pct(oc.ret_open_5dclose_net)} if held 5 days. Verify it against the public log.`
    : `Frozen ${fmtDate(pick.published_at)} before the outcome is known. Watch it get graded in the open on ThePickLog.`;

  const body = `
  <div class="card">
    <div class="hd">⛓ ThePickLog <span class="site">thepicklog.com</span> <span class="badge">PICK</span></div>
    <div class="bd">
      <div class="claim">${esc(ticker)}<span class="sub">${rule}</span></div>
      <div class="stamps">
        <div class="stamp"><div class="k">Frozen</div><div class="v">${fmtDateTime(pick.published_at)}</div></div>
        <div class="stamp"><div class="k">Graded</div><div class="v">${graded ? fmtDate(oc.graded_at) : "—"}</div></div>
      </div>
      <div class="frozen-note">Frozen before the result. Nobody can edit this.</div>
      ${chipFor(state)}
      ${outcome}
    </div>
    <div class="ft">
      <a class="btn" href="${esc(base)}/picks.csv">Check the log →</a>
      <a class="btn ghost" href="${esc(base)}/#proof">See the full record</a>
    </div>
  </div>`;
  return page({ title, desc, url, bodyHTML: body, immutable: !!graded });
}

/* ---- HYPOTHESIS (RULE) receipt ------------------------------------ */
function renderHyp(row, lb, base, url) {
  const delta = Number(row.delta_post);
  const cls = (n) => (n > 0 ? "pos" : n < 0 ? "neg" : "");
  const state = String(row.state || "").toLowerCase() === "maturing" ? "live" : "graded";
  const ci = Array.isArray(row.ci95) ? `[${pct(row.ci95[0])}, ${pct(row.ci95[1])}]` : "—";
  // Use the rule-specific baseline so avg / baseline / Δ reconcile
  // (exit rules are compared to the same picks' same-day close, which differs
  // from the global baseline). Fall back to the global baseline if absent.
  const baseAvg = (row.baseline_avg_post != null) ? row.baseline_avg_post : lb?.baseline?.avg_post;

  const title = `Rule: ${row.title} — beats baseline by ${pct(row.delta_post)} so far`;
  const desc = `Registered ${fmtDate(row.registered_at)}, graded out-of-sample only on picks logged after. ${row.n_post} picks, ${row.win_post}% win, expectancy ${pct(row.avg_post)} vs baseline ${pct(baseAvg)} (Δ ${pct(row.delta_post)}). ${row.significant ? "Interval clears zero." : "Directional, not proven — interval still spans zero."}`;

  const body = `
  <div class="card">
    <div class="hd">⛓ ThePickLog <span class="site">thepicklog.com</span> <span class="badge">RULE</span></div>
    <div class="bd">
      <div class="claim">${esc(row.title)}<span class="sub">${esc(row.rule_str || "")} · by ${esc(row.author || "—")}</span></div>
      <div class="stamps">
        <div class="stamp"><div class="k">Registered</div><div class="v">${fmtDate(row.registered_at)}</div></div>
        <div class="stamp"><div class="k">Graded through</div><div class="v">${fmtDate(lb?.generated_at)}</div></div>
      </div>
      <div class="frozen-note">Frozen before the picks it's judged on. Only picks logged after registration count.</div>
      ${chipFor(state)}
      <div class="grid">
        <div class="cell"><div class="k">Out-of-sample picks</div><div class="v">${esc(row.n_post)}</div></div>
        <div class="cell"><div class="k">Win rate</div><div class="v">${esc(row.win_post)}%</div></div>
        <div class="cell"><div class="k">Δ vs baseline</div><div class="v ${cls(delta)}">${pct(row.delta_post)}</div></div>
      </div>
      <div class="row"><span class="k">Expectancy (this rule)</span><span class="${cls(Number(row.avg_post))}">${pct(row.avg_post)}</span></div>
      <div class="row"><span class="k">Baseline (same picks, same-day close)</span><span>${pct(baseAvg)}</span></div>
      <div class="row"><span class="k">95% interval on the edge</span><span>${ci}</span></div>
      ${row.significant ? "" : `<div class="ns">Directional, not proven — the 95% interval still spans zero.</div>`}
    </div>
    <div class="ft">
      <a class="btn" href="${esc(base)}/dashboard.html#verify=${encodeURIComponent(JSON.stringify(row.rule_spec || {}))}">Re-derive this rule →</a>
      <a class="btn ghost" href="${esc(base)}/#proof">See the full board</a>
    </div>
  </div>`;
  return page({ title, desc, url, bodyHTML: body, immutable: false });
}

/* ---- handler ------------------------------------------------------ */
export default async function handler(req, res) {
  const proto = (req.headers["x-forwarded-proto"] || "https").split(",")[0];
  const host = (req.headers["x-forwarded-host"] || req.headers.host || "thepicklog.vercel.app").split(",")[0];
  const base = `${proto}://${host}`;

  let raw = String((req.query && req.query.id) || "").trim();
  if (!raw) return res.status(400).send("Missing receipt id.");
  const url = `${base}/r/${encodeURIComponent(raw)}`;
  // strip an optional type prefix (p-/c-/h-) but keep the rest intact
  const cleaned = raw.replace(/^([pch])-/i, "");

  try {
    // 1) hypothesis match (leaderboard row id, case-insensitive)
    const lb = await getJSON(base, "leaderboard.json").catch(() => null);
    if (lb && Array.isArray(lb.rows)) {
      const row = lb.rows.find(r =>
        String(r.id).toLowerCase() === raw.toLowerCase() ||
        String(r.id).toLowerCase() === cleaned.toLowerCase());
      if (row) {
        const out = renderHyp(row, lb, base, url);
        res.setHeader("content-type", "text/html; charset=utf-8");
        res.setHeader("cache-control", out.cache);
        return res.status(200).send(out.html);
      }
    }
    // 2) pick match (pick_id in picks.csv)
    const picks = parseCSV(await getText(base, "picks.csv"));
    const pick = picks.find(p => p.pick_id === raw || p.pick_id === cleaned);
    if (pick) {
      const outcomes = parseCSV(await getText(base, "outcomes.csv").catch(() => ""));
      const oc = outcomes.find(o => o.pick_id === pick.pick_id) || null;
      const out = renderPick(pick, oc, base, url);
      res.setHeader("content-type", "text/html; charset=utf-8");
      res.setHeader("cache-control", out.cache);
      return res.status(200).send(out.html);
    }
    res.setHeader("content-type", "text/html; charset=utf-8");
    return res.status(404).send(`<!doctype html><meta charset="utf-8"><body style="background:${THEME.bg};color:${THEME.text};font-family:sans-serif;text-align:center;padding:60px 20px"><h1>Receipt not found</h1><p style="color:${THEME.muted}">No call with id <code>${esc(raw)}</code> in the public log. <a style="color:${THEME.a}" href="${esc(base)}/">Go to ThePickLog →</a></p></body>`);
  } catch (e) {
    return res.status(502).send("Receipt render failed: " + esc(e.message));
  }
}
