import struct, sys, collections, math
def rup(x,a): return (x+a-1)//a*a
def scan(path, N):
    data=open(path,'rb').read()
    E=N+1
    first16=rup(E*2,4); first32=first16+rup(E*4,8)
    res=[]
    for first in (first16, first32):
        pat=struct.pack('<I', first); start=0
        while True:
            i=data.find(pat, start)
            if i<0: break
            start=i+1
            if i%4 or i<8: continue
            hasMeta, is32, p1, p2, numVP = struct.unpack_from('<BBBBI', data, i-8)
            if hasMeta!=1 or is32 not in (0,1) or (is32==1)!=(first==first32): continue
            if i+4*E>len(data): continue
            offs=struct.unpack_from('<%dI'%E, data, i)
            if any(offs[k]>offs[k+1] for k in range(E-1)) or offs[-1]>50_000_000: continue
            res.append((i-8, is32, numVP, offs))
    return res
if __name__=='__main__':
    path, N, opsfile = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    ops={}
    for line in open(opsfile):
        i,n=line.split(); ops[n]=int(i)
    res=scan(path, N)
    print("tables:", len(res))
    for name in ['op_call','op_call_ignore_result','op_tail_call','op_construct','op_iterator_open','op_iterator_next','op_call_varargs','op_get_by_id','op_get_by_val']:
        if name not in ops: continue
        op=ops[name]; sizes=collections.Counter()
        for h,is32,nvp,offs in res:
            sz=offs[op+1]-rup(offs[op],8)
            if sz>0: sizes[sz]+=1
        top=sorted(s for s,_ in sizes.most_common(5))
        print(f"  {name:22s} idx={op:2d} regions={sum(sizes.values()):6d} top_sizes={top}")
