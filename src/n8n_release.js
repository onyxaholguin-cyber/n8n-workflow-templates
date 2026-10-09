// Compare n8n GitHub releases with the version you run; list newer stable releases.
function parseV(s) { const m = String(s || '').match(/(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?/); return m ? { v: [+m[1], +m[2], +m[3]], pre: m[4] || '' } : null; }
function cmp(a, b) { for (let i = 0; i < 3; i++) if (a.v[i] !== b.v[i]) return a.v[i] - b.v[i]; return 0; }
function releaseReport(releases, cfg) {
  const cur = parseV(cfg.currentVersion);
  if (!cur) throw new Error('Set currentVersion to the n8n version you run, e.g. 2.40.6');
  const seen = parseV(cfg.lastNotified || '');
  const stable = (Array.isArray(releases) ? releases : [])
    .filter((r) => !r.draft && !r.prerelease)
    .map((r) => ({ r, p: parseV(r.tag_name || r.name) }))
    .filter((x) => x.p && !x.p.pre && /^n8n@|^v?\d/.test(String(x.r.tag_name || '')));
  const newer = stable.filter((x) => cmp(x.p, cur) > 0).sort((a, b) => cmp(b.p, a.p));
  if (!newer.length) return { newer: [], latest: null, text: '', notify: false };
  const latest = newer[0];
  const notify = !seen || cmp(latest.p, seen) > 0;
  const majorJump = latest.p.v[0] > cur.v[0];
  const minors = new Set(newer.map((x) => x.p.v[0] + '.' + x.p.v[1])).size;
  const lines = newer.slice(0, 8).map((x) => `• ${x.p.v.join('.')} (${String(x.r.published_at || '').slice(0, 10)}) ${x.r.html_url || ''}`);
  const text = `New n8n release${newer.length > 1 ? 's' : ''}: you run ${cur.v.join('.')}, latest stable is ${latest.p.v.join('.')} (${newer.length} newer release${newer.length > 1 ? 's' : ''}${minors > 1 ? ', ' + minors + ' minor versions' : ''}).`
    + (majorJump ? '\n⚠️ Major version jump: read the breaking changes first: https://docs.n8n.io/release-notes/' : '\nRelease notes: https://docs.n8n.io/release-notes/')
    + '\n' + lines.join('\n') + (newer.length > 8 ? `\n…and ${newer.length - 8} more` : '')
    + '\nBefore upgrading: back up the database and keep your N8N_ENCRYPTION_KEY.';
  return { newer: newer.map((x) => x.p.v.join('.')), latest: latest.p.v.join('.'), majorJump, notify, text };
}
module.exports = { releaseReport, parseV };
