import re,glob,os,json,sys
HERE=os.path.dirname(os.path.abspath(__file__))
rows=[]
for f in sorted(glob.glob(os.path.join(HERE,'results','*__*.log'))):
    cfg,test=os.path.basename(f)[:-4].split('__')
    t=open(f).read()
    r={'cfg':cfg,'test':test}
    for tag in ['beforeGC','afterGC']:
        m=re.search(r'=== %s jitPoolSize=(\d+) jitPoolRss=(-?\d+) jitPoolVMAs=-?\d+ totalRss=(\d+)'%tag,t)
        if m: r[tag+'_jitRss']=int(m.group(2)); r[tag+'_rss']=int(m.group(3))
        m=re.search(r'=== %s heapSize=(\d+) heapCapacity=(\d+) extraMemorySize=(\d+) objectCount=(\d+)'%tag,t)
        if m: r[tag+'_heap']=int(m.group(1)); r[tag+'_extra']=int(m.group(3)); r[tag+'_objs']=int(m.group(4))
        m=re.search(r'=== %s counts (.*)'%tag,t)
        if m:
            for kv in m.group(1).split(): k,v=kv.split('='); r[tag+'_'+k]=int(v)
        m=re.search(r'=== %s footprint current=(\d+) peak=(\d+)'%tag,t)
        if m: r[tag+'_fp']=int(m.group(1)); r[tag+'_peak']=int(m.group(2))
    for m in re.finditer(r'^\s+(\w+): (\d+)(?: \([^)]*\))?(?: count (\d+) avg size (\d+))?$', t, re.M):
        r['lb_'+m.group(1)]=int(m.group(2))
        if m.group(3): r['lbc_'+m.group(1)]=int(m.group(3))
    m=re.search(r'Score: ([\d.]+)',t)
    if m: r['score']=float(m.group(1))
    rows.append(r)
json.dump(rows,open(os.path.join(HERE,'results','summary.json'),'w'),indent=1)
if len(sys.argv)>1:
    cols=sys.argv[1].split(',')
    print('cfg,test,'+','.join(cols))
    for r in rows: print(r['cfg'],r['test'],*[r.get(c,'') for c in cols],sep=',')
