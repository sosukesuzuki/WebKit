#!/usr/bin/env python3
"""compare.py <results-dir> <labelA> <labelB> <suite> [minms]  — mean phase totals over runs labelA{1,2,3} vs labelB{1,2,3}"""
import sys, re, glob, statistics, os
d, a, b, suite = sys.argv[1:5]
minms = float(sys.argv[5]) if len(sys.argv) > 5 else 5.0
def load(label):
    runs = {}
    for f in sorted(glob.glob(os.path.join(d, f"{label}[0-9]*-{suite}.txt"))):
        phases = {}
        for line in open(f):
            m = re.match(r"total ms:\s*([\d.]+)\s+max ms:\s*([\d.]+)\s+\[(.*?)\] (.*)", line)
            if m:
                phases[f"[{m.group(3)}] {m.group(4).strip()}"] = float(m.group(1))
            m = re.search(r"RUSAGE maxrss_kb=(\d+) user=([\d.]+) sys=([\d.]+) wall=([\d.]+)", line)
            if m:
                phases["maxrss_MB"] = int(m.group(1)) / 1024
                phases["user_s"] = float(m.group(2)); phases["wall_s"] = float(m.group(4))
        for k, v in phases.items():
            runs.setdefault(k, []).append(v)
    return runs
A, B_ = load(a), load(b)
rows = []
for k in set(A) | set(B_):
    va, vb = A.get(k), B_.get(k)
    ma = statistics.mean(va) if va else None
    mb = statistics.mean(vb) if vb else None
    rows.append((k, ma, mb, va, vb))
rows.sort(key=lambda r: -(r[1] or r[2] or 0))
print(f"{'phase':60s} {a:>10s} {b:>10s} {'delta':>8s}  (n={len(next(iter(A.values())))},{len(next(iter(B_.values())))})")
for k, ma, mb, va, vb in rows:
    if (ma or 0) < minms and (mb or 0) < minms: continue
    delta = f"{(mb-ma)/ma*100:+6.1f}%" if ma and mb else "n/a"
    sa = f"{ma:10.1f}" if ma is not None else f"{'-':>10s}"
    sb = f"{mb:10.1f}" if mb is not None else f"{'-':>10s}"
    spread = ""
    if va and len(va) > 1: spread = f"  [{min(va):.0f}-{max(va):.0f} | {min(vb):.0f}-{max(vb):.0f}]" if vb else ""
    print(f"{k:60s} {sa} {sb} {delta}{spread}")
