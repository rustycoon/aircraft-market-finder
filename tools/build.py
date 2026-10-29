"""Build the Aircraft Market Finder page.

Reads   profiles/<type>.json            (one per aircraft type)
        data/<type>/<YYYY-MM-DD>.json   (one per run)
Writes  index.html

Run:    python3 tools/build.py <site folder>
"""
import json, re, sys, glob, os, datetime as dt

ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
TPL = os.path.join(ROOT, 'tools', 'template.html')


def ident(r):
    """One aircraft = one row: serial first, then tail, then the ad link."""
    s = re.sub(r'[^0-9A-Z]', '', (r.get('serial') or '').upper())
    if s:
        return 'SN:' + s
    t = re.sub(r'[^0-9A-Z]', '', (r.get('tail') or '').upper())
    if t:
        return 'TAIL:' + t
    return 'URL:' + r.get('url', '')


def counted(r):
    return bool(r.get('ask')) and not r.get('kind')


def stats(rows):
    a = sorted(r['ask'] for r in rows if counted(r))
    if not a:
        return {'n': 0}
    n = len(a)
    med = a[n // 2] if n % 2 else (a[n // 2 - 1] + a[n // 2]) / 2
    return {'n': n, 'median': med, 'mean': sum(a) / n}


def build_type(prof, runs):
    runs = sorted(runs, key=lambda r: r['run_date'])
    hist = {}  # id -> {'first': date, 'asks': [(date, ask)]}
    for run in runs:
        for r in run['listings']:
            h = hist.setdefault(ident(r), {'first': run['run_date'], 'asks': []})
            if not h['asks'] or h['asks'][-1][1] != r.get('ask'):
                h['asks'].append((run['run_date'], r.get('ask')))
    latest = runs[-1]
    prev = runs[-2] if len(runs) > 1 else None
    today = dt.date.fromisoformat(latest['run_date'])
    rows = []
    for r in latest['listings']:
        r = dict(r)
        h = hist[ident(r)]
        r['first_seen'] = h['first']
        r['days_listed'] = (today - dt.date.fromisoformat(h['first'])).days
        r['price_history'] = [{'date': d, 'ask': a} for d, a in h['asks']]
        rows.append(r)
    changes = None
    if prev:
        p = {ident(r): r for r in prev['listings']}
        c = {ident(r): r for r in latest['listings']}
        changes = {
            'since': prev['run_date'],
            'new': [ident(r) for r in latest['listings'] if ident(r) not in p],
            'gone': [{'year': r.get('year'), 'model': r.get('model'), 'tail': r.get('tail'), 'loc': r.get('loc'),
                      'last_ask': r.get('ask'), 'group': r.get('group'), 'url': r.get('url')}
                     for k, r in p.items() if k not in c],
            'moves': [{'id': k, 'from': p[k].get('ask'), 'to': r.get('ask')}
                      for k, r in c.items() if k in p and p[k].get('ask') != r.get('ask')],
        }
    for r in rows:
        r['id'] = ident(r)
    trend = []
    for run in runs:
        t = {'date': run['run_date']}
        for g in prof['groups']:
            t[g['id']] = stats([r for r in run['listings'] if r.get('group') == g['id']])
        trend.append(t)
    return {'id': prof['id'], 'name': prof['name'], 'groups': prof['groups'], 'run_date': latest['run_date'],
            'runs': len(runs), 'sources_ok': latest['sources_ok'], 'sources_fail': latest['sources_fail'],
            'listings': rows, 'changes': changes, 'trend': trend,
            'draft': bool(prof.get('draft')), 'draft_note': prof.get('draft_note', '')}


def main():
    types = []
    for pf in sorted(glob.glob(os.path.join(ROOT, 'profiles', '*.json'))):
        prof = json.load(open(pf))
        runs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(ROOT, 'data', prof['id'], '*.json')))]
        if runs:
            types.append(build_type(prof, runs))
    blob = json.dumps({'types': types}, ensure_ascii=False).replace('</', '<\\/')
    html = open(TPL).read().replace('__DATA__', blob)
    out = os.path.join(ROOT, 'index.html')
    open(out, 'w').write(html)
    print(out, len(html), [(t['name'], t['runs'], len(t['listings'])) for t in types])


if __name__ == '__main__':
    main()
