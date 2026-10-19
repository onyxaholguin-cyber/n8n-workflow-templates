#!/usr/bin/env python3
"""Check n8n workflow JSON files against the n8n Creator Hub template rules.

Rules (n8n "Template submission guidelines" + "Sticky note guidelines for templates", read 2026-10-19):
- exactly one main overview sticky: yellow (color 1 / unset), top-left of the canvas, 100-300 words,
  contains '### How it works' and '### Setup'
- other stickies are section stickies: white/neutral (color 7), titles only
- workflows with 4+ nodes need section stickies; every node should sit inside a sticky
- no embedded credentials, no pinData, no default node names, no hardcoded secrets
- title: starts with a verb, no emoji/hype words, <= 90 characters
Usage: check_creator_hub.py FILE... (exit 1 on any error)
"""
import json, re, sys

NODE_W, NODE_H = 100, 100
DEFAULT_NAMES = re.compile(r'^(HTTP Request|Code|Set|Edit Fields|If|IF|Switch|Merge|No Operation, do nothing|'
                           r'Schedule Trigger|Webhook|Function|Sticky Note|When clicking .*)\d*$')
SECRET = re.compile(r'(sk-[A-Za-z0-9]{20,}|xox[abp]-[A-Za-z0-9-]{10,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|'
                    r'Bearer\s+[A-Za-z0-9._-]{20,}|hooks\.slack\.com/services/[A-Z0-9]+/|discord(?:app)?\.com/api/webhooks/\d+)')
HYPE = re.compile(r'(?i)\b(ultimate|powerful|revolutionary|10x|magic|insane|best)\b')
EMOJI = re.compile('[\U0001F300-\U0001FAFF\u2600-\u27BF]')
VERBS = {'audit', 'send', 'get', 'categorize', 'create', 'sync', 'post', 'track', 'monitor', 'generate', 'back',
         'check', 'notify', 'alert', 'import', 'export', 'convert', 'summarize', 'build', 'remind', 'calculate'}


def words(s):
    return len(re.findall(r"[A-Za-z0-9][\w'’.-]*", s))


def inside(n, s):
    x, y = n['position']; sx, sy = s['position']
    w, h = s['parameters'].get('width', 240), s['parameters'].get('height', 160)
    return sx <= x and sy <= y and x + NODE_W <= sx + w and y + NODE_H <= sy + h


def check(path):
    errs, warns = [], []
    w = json.load(open(path))
    nodes = w.get('nodes', [])
    stickies = [n for n in nodes if n['type'].endswith('stickyNote')]
    real = [n for n in nodes if not n['type'].endswith('stickyNote')]
    main = [s for s in stickies if s['parameters'].get('color', 1) == 1]
    if len(main) != 1:
        errs.append(f'need exactly 1 yellow main sticky, found {len(main)}')
    else:
        m = main[0]; c = m['parameters'].get('content', '')
        n = words(c)
        if not 100 <= n <= 300: errs.append(f'main sticky has {n} words (need 100-300)')
        for h in ('### How it works', '### Setup'):
            if not re.search('^' + re.escape(h) + r'\s*$', c, re.M): errs.append(f'main sticky lacks heading "{h}"')
        mx, my = m['position']
        if any(o['position'][0] < mx or o['position'][1] < my for o in nodes if o is not m):
            errs.append('main sticky is not top-left')
    for s in stickies:
        if s in main: continue
        if s['parameters'].get('color') != 7: errs.append(f'section sticky "{s["name"]}" is not white (color 7)')
        t = s['parameters'].get('content', '').strip()
        if '\n' in t or words(t) > 10: errs.append(f'section sticky "{s["name"]}" is not a title only')
    if len(real) >= 4:
        if len(stickies) - len(main) < 1: errs.append('4+ nodes but no section stickies')
        sections = [s for s in stickies if s not in main]
        for n in real:
            if not any(inside(n, s) for s in sections): errs.append(f'node "{n["name"]}" is not inside a section sticky')
    for n in real:
        if n.get('credentials'): errs.append(f'node "{n["name"]}" embeds a credentials block')
        if DEFAULT_NAMES.match(n['name']): errs.append(f'node "{n["name"]}" has a default name')
    if w.get('pinData'): errs.append('pinData is not empty')
    if SECRET.search(json.dumps(w)): errs.append('possible hardcoded secret or live webhook URL')
    title = w.get('name', '')
    if EMOJI.search(title) or HYPE.search(title): errs.append(f'title has emoji/hype: {title}')
    if title.split(' ')[0].lower() not in VERBS: warns.append(f'title does not start with a known verb: {title}')
    if len(title) > 90: errs.append(f'title is {len(title)} chars (> 90)')
    return errs, warns


if __name__ == '__main__':
    bad = 0
    for p in sys.argv[1:]:
        e, wn = check(p)
        print(('FAIL ' if e else 'OK   ') + p)
        for x in e: print('   error:', x)
        for x in wn: print('   warn: ', x)
        bad += bool(e)
    sys.exit(1 if bad else 0)
