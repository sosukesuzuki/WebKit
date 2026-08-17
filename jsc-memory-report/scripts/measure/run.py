#!/usr/bin/env python3
"""Run jsc with a workload; when the JS side prints '@@WAIT <tag>', read /proc/pid/smaps for the JIT pool + total RSS, then send a newline."""
import subprocess, sys, re, os
JSC = os.environ.get("JSC") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "WebKitBuild", "JSCOnly-Release", "bin", "jsc")
def smaps(pid):
    txt = open(f"/proc/{pid}/smaps").read()
    regs=[]; cur=None; total_rss=0
    for l in txt.split("\n"):
        m = re.match(r"^([0-9a-f]+)-([0-9a-f]+) (\S+) (\S+) (\S+) (\S+)\s*(.*)$", l)
        if m:
            cur=[int(m.group(1),16),int(m.group(2),16),m.group(3),m.group(7),0]; regs.append(cur); continue
        r=re.match(r"^Rss:\s+(\d+) kB", l)
        if r and cur is not None:
            cur[4]=int(r.group(1))*1024; total_rss+=cur[4]
    # JIT pool = cluster of contiguous anonymous executable mappings whose total size >= 64MB
    best=None; groups=[]; g=None
    for r in regs:
        ok = ('x' in r[2] and r[3]=='')
        if ok and g is not None and g["end"]==r[0]:
            g["size"]+=r[1]-r[0]; g["rss"]+=r[4]; g["end"]=r[1]; g["n"]+=1
        elif ok:
            g={"size":r[1]-r[0],"rss":r[4],"end":r[1],"n":1}; groups.append(g)
        else:
            g=None
    for g in groups:
        if g["size"]>=64*1024*1024 and (best is None or g["size"]>best["size"]): best=g
    return best, total_rss
def main():
    args=[JSC]+sys.argv[1:]
    p=subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.environ.get("CWD","."))
    for line in p.stdout:
        line=line.rstrip("\n")
        if line.startswith("@@WAIT"):
            tag=line.split(" ",1)[1] if " " in line else ""
            best,total=smaps(p.pid)
            print(f"=== {tag} jitPoolSize={best['size'] if best else -1} jitPoolRss={best['rss'] if best else -1} jitPoolVMAs={best['n'] if best else -1} totalRss={total}", flush=True)
            p.stdin.write("\n"); p.stdin.flush()
        else:
            print(line, flush=True)
    p.wait()
main()
