"""Unit tests for the template logic (src/*.js) against an independent Python model.
Runs node on the JS modules; Python re-implements the rules from the spec, not from the JS."""
import json, random, subprocess, datetime as dt, sys
import os
R5 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')
def js(mod, fn, *args):
    code = f"const m=require('{R5}/{mod}');process.stdout.write(JSON.stringify(m.{fn}(...JSON.parse(process.argv[1]))))"
    r = subprocess.run(['node', '-e', code, json.dumps(args)], capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr[-800:])
    return json.loads(r.stdout)
D = lambda s: dt.date.fromisoformat(s)
fails = 0
def check(cond, msg):
    global fails
    if not cond: fails += 1; print('FAIL', msg)

# ---------- rent: model
def model_rent(rows, cfg):
    asof = D(cfg['asOfDate']); out = []
    for r in rows:
        due = D(r['due']); rent = r['rent']; paid = r['paid']; paid_on = D(r['paid_on']) if r['paid_on'] else None
        end = paid_on if (paid_on and paid >= rent) else asof
        late = max(0, (end - due).days)
        fee = 0.0
        if late > cfg['graceDays']:
            fee = cfg['lateFeeFlat'] + cfg['lateFeePercent'] / 100 * rent + cfg['dailyFee'] * (late - cfg['graceDays'])
            if cfg['maxFee'] > 0: fee = min(cfg['maxFee'], fee)
            fee = round(fee + 1e-9, 2)
        bal = round(rent + fee - paid, 2)
        st = 'Paid' if bal <= 0 else 'Fee owed' if paid >= rent else 'Upcoming' if due > asof else 'LATE' if late > cfg['graceDays'] else 'Partial' if paid > 0 else 'Due'
        out.append((late, fee, bal, st))
    return out
def csv_rent(rows):
    return 'Tenant,Unit,Due date,Rent,Amount paid,Date paid\n' + '\n'.join(f"{r['t']},{r['u']},{r['due']},{r['rent']},{r['paid']},{r['paid_on']}" for r in rows) + '\n'

# tutorial worked example anchor (as-of 2026-10-20, grace 5, $50 flat, $10/day, max $150)
cfg = dict(asOfDate='2026-10-20', graceDays=5, lateFeeFlat=50, lateFeePercent=0, dailyFee=10, maxFee=150)
ex = [dict(t='A', u='102 Maple', due='2026-10-01', rent=1395, paid=1395, paid_on='2026-10-06'),
      dict(t='B', u='103 Maple', due='2026-10-01', rent=1395, paid=1395, paid_on='2026-10-07'),
      dict(t='C', u='104 Maple', due='2026-10-01', rent=1200, paid=0, paid_on=''),
      dict(t='D', u='105 Maple', due='2026-11-01', rent=1200, paid=0, paid_on='')]
res = js('rent_late.js', 'rentReport', csv_rent(ex), cfg)
got = [(x['daysLate'], x['fee'], x['balance'], x['status']) for x in res['rows']]
check(got[0] == (5, 0, 0, 'Paid'), f'grace boundary paid on 6th {got[0]}')
check(got[1] == (6, 60, 60, 'Fee owed'), f'tutorial 103 Maple $60 {got[1]}')
check(got[2] == (19, 150, 1350, 'LATE'), f'cap at $150 {got[2]}')
check(got[3][3] == 'Upcoming', f'upcoming {got[3]}')
check('104 Maple' in res['text'] and '$150.00' in res['text'] and res['flagged'] == 2, res['text'])
check(got == model_rent(ex, cfg), 'anchor vs model')

random.seed(5)
n = 0
for s in range(40):
    cfg = dict(asOfDate=f'2026-{random.randint(1,12):02d}-{random.randint(1,28):02d}', graceDays=random.choice([0, 2, 4, 5, 6, 10]),
               lateFeeFlat=random.choice([0, 25, 50, 75]), lateFeePercent=random.choice([0, 5, 10, 12]), dailyFee=random.choice([0, 5, 10]), maxFee=random.choice([0, 50, 100, 150]))
    rows = []
    for i in range(25):
        asof = D(cfg['asOfDate']); due = asof + dt.timedelta(days=random.randint(-40, 15)); rent = random.choice([850, 1199.5, 1395, 2100])
        k = random.random()
        if k < .3: paid, po = 0, ''
        elif k < .5: paid, po = round(rent * random.random(), 2), ''
        elif k < .9: paid, po = rent, (due + dt.timedelta(days=random.randint(-3, 25))).isoformat()
        else: paid, po = rent + 60, (due + dt.timedelta(days=random.randint(0, 20))).isoformat()
        rows.append(dict(t=f'T{i}', u=f'U{i}', due=due.isoformat(), rent=rent, paid=paid, paid_on=po))
    res = js('rent_late.js', 'rentReport', csv_rent(rows), cfg)
    got = [(x['daysLate'], x['fee'], x['balance'], x['status']) for x in res['rows']]
    exp = model_rent(rows, cfg)
    for g, e, r in zip(got, exp, rows):
        n += 1; check(g[0] == e[0] and abs(g[1] - e[1]) < 0.005 and abs(g[2] - e[2]) < 0.005 and g[3] == e[3], f'rent {cfg} {r} js={g} model={e}')
print('rent rows compared', n)
# bad input -> problem line, not crash
res = js('rent_late.js', 'rentReport', 'Tenant,Unit,Due date,Rent,Amount paid\nX,1,notadate,1000,0\n', dict(asOfDate='2026-10-09', graceDays=5, lateFeeFlat=50, lateFeePercent=0, dailyFee=0, maxFee=0))
check(res['problems'] and 'check the due date' in res['problems'][0], res)

# ---------- lease renewals: model
def model_lease(rows, cfg):
    asof = D(cfg['asOfDate']); out = []
    for r in rows:
        if r['status'].lower() in ('renewed', 'moved out', 'notice sent'): continue
        end = D(r['end']); notice = cfg['noticeDays'] if r['notice'] == '' else int(r['notice'])
        send_by = end - dt.timedelta(days=notice + cfg['mailingBufferDays']); left = (send_by - asof).days
        if end < asof or left > cfg['alertWindowDays']: continue
        out.append((r['t'], send_by.isoformat(), left, round(r['rent'] * (1 + r['inc'] / 100) + 1e-9, 2)))
    return sorted(out, key=lambda x: x[2])
def csv_lease(rows):
    return 'Tenant,Unit,Lease end,Notice days,Rent,Increase %,Status\n' + '\n'.join(f"{r['t']},{r['u']},{r['end']},{r['notice']},{r['rent']},{r['inc']},{r['status']}" for r in rows) + '\n'
m = 0
for s in range(40):
    cfg = dict(asOfDate=f'2026-{random.randint(1,12):02d}-{random.randint(1,28):02d}', noticeDays=random.choice([30, 60, 90]), mailingBufferDays=random.choice([0, 3, 5]), alertWindowDays=random.choice([14, 30, 45]))
    rows = []
    for i in range(20):
        asof = D(cfg['asOfDate'])
        rows.append(dict(t=f'L{i}', u=f'U{i}', end=(asof + dt.timedelta(days=random.randint(-10, 200))).isoformat(), notice=random.choice(['', '', '30', '60', '90']),
                         rent=random.choice([900, 1250, 1999]), inc=random.choice([0, 3, 4.5, 10]), status=random.choice(['', '', '', 'Renewed', 'Moved out', 'Active'])))
    res = js('lease_renewals.js', 'renewalReport', csv_lease(rows), cfg)
    got = [(x['tenant'], x['sendBy'], x['daysLeft'], x['newRent']) for x in res['due']]
    exp = model_lease(rows, cfg)
    m += len(exp)
    check(sorted(got) == sorted(exp), f'lease {cfg}\n js={got}\n model={exp}')
print('lease reminders compared', m)
# known example: lease ends 2026-12-31, 60-day notice, 5-day buffer -> send by 2026-10-27
res = js('lease_renewals.js', 'renewalReport', 'Tenant,Unit,Lease end,Rent,Increase %\nRivera,2B,2026-12-31,1450,4\n', dict(asOfDate='2026-10-09', noticeDays=60, mailingBufferDays=5, alertWindowDays=30))
check(res['due'] and res['due'][0]['sendBy'] == '2026-10-27' and res['due'][0]['daysLeft'] == 18 and res['due'][0]['newRent'] == 1508, res)
check('$1,450.00 → $1,508.00 (+4%)' in res['text'], res['text'])

# ---------- n8n releases
rel = [dict(tag_name='n8n@2.42.0', name='n8n@2.42.0', prerelease=True, draft=False, published_at='2026-10-08T00:00:00Z', html_url='u0'),
       dict(tag_name='n8n@2.41.4', name='n8n@2.41.4', prerelease=False, draft=False, published_at='2026-10-01T00:00:00Z', html_url='u1'),
       dict(tag_name='n8n@2.41.3', name='n8n@2.41.3', prerelease=False, draft=False, published_at='2026-09-28T00:00:00Z', html_url='u2'),
       dict(tag_name='n8n@2.40.6', name='n8n@2.40.6', prerelease=False, draft=False, published_at='2026-09-20T00:00:00Z', html_url='u3'),
       dict(tag_name='n8n@1.123.9', name='n8n@1.123.9', prerelease=False, draft=False, published_at='2026-09-25T00:00:00Z', html_url='u4'),
       dict(tag_name='@n8n/chat@1.9.0', name='chat', prerelease=False, draft=False, published_at='2026-10-02T00:00:00Z', html_url='u5')]
r = js('n8n_release.js', 'releaseReport', rel, dict(currentVersion='2.40.6'))
check(r['newer'] == ['2.41.4', '2.41.3'] and r['latest'] == '2.41.4' and r['notify'] and not r['majorJump'], r)
r = js('n8n_release.js', 'releaseReport', rel, dict(currentVersion='2.40.6', lastNotified='2.41.4'))
check(not r['notify'], 'already notified')
r = js('n8n_release.js', 'releaseReport', rel, dict(currentVersion='1.123.9'))
check(r['majorJump'] and r['newer'][0] == '2.41.4' and 'Major version jump' in r['text'], r)
r = js('n8n_release.js', 'releaseReport', rel, dict(currentVersion='2.41.4'))
check(r['newer'] == [] and r['text'] == '', r)
print('RESULT', 'PASS' if not fails else f'{fails} FAILURES')
sys.exit(1 if fails else 0)
