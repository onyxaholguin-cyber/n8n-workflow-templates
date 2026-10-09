// Shared helpers: tiny CSV parser + date math (no dependencies).
function parseCSV(text) {
  const rows = []; let row = [], f = '', q = false;
  text = String(text || '').replace(/^\uFEFF/, '');
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
    else if (c === '"') q = true;
    else if (c === ',') { row.push(f); f = ''; }
    else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; row.push(f); rows.push(row); row = []; f = ''; }
    else f += c;
  }
  if (f !== '' || row.length) { row.push(f); rows.push(row); }
  const clean = rows.filter((r) => r.some((c) => String(c).trim() !== ''));
  if (!clean.length) return [];
  const head = clean[0].map((h) => String(h).trim().toLowerCase());
  return clean.slice(1).map((r) => { const o = {}; head.forEach((h, i) => { o[h] = String(r[i] == null ? '' : r[i]).trim(); }); return o; });
}
function pick(o, names) { for (const n of names) { if (o[n] !== undefined && o[n] !== '') return o[n]; } return ''; }
function toDay(s) { // 'YYYY-MM-DD' or 'M/D/YYYY' -> integer day number (UTC), or null
  s = String(s || '').trim(); let m, y, mo, d;
  if ((m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/))) { y = +m[1]; mo = +m[2]; d = +m[3]; }
  else if ((m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/))) { mo = +m[1]; d = +m[2]; y = +m[3]; }
  else return null;
  const t = Date.UTC(y, mo - 1, d); const back = new Date(t);
  if (back.getUTCMonth() !== mo - 1 || back.getUTCDate() !== d) return null;
  return Math.round(t / 86400000);
}
function dayToISO(n) { return new Date(n * 86400000).toISOString().slice(0, 10); }
function num(s) { s = String(s == null ? '' : s).replace(/[$,\s]/g, ''); if (s === '') return 0; const v = Number(s.replace(/%$/, '')); return isFinite(v) ? v : NaN; }
function r2(v) { return Math.round(Number((v * 100).toFixed(6))) / 100; } // half-up like a spreadsheet ROUND
function money(v) { return '$' + r2(v).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
module.exports = { parseCSV, pick, toDay, dayToISO, num, money, r2 };
