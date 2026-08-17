import re,sys,glob,os,json
out={}
for f in sorted(glob.glob('results/instr__*.log')):
    t=os.path.basename(f)[7:-4]
    agg={'DFG':{}, 'FTL':{}}
    txt=open(f).read()
    for l in txt.splitlines():
        if not l.startswith('RETAINED'): continue
        parts=l.split()
        tier=parts[1]
        d=agg[tier]
        d['count']=d.get('count',0)+1
        for kv in parts[2:]:
            if '=' not in kv: continue
            k,v=kv.split('=',1)
            try: v=int(v)
            except: continue
            d[k]=d.get(k,0)+v
    # metadata stats
    m=re.search(r'total memory: (\d+)\n\t of which due to multiple linked copies: (\d+)\n# of unlinked metadata tables created: (\d+)\n# of which were 32bit: (\d+)\n# of copies from linking: (\d+)',txt)
    meta={}
    if m: meta={'total':int(m.group(1)),'copies':int(m.group(2)),'tables':int(m.group(3)),'is32':int(m.group(4)),'ncopies':int(m.group(5))}
    per={}
    for mm in re.finditer(r'(op_\w+):\n\tnumber of entries: (\d+)\n\tmemory usage: (\d+)',txt):
        per[mm.group(1)]=(int(mm.group(2)),int(mm.group(3)))
    meta['per']=per
    out[t]={'retained':agg,'meta':meta}
json.dump(out,open(os.path.join(HERE,'results','retained.json'),'w'),indent=1)
for t,v in out.items():
    print("==",t)
    for tier in ['DFG','FTL']:
        d=v['retained'][tier]
        if not d: continue
        print(tier, {k:d[k] for k in sorted(d)})
    mt=v['meta']; print("meta total=%s copies=%s tables=%s copiesN=%s"%(mt.get('total'),mt.get('copies'),mt.get('tables'),mt.get('ncopies')))
    per=sorted(mt['per'].items(), key=lambda kv:-kv[1][1])[:8]
    print("  top:", ", ".join(f"{k}:{n}x={b}" for k,(n,b) in per))
