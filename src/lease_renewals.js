// Lease renewal reminders: send-by date = lease end - notice days - mailing buffer.
// Reports leases whose send-by date is within alertWindowDays (or already passed while the lease is still running).
const { parseCSV, pick, toDay, dayToISO, num, money, r2 } = require('./common.js');
function renewalReport(csvText, cfg) {
  const asOf = toDay(cfg.asOfDate);
  if (asOf == null) throw new Error('asOfDate must be YYYY-MM-DD');
  const defNotice = num(cfg.noticeDays), buffer = num(cfg.mailingBufferDays), win = num(cfg.alertWindowDays);
  if ([defNotice, buffer, win].some((v) => !isFinite(v) || v < 0)) throw new Error('Day settings must be numbers >= 0');
  const skip = /renewed|moved out|notice sent|vacat/i;
  const rows = parseCSV(csvText), due = [], problems = [];
  rows.forEach((r, i) => {
    const tenant = pick(r, ['tenant', 'name', 'tenant name']), unit = pick(r, ['unit', 'property', 'address']);
    if (!tenant && !unit) return;
    if (skip.test(pick(r, ['status']))) return;
    const end = toDay(pick(r, ['lease end', 'end date', 'lease end date']));
    if (end == null) { problems.push(`Row ${i + 2} (${tenant || unit}): lease end must be a date`); return; }
    const nd = pick(r, ['notice days']); const notice = nd === '' ? defNotice : num(nd);
    const rent = num(pick(r, ['rent', 'current rent'])), inc = num(pick(r, ['increase %', 'planned increase %', 'increase']));
    if (!isFinite(notice) || !isFinite(rent) || !isFinite(inc)) { problems.push(`Row ${i + 2} (${tenant || unit}): check notice days / rent / increase %`); return; }
    const sendBy = end - notice - buffer, daysLeft = sendBy - asOf;
    if (end < asOf) return;                       // lease already ended: not a renewal question any more
    if (daysLeft > win) return;                   // not yet in the window
    const newRent = r2(rent * (1 + inc / 100));
    due.push({ tenant, unit, leaseEnd: dayToISO(end), notice, sendBy: dayToISO(sendBy), daysLeft, rent, increasePct: inc, newRent, overdue: daysLeft < 0 });
  });
  due.sort((a, b) => a.daysLeft - b.daysLeft);
  const lines = due.map((x) => `${x.overdue ? '🔴 OVERDUE' : x.daysLeft <= 7 ? '🟠 This week' : '🟡 Coming up'}: ${x.tenant || '?'}${x.unit ? ' (' + x.unit + ')' : ''}, lease ends ${x.leaseEnd}, send the ${x.notice}-day notice by ${x.sendBy} (${x.overdue ? Math.abs(x.daysLeft) + ' days ago' : x.daysLeft === 0 ? 'today' : 'in ' + x.daysLeft + ' days'})` + (x.rent ? `, rent ${money(x.rent)}` + (x.increasePct ? ` → ${money(x.newRent)} (+${x.increasePct}%)` : '') : ''));
  const text = due.length ? `Lease renewals as of ${dayToISO(asOf)}: ${due.length} notice${due.length === 1 ? '' : 's'} to send.\n` + lines.join('\n') + (problems.length ? '\n⚠️ ' + problems.join('\n⚠️ ') : '') : (problems.length ? `Lease renewals as of ${dayToISO(asOf)}: nothing due.\n⚠️ ` + problems.join('\n⚠️ ') : '');
  return { asOf: dayToISO(asOf), due, problems, text };
}
module.exports = { renewalReport };
