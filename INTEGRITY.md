# ThePickLog — Integrity & Resilience

Three safety layers protect the forward log (`picks.csv`, `outcomes.csv`, `paths.csv`) —
the record the entire verifiability claim rests on. Added 2026-07-06.

---

## 1. Tamper-evident hash chain — `log_integrity.py`

Every scan, grade, and weekly report seals a row into `integrity_ledger.csv`: the
SHA-256 of each log file plus a running **chain hash** that folds in the previous
row. Editing any historical file, or any past ledger row, breaks the chain from
that point forward — and the break is provable, not just suspicious.

**Chain definition** (so anyone can reproduce it):

```
file_sha  = sha256(raw bytes of the file)            # literal "MISSING" if absent
genesis    prev_chain = "0" * 64
chain      = sha256( prev_chain | picks_sha | outcomes_sha | paths_sha | ts | event )
             # "|" is a literal pipe; fields UTF-8 encoded
```

**Anyone can verify the whole history in one command** (serves the north star —
a stranger can confirm the record was never quietly rewritten):

```
python log_integrity.py --verify        # recompute the chain; exits 1 on any break
python log_integrity.py --verify-head   # also confirm current files match the last seal
```

The genesis row was sealed 2026-07-06 over the then-current log
(254 picks / 180 outcomes / 601 path rows).

---

## 2. Offsite backup — GitHub artifacts

Both workflows upload `picks/outcomes/paths.csv`, `leaderboard.json`, and
`integrity_ledger.csv` as a **GitHub Actions artifact** on every run. These live in
GitHub's artifact store, **independent of git history**, so they survive a force-push,
a bad rebase, or a repo compromise. Retention: 90 days (adjust `retention-days`).

Download: repo → **Actions** → any run → **Artifacts**.

**Stronger upgrades (optional, when this matters more):**
- Push the same files to a second **private repo** or an **S3 bucket** on each run
  (needs one secret: a PAT or AWS keys). Gives >90-day, off-GitHub durability.
- The hash chain makes any store tamper-*evident*, so even a public mirror is safe.

---

## 3. Dead-man's-switch — two independent alerts

**a. Native watchdog — `watchdog.yml` (already active, no setup).**
Runs daily. If the forward log hasn't been committed in ≥ 4 days (longest legit
weekday gap is Fri→Mon = 3), it opens a GitHub **issue** and comments daily until
data flows again, then auto-closes. Uses the built-in `GITHUB_TOKEN` — no secret.
Catches the #1 silent failure: **GitHub auto-disables scheduled workflows after 60
days of repo inactivity.**

**b. healthchecks.io ping — push email/SMS alert (needs a free secret).**
Each successful run pings a monitor URL. If a run is skipped, disabled, or errors,
the ping stops and healthchecks.io notifies you. Setup:

1. Create a free account at healthchecks.io.
2. New check for the **daily** job → period **1 day**, grace **1 day**. Copy its ping URL.
   Repo → **Settings → Secrets and variables → Actions → New secret**:
   `HEALTHCHECK_URL` = that URL.
3. New check for the **weekly** report → period **7 days**, grace **1 day**.
   Add secret `HEALTHCHECK_URL_WEEKLY` = its URL.
4. Add your email/SMS/Slack as the notification channel.

Until the secrets are set, the workflow just logs "inactive" and continues — nothing breaks.

---

## Related secret already referenced

`VERCEL_DEPLOY_HOOK` (Vercel → Project → Settings → Git → Deploy Hooks) — fires a
deploy after each push, covering the occasional skipped GitHub→Vercel webhook.

---

## Note on push identity (item 4, "move off the Mac")

The **automated** daily/weekly/watchdog jobs already run entirely on GitHub's
servers and commit via the built-in Actions token authored as
`joshldavis <davis1163@gmail.com>` — no Mac involved, no personal token.
The only thing still routed through the Mac (osascript git) is **manual** pushes of
code changes. If you want those off the Mac too, push over HTTPS with a GitHub PAT
or `gh auth`, or open PRs from a second machine — but that's a convenience upgrade,
not a resilience gap: the unattended record-keeping no longer depends on your laptop.
