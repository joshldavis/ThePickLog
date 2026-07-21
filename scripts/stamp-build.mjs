// Build-stamp injector — runs during the Vercel build.
// Replaces the __BUILDSTAMP__ token in the footers with the real commit SHA
// and the deploy time, so the live footer always reflects the deployed version.
// Defensive by design: never throws, never fails the build.
import { readFileSync, writeFileSync, readdirSync, unlinkSync } from 'node:fs';

const sha = (process.env.VERCEL_GIT_COMMIT_SHA || '').slice(0, 7) || 'dev';

let when = 'unknown time';
try {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/New_York',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: false,
  }).format(new Date());          // e.g. "2026-07-14, 08:15"
  when = parts.replace(',', '') + ' ET';
} catch (e) {
  console.log('stamp: time format failed:', e.message);
}

const stamp = `${when} · ${sha}`;
const files = ['index.html', 'guide.html', 'trust.html'];

for (const f of files) {
  try {
    const s = readFileSync(f, 'utf8');
    if (s.includes('__BUILDSTAMP__')) {
      writeFileSync(f, s.split('__BUILDSTAMP__').join(stamp));
      console.log(`stamp: ${f} -> ${stamp}`);
    } else {
      console.log(`stamp: no token in ${f} (left as-is)`);
    }
  } catch (e) {
    console.log(`stamp: skip ${f}: ${e.message}`);
  }
}

// ---- Prune internal docs from the deployed output ----------------------------
// outputDirectory is ".", so root-level Markdown files removed here are simply
// not served (they remain in git). ALLOWLIST = docs intentionally linked from the
// site; every other root-level *.md is internal and must not be publicly
// fetchable. Allowlist-based on purpose: a future internal .md is excluded by
// default. Defensive: never throws, never fails the build. Only touches the repo
// root — reports/*.md and any subdirectory Markdown are left untouched.
const PUBLIC_DOCS = new Set([
  'HYPOTHESES.md',
  'MONETIZATION-GATE.md',
  'ThePickLog-Domain-Coverage-Spec-2026-07-06.md',
  'ThePickLog-Empirical-Validity-Studies-2026-07-07.md',
  'ThePickLog-Generalizability-and-Consequential-2026-07-07.md',
  'ThePickLog-Structural-Justification-2026-07-06.md',
  'ThePickLog-Validity-Dossier-UG15-2026-07-07.md',
  'ThePickLog-Validity-Framework-Messick-2026-07-06.md',
]);
try {
  for (const f of readdirSync('.')) {
    if (f.endsWith('.md') && !PUBLIC_DOCS.has(f)) {
      try {
        unlinkSync(f);
        console.log(`prune: removed internal doc ${f}`);
      } catch (e) {
        console.log(`prune: skip ${f}: ${e.message}`);
      }
    }
  }
} catch (e) {
  console.log('prune: skipped:', e.message);
}
