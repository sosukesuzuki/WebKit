#!/usr/bin/env python3
"""Merge the primary measurement outputs into data/data.json (consumed by gen_report.py).
Inputs (all under data/): sizes.txt (stdout of scripts/sizeof/sizes), meta.txt (stdout of scripts/sizeof/meta),
summary.json (scripts/measure/parse.py), retained.json (scripts/measure/agg_retained.py),
sizestats_typescript.log / dfgsizestats_typescript.log (jsc --dump{Baseline,DFG}JITSizeStatistics=1)."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, 'data')
def rd(name): return open(os.path.join(DATA, name)).read()
sizeof = {}
for l in rd('sizes.txt').splitlines():
    k, v = l.rsplit(None, 1); sizeof[k.strip()] = int(v)
meta = {}
for l in rd('meta.txt').splitlines():
    m = re.match(r'(\S+)\s+meta=\s*(\d+)', l)
    if m: meta[m.group(1)] = int(m.group(2))
def perop(name):
    rows = [(m.group(1), int(m.group(2)), int(m.group(3)), float(m.group(4)))
            for m in re.finditer(r'(\S+) totalBytes: (\d+) count: (\d+) avg: ([\d.]+)', rd(name))]
    return sorted(rows, key=lambda x: -x[1])
out = {'sizeof': sizeof, 'metaSizes': meta,
       'matrix': json.loads(rd('summary.json')), 'retained': json.loads(rd('retained.json')),
       'baselineOps': perop('sizestats_typescript.log'), 'dfgOps': perop('dfgsizestats_typescript.log')}
json.dump(out, open(os.path.join(DATA, 'data.json'), 'w'), indent=1)
print('wrote data/data.json')
