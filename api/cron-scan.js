/* =====================================================================
   ThePickLog — external scan trigger (Vercel Cron → GitHub workflow_dispatch)
   ---------------------------------------------------------------------
   WHY THIS EXISTS

   GitHub's scheduled-workflow dispatcher is best-effort, and from 2026-08-27
   it delivered this repo's scan trigger 4-10 HOURS late every single day.
   Five sessions were lost that way (08-27, 08-28, 08-31, 09-01, 09-02): the
   pre-open gate correctly refused to log a cohort after the opening bell, and
   a pick written down after the bell was never a forecast, so those sessions
   can never be backfilled.

   The first fix assumed dispatches were being DROPPED and added a redundant
   cron an hour earlier. The data disproved that: every dispatch fires, they
   are simply all delayed by the same amount. Redundancy was the wrong axis —
   margin is the right one — and a second scheduler reading the same broken
   clock cannot help. A DIFFERENT clock can.

   Vercel Cron on Hobby is documented at per-hour precision: a job scheduled
   for 11:00 UTC fires between 11:00 and 11:59. That lands 07:00-07:59 ET,
   comfortably inside the scanner's 06:00 ET floor and 09:20 ET cutoff — a
   3h20m window against 59 minutes of jitter. The GitHub crons stay in place
   as a backup; the workflow's same-day idempotency guard turns whichever
   trigger arrives second into a clean no-op, so belt and braces costs nothing.

   WHAT THIS DOES NOT DO

   It only ASKS GitHub to run the scan. Every integrity rule — trading-day
   check, 06:00 ET floor, 09:20 ET cutoff, same-day idempotency — still lives
   in the workflow and in ignitionscan.py, where it is version-controlled and
   auditable by a stranger. Moving the trigger does not move the guarantees,
   and this endpoint cannot cause a late cohort to be logged even if it fires
   at the wrong time or is called by someone else.

   REQUIRED ENV VARS (Vercel → Project → Settings → Environment Variables):

     GITHUB_DISPATCH_TOKEN   Fine-grained personal access token, scoped to the
                             single repo joshldavis/thepicklog, with exactly one
                             permission: Actions → Read and write. Nothing else.
     CRON_SECRET             Any long random string. Vercel automatically sends
                             it as `Authorization: Bearer <CRON_SECRET>` on cron
                             invocations, and we reject anything that does not
                             match, so this is not a public "run a scan" button.

   Both are required. If either is missing the endpoint fails loudly with 500
   rather than silently doing nothing — a trigger that quietly stops firing is
   the failure mode this whole exercise exists to eliminate.
   ===================================================================== */

const OWNER = "joshldavis";
const REPO = "thepicklog";
const WORKFLOW = "ignitionscan.yml";

export default async function handler(req, res) {
  const secret = process.env.CRON_SECRET;
  const token = process.env.GITHUB_DISPATCH_TOKEN;

  const missing = [
    !token && "GITHUB_DISPATCH_TOKEN",
    !secret && "CRON_SECRET",
  ].filter(Boolean);
  if (missing.length) {
    return res.status(500).json({ ok: false, error: "not configured", missing });
  }

  if (req.headers.authorization !== `Bearer ${secret}`) {
    return res.status(401).json({ ok: false, error: "unauthorized" });
  }

  const url = `https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/dispatches`;
  let r;
  let body = "";
  try {
    r = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "thepicklog-cron",
      },
      body: JSON.stringify({ ref: "main", inputs: { command: "scan" } }),
    });
    body = await r.text();
  } catch (e) {
    return res.status(502).json({ ok: false, error: "dispatch request failed", detail: String(e) });
  }

  // 204 No Content is the documented success response for workflow_dispatch.
  const ok = r.status === 204;
  return res.status(ok ? 200 : 502).json({
    ok,
    dispatched_at: new Date().toISOString(),
    github_status: r.status,
    detail: ok ? "scan dispatched" : body.slice(0, 500),
  });
}
