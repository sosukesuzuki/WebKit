import sys,re
# usage: showlayout.py layouts.txt JSC::Type ...   (layouts.txt = clang -Xclang -fdump-record-layouts output of sizes.cpp)
txt=open(sys.argv[1]).read()
blocks=txt.split('*** Dumping AST Record Layout')
want=sys.argv[2:]
for b in blocks:
    m=re.search(r'^\s*0 \| (class|struct|union) (\S+)', b, re.M)
    if not m: continue
    name=m.group(2)
    if name in want:
        print('*** Dumping AST Record Layout'+b.rstrip()); print()
