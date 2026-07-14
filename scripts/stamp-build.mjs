// Build-stamp injector — runs during the Vercel build.
// Replaces the __BUILDSTAMP__ token in the footers with the real commit SHA
// and the deploy time, so the live footer always reflects the deployed version.
// Defensive by design: never throws, never fails the build.
import { readFileSync, writeFileSync } from 'node:fs';

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
