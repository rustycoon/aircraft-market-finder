"""Check one aircraft type on the built page against its latest run file.

python3 tools/check_type.py <site folder> <type id>

It first breaks one price in a scratch copy and makes sure the check FAILS on it,
then checks the real page. Exit code 0 only if the broken copy failed and the real page passed.
"""
import sys, os, json, glob, shutil, tempfile, subprocess, asyncio, statistics as st
from playwright.async_api import async_playwright

SITE, TID = os.path.abspath(sys.argv[1]), sys.argv[2]


def expected(site):
    prof = json.load(open(os.path.join(site, 'profiles', TID + '.json')))
    run = json.load(open(sorted(glob.glob(os.path.join(site, 'data', TID, '*.json')))[-1]))
    out = {}
    for g in prof['groups']:
        rows = [r for r in run['listings'] if r.get('group') == g['id']]
        a = sorted(r['ask'] for r in rows if r.get('ask') and not r.get('kind'))
        out[g['id']] = (str(len(rows)), str(len(a)),
                        '$' + format(round(st.median(a)), ',') if a else '—',
                        '$' + format(round(st.mean(a)), ',') if a else '—')
    return out


async def page_values(index):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 390, 'height': 900})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://' + index + '#' + TID, wait_until='domcontentloaded')
        secs = await pg.eval_on_selector_all('section', '''ss=>ss.map(s=>({g:s.dataset.group,rows:String(s.querySelectorAll('details.row').length),
              t:[...s.querySelectorAll('.tile .v')].map(v=>v.textContent)}))''')
        sw = await pg.evaluate('document.documentElement.scrollWidth')
        await b.close()
    return {s['g']: (s['rows'], s['t'][1], s['t'][2], s['t'][3]) for s in secs}, errs, sw


def check(index, exp):
    got, errs, sw = asyncio.run(page_values(index))
    fails = [f'{g}: page {got.get(g)} != data {v}' for g, v in exp.items() if got.get(g) != v]
    if errs: fails.append(f'page errors {errs}')
    if sw > 390: fails.append(f'sideways scroll on a phone ({sw})')
    return fails


exp = expected(SITE)
tmp = tempfile.mkdtemp()
shutil.copytree(SITE, os.path.join(tmp, 's'), ignore=shutil.ignore_patterns('.git'))
bad = os.path.join(tmp, 's')
f = sorted(glob.glob(os.path.join(bad, 'data', TID, '*.json')))[-1]
run = json.load(open(f))
for r in run['listings']:
    if r.get('ask') and not r.get('kind'):
        r['ask'] = r['ask'] + 12345
        break
json.dump(run, open(f, 'w'))
subprocess.run([sys.executable, os.path.join(bad, 'tools', 'build.py'), bad], check=True, capture_output=True)
broken = check(os.path.join(bad, 'index.html'), exp)
real = check(os.path.join(SITE, 'index.html'), exp)
print('broken copy:', 'FAILED as it should' if broken else 'PASSED — the check is not working')
print('real page:  ', 'PASS' if not real else 'FAIL')
for x in real: print('   ', x)
print('expected:', exp)
sys.exit(0 if broken and not real else 1)
