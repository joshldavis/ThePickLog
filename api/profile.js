/* =====================================================================
   ThePickLog — Public profile board (Vercel serverless)
   ---------------------------------------------------------------------
   /u/:handle -> /api/profile?handle=:handle  (via vercel.json rewrite)

   Shows every rule a handle has on the public board (from leaderboard.json,
   matched on the `author` field), with each rule's honest out-of-sample
   record and a link to its shareable receipt. One page = a person's whole
   verifiable track record. Nothing here isn't already on the board.
   ===================================================================== */

const THEME = {
  bg: "#0c0f14", panel: "#0e1420", line: "#2a3240",
  text: "#e8e8e8", muted: "#8b98a8", a: "#1f6f6b",
  green: "#2ec27e", red: "#f0506e", amber: "#f5b14c", blue: "#5aa0ff",
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
  return isNaN(d) ? String(s) : d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric", timeZone: "America/New_York" });
};
const cls = (n) => (Number(n) > 0 ? "pos" : Number(n) < 0 ? "neg" : "");

async function getJSON(base, path) {
  const r = await fetch(`${base}/${path}`, { headers: { "cache-control": "no-cache" } });
  if (!r.ok) throw new Error(`${path} ${r.status}`);
  return r.json();
}

export default async function handler(req, res) {
  const proto = (req.headers["x-forwarded-proto"] || "https").split(",")[0];
  const host = (req.headers["x-forwarded-host"] || req.headers.host || "thepicklog.vercel.app").split(",")[0];
  const base = `${proto}://${host}`;

  const handle = String((req.query && req.query.handle) || "").trim();
  if (!handle) return res.status(400).send("Missing handle.");
  const url = `${base}/u/${encodeURIComponent(handle)}`;

  let lb;
  try { lb = await getJSON(base, "leaderboard.json"); }
  catch (e) { return res.status(502).send("Profile load failed: " + esc(e.message)); }

  const rows = (lb.rows || []).filter(r =>
    String(r.author || "").toLowerCase() === handle.toLowerCase());

  const label = handle.toLowerCase() === "house" ? "ThePickLog (house rules)" : "@" + handle;

  if (!rows.length) {
    res.setHeader("content-type", "text/html; charset=utf-8");
    return res.status(404).send(`<!doctype html><meta charset="utf-8"><body style="background:${THEME.bg};color:${THEME.text};font-family:sans-serif;text-align:center;padding:60px 20px"><h1>No public rules yet</h1><p style="color:${THEME.muted}">${esc(label)} has no rules on the board yet. Rules appear here once they're registered and start getting graded. <a style="color:${THEME.a}" href="${esc(base)}/#compete">Put one on the board →</a></p></body>`);
  }

  const nBeat = rows.filter(r => Number(r.delta_post) > 0).length;
  const nSig = rows.filter(r => r.significant).length;
  const best = rows.reduce((m, r) => Number(r.delta_post) > Number(m.delta_post) ? r : m, rows[0]);
  const baseAvg = lb?.baseline?.avg_post;

  const title = `${label} on ThePickLog — ${rows.length} rule${rows.length > 1 ? "s" : ""} on the record`;
  const desc = `${nBeat} of ${rows.length} beat the baseline out-of-sample; ${nSig} clear the 95% bar. Best edge: ${pct(best.delta_post)} (${best.title}). Every number verifiable against the public log.`;

  const rowsHTML = rows
    .sort((a, b) => Number(b.delta_post) - Number(a.delta_post))
    .map(r => {
      const ci = Array.isArray(r.ci95) ? `[${pct(r.ci95[0])}, ${pct(r.ci95[1])}]` : "—";
      const flag = r.significant ? `<span class="tag ok">clears 95%</span>` : `<span class="tag ns">directional</span>`;
      const stabTag = (r.stability === "stable" || r.stability === "mixed") ? ` <span class="tag ${r.stability === "stable" ? "ok" : "ns"}">sign ${esc(r.stability)}</span>` : "";
      const kindTag = r.kind === "question" ? `<span class="tag q">question</span> ` : "";
      return `<tr>
        <td class="l">${kindTag}<b>${esc(r.id)}</b> · ${esc(r.title)}<div class="rule">${esc(r.rule_str || "")} · reg ${fmtDate(r.registered_at)}</div></td>
        <td class="num">${esc(r.n_post)}</td>
        <td class="num">${esc(r.win_post)}%</td>
        <td class="num ${cls(r.delta_post)}">${pct(r.delta_post)}<div class="ci">${ci}</div></td>
        <td>${flag}${stabTag}</td>
        <td><a class="rcpt" href="${esc(base)}/r/${encodeURIComponent(r.id)}" target="_blank" rel="noopener">receipt ↗</a></td>
      </tr>`;
    }).join("");

  const html = `<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
<meta property="og:type" content="profile">
<meta property="og:site_name" content="ThePickLog">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(desc)}">
<meta property="og:url" content="${esc(url)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(desc)}">
<style>
  :root{--bg:${THEME.bg};--panel:${THEME.panel};--line:${THEME.line};--text:${THEME.text};--muted:${THEME.muted};--a:${THEME.a};--green:${THEME.green};--red:${THEME.red};--amber:${THEME.amber};--blue:${THEME.blue}}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    display:flex;flex-direction:column;align-items:center;padding:28px 16px 44px}
  a{color:var(--a)}
  .wrap{width:100%;max-width:760px}
  .hd{display:flex;align-items:center;gap:8px;font-weight:700;margin-bottom:18px}
  .hd .site{color:var(--muted);font-weight:600;font-size:13px}
  .name{font-size:30px;font-weight:800;margin:2px 0 2px}
  .sub{color:var(--muted);font-size:14px;margin-bottom:18px}
  .cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:22px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}
  .card .k{font-size:12px;color:var(--muted)}
  .card .v{font-size:28px;font-weight:800;margin-top:4px}
  table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden}
  th,td{padding:12px 14px;text-align:left;border-top:1px solid var(--line);vertical-align:top;font-size:14px}
  th{color:var(--muted);font-size:11px;letter-spacing:.05em;text-transform:uppercase;border-top:0}
  td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
  .rule{color:var(--muted);font-size:12px;margin-top:3px}
  .ci{color:var(--muted);font-size:11px}
  .pos{color:var(--green)}.neg{color:var(--red)}
  .tag{font-size:11px;font-weight:700;padding:3px 9px;border-radius:999px;white-space:nowrap}
  .tag.ok{color:var(--blue);background:#10202e;border:1px solid #24405a}
  .tag.ns{color:var(--amber);background:#2a1d10;border:1px solid #5a3a22}
  .tag.q{color:#c99bff;background:#241a33;border:1px solid #4a3a6a}
  .rcpt{font-weight:600;font-size:13px;white-space:nowrap}
  .base{color:var(--muted);font-size:13px;margin:14px 2px}
  .ft{margin-top:18px;display:flex;gap:10px;flex-wrap:wrap}
  .btn{display:inline-block;background:var(--a);color:#fff;text-decoration:none;font-weight:700;font-size:14px;padding:9px 16px;border-radius:10px}
  .btn.ghost{background:transparent;border:1px solid var(--line);color:var(--text)}
  .disc{font-size:12px;color:var(--muted);margin:18px 2px 0}
</style></head><body>
<div class="wrap">
  <div class="hd">⛓ ThePickLog <span class="site">thepicklog.com</span></div>
  <div class="name">${esc(label)}</div>
  <div class="sub">Every rule this ${handle.toLowerCase() === "house" ? "site runs" : "player has put"} on the public board, graded out-of-sample. Nothing added, nothing deleted.</div>
  <div class="cards">
    <div class="card"><div class="k">Rules on the board</div><div class="v">${rows.length}</div></div>
    <div class="card"><div class="k">Beat the baseline</div><div class="v">${nBeat}<span style="font-size:15px;color:var(--muted)">/${rows.length}</span></div></div>
    <div class="card"><div class="k">Clear 95% bar</div><div class="v ${nSig ? "pos" : ""}">${nSig}</div></div>
  </div>
  <table>
    <thead><tr><th>Rule</th><th class="num">OOS n</th><th class="num">Win%</th><th class="num">Δ vs base</th><th>Signal</th><th></th></tr></thead>
    <tbody>${rowsHTML}</tbody>
  </table>
  <div class="base">Baseline (same picks, same-day close): <b>${pct(baseAvg)}</b>. "Δ vs base" is out-of-sample, on picks logged after each rule was registered. <b>directional</b> = the 95% interval still spans zero — not proven yet.</div>
  <div class="ft">
    <a class="btn" href="${esc(base)}/#compete">Put your own rule on the board →</a>
    <a class="btn ghost" href="${esc(base)}/#proof">See the full board</a>
  </div>
  <p class="disc">Simulated (paper) trading · research, not investment advice. Every figure re-derives from the public pick log. Past results do not predict future returns.</p>
</div>
</body></html>`;

  res.setHeader("content-type", "text/html; charset=utf-8");
  res.setHeader("cache-control", "public, s-maxage=300, stale-while-revalidate=1800");
  return res.status(200).send(html);
}
