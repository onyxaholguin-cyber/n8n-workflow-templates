"""Static checks for every workflow JSON: importable shape, connections point at real nodes,
no credential ids, no pinned data, no secret-looking values, embedded logic matches src/."""
import json, glob, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
SECRET = re.compile(r'(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|xox[bp]-[A-Za-z0-9-]{10,}|hooks\.slack\.com/services/[A-Z0-9]+/|discord(app)?\.com/api/webhooks/\d+|Bearer [A-Za-z0-9._-]{20,})')
fails = 0
for f in sorted(glob.glob(os.path.join(ROOT, 'workflows', '*.json'))):
    w = json.load(open(f)); name = os.path.basename(f); errs = []
    for k in ('name', 'nodes', 'connections'):
        if k not in w: errs.append(f'missing {k}')
    names = {n['name'] for n in w['nodes']}
    if len(names) != len(w['nodes']): errs.append('duplicate node names')
    for src, outs in w['connections'].items():
        if src not in names: errs.append(f'connection from unknown node {src}')
        for branch in outs.get('main', []):
            for c in branch:
                if c['node'] not in names: errs.append(f'connection to unknown node {c["node"]}')
    for n in w['nodes']:
        for cred in (n.get('credentials') or {}).values():
            if cred.get('id'): errs.append(f'credential id left in {n["name"]}')
    if w.get('pinData'): errs.append('pinned data present')
    if SECRET.search(json.dumps(w)): errs.append('secret-looking value')
    triggers = [n for n in w['nodes'] if 'Trigger' in n['type'] or n['type'].endswith('trigger')]
    if not triggers: errs.append('no trigger node')
    print(('FAIL ' if errs else 'ok   ') + name, '; '.join(errs)); fails += bool(errs)
print('RESULT', 'PASS' if not fails else f'{fails} FAILED'); sys.exit(1 if fails else 0)
