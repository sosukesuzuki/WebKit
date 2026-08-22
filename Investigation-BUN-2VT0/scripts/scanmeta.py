import struct, sys, collections
N=51
def rup(x,a): return (x+a-1)//a*a
def scan(path, limit=None):
    data=open(path,'rb').read()
    mv=memoryview(data)
    res=[]
    # candidates: u32 value 104 or 312 at 4-aligned offsets with preceding header
    import re
    for first in (104, 312):
        pat=struct.pack('<I', first)
        start=0
        while True:
            i=data.find(pat, start)
            if i<0: break
            start=i+1
            if i%4: continue
            h=i-8
            if h<0: continue
            hasMeta, is32, p1, p2, numVP = struct.unpack_from('<BBBBI', data, h)
            if hasMeta!=1 or is32 not in (0,1) or (is32==1)!=(first==312): continue
            offs=struct.unpack_from('<%dI'%N, data, i)
            if any(offs[k]>offs[k+1] for k in range(N-1)): continue
            if offs[-1] > 50_000_000: continue
            res.append((h, is32, numVP, offs))
            if limit and len(res)>=limit: break
    return res
if __name__=='__main__':
    path=sys.argv[1]
    res=scan(path)
    print(path, "tables found:", len(res))
    ops={26:'op_call',27:'op_call_ignore_result',13:'op_tail_call',5:'op_iterator_open',2:'op_iterator_next',11:'op_construct',21:'op_get_by_id',38:'op_get_by_val',42:'op_enumerator_next',0:'op_tail_call_varargs',1:'op_call_varargs',29:'op_resolve_scope'}
    for op,name in ops.items():
        sizes=collections.Counter()
        for h,is32,nvp,offs in res:
            sz=offs[op+1]-rup(offs[op],8)
            if sz>0: sizes[sz]+=1
        # gcd of observed sizes
        import math
        g=0
        for s in sizes: g=math.gcd(g,s)
        print(f"  {name:24s} regions={sum(sizes.values()):7d} gcd={g:4d} smallest={sorted(sizes)[:6]}")
