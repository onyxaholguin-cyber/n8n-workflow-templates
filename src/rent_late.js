// Rent status + late fee for each charge row, same rule as the Sheet & Flow late-fee tutorial:
// days late = (date paid in full, else as-of date) - due date, never below 0.
// No fee while days late <= graceDays; after that: flat + percent x rent + daily x (days late - grace), capped at maxFee (0 = no cap).
const { parseCSV, pick, toDay, dayToISO, num, money, r2 } = require('./common.js');
function rentReport(csvText, cfg) {
  const asOf = toDay(cfg.asOfDate);
  if (asOf == null) throw new Error('asOfDate must be YYYY-MM-DD');
  const grace = num(cfg.graceDays), flat = num(cfg.lateFeeFlat), pct = num(cfg.lateFeePercent) / 100, daily = num(cfg.dailyFee), cap = num(cfg.maxFee);
  if ([grace, flat, pct, daily, cap].some((v) => !isFinite(v) || v < 0)) throw new Error('Fee settings must be numbers >= 0');
  const rows = parseCSV(csvText), out = [], problems = [];
  rows.forEach((r, i) => {
    const tenant = pick(r, ['tenant', 'name', 'tenant name']), unit = pick(r, ['unit', 'property', 'address']);
    const due = toDay(pick(r, ['due date', 'due'])), rent = num(pick(r, ['rent', 'amount due', 'monthly rent']));
    const paid = num(pick(r, ['amount paid', 'paid'])), paidOn = pick(r, ['date paid', 'paid date', 'paid on']);
    if (!tenant && !unit) return;
    if (due == null || !isFinite(rent) || !isFinite(paid)) { problems.push(`Row ${i + 2} (${tenant || unit}): check the due date / rent / amount paid`); return; }
    const paidDay = paidOn ? toDay(paidOn) : null;
    const end = paidDay != null && paid >= rent ? paidDay : asOf;
    const daysLate = Math.max(0, end - due);
    let fee = 0;
    if (daysLate > grace) { fee = flat + pct * rent + daily * (daysLate - grace); if (cap > 0) fee = Math.min(cap, fee); fee = r2(fee); }
    const balance = r2(rent + fee - paid);
    let status;
    if (balance <= 0) status = 'Paid';
    else if (paid >= rent) status = 'Fee owed';
    else if (due > asOf) status = 'Upcoming';
    else if (daysLate > grace) status = 'LATE';
    else if (paid > 0) status = 'Partial';
    else status = 'Due';
    out.push({ tenant, unit, due: dayToISO(due), rent, paid, daysLate, fee, balance, status });
  });
  const flagged = out.filter((x) => x.status === 'LATE' || x.status === 'Fee owed' || x.status === 'Partial' || (x.status === 'Due' && x.daysLate > 0));
  const order = { LATE: 0, 'Fee owed': 1, Partial: 2, Due: 3 };
  flagged.sort((a, b) => order[a.status] - order[b.status] || b.daysLate - a.daysLate);
  const totalOwed = flagged.reduce((s, x) => s + x.balance, 0);
  const lines = flagged.map((x) => `${x.status === 'LATE' ? '🔴' : x.status === 'Fee owed' ? '🟠' : '🟡'} ${x.status}: ${x.tenant || '?'}${x.unit ? ' (' + x.unit + ')' : ''}, due ${x.due}, ${x.daysLate} day${x.daysLate === 1 ? '' : 's'} late, late fee ${money(x.fee)}, balance ${money(x.balance)}`);
  const text = flagged.length
    ? `Rent check for ${dayToISO(asOf)}: ${flagged.length} of ${out.length} charges need attention, ${money(totalOwed)} owed in total.\n` + lines.join('\n') + (problems.length ? '\n⚠️ ' + problems.join('\n⚠️ ') : '')
    : '';
  return { asOf: dayToISO(asOf), rows: out, flagged: flagged.length, totalOwed: r2(totalOwed), problems, text: text || (problems.length ? `Rent check for ${dayToISO(asOf)}: nothing late.\n⚠️ ` + problems.join('\n⚠️ ') : '') };
}
module.exports = { rentReport };
