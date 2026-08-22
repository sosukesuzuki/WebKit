#!/bin/bash
# usage: checkcc2.sh <pkg> <version> <N> <opsfile>
p=$1; v=$2; N=$3; OPS=$4
t=$(curl -sS "https://registry.npmjs.org/@anthropic-ai/claude-code-$p/$v" | python3 -c "import json,sys;print(json.load(sys.stdin)['dist']['tarball'])")
rm -rf /tmp/ccchk; mkdir -p /tmp/ccchk; curl -sS "$t" | tar -xz -C /tmp/ccchk 2>/dev/null
bin=$(ls /tmp/ccchk/package/claude* | head -1)
bunver=$(strings -n 8 "$bin" | grep -oE "^1\.[0-9]+\.[0-9]+(-canary(\.[0-9]+)?)?\+[0-9a-f]{9}$" | head -1)
python3 - "$bin" <<'PY'
import sys; sys.path.insert(0,'/tmp')
from parsegraph import parse
data, base, files, flags = parse(sys.argv[1]); name,f=files[0]
open('/tmp/ccchk/bc.bin','wb').write(data[base+f[6]: base+f[6]+f[7]])
print("bytecode bytes:", f[7])
PY
echo "$p $v bun=$bunver"; python3 /tmp/scanmeta2.py /tmp/ccchk/bc.bin "$N" "$OPS"
rm -rf /tmp/ccchk
