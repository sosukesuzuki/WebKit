#!/bin/bash
M=$(cd "$(dirname "$0")" && pwd)
WEBKIT=$(cd "$M/../../.." && pwd)
export JSC=${JSC:-$WEBKIT/WebKitBuild/JSCOnly-Release/bin/jsc}
cd "$WEBKIT/PerformanceTests/JetStream2" || exit 1
cp -n "$M/cli-mem.js" . 2>/dev/null
mkdir -p "$M/results"
TESTS="typescript Babylon acorn-wtb Air pdfjs octane-zlib ML raytrace splay gbemu"
declare -A CFG
CFG[default]=""
CFG[nosharing]="--useBaselineJITCodeSharing=0"
CFG[jit2000]="--thresholdForJITAfterWarmUp=2000 --thresholdForJITSoon=400"
CFG[jit5000]="--thresholdForJITAfterWarmUp=5000 --thresholdForJITSoon=1000"
CFG[nodfg]="--useDFGJIT=0"
CFG[noftl]="--useFTLJIT=0"
CFG[eagerjettison]="--forceCodeBlockToJettisonDueToOldAge=1 --useEagerCodeBlockJettisonTiming=1"
CFG[nojit]="--useJIT=0"
for cfg in default nosharing jit2000 jit5000 nodfg noftl eagerjettison nojit; do
  for t in $TESTS; do
    out=$M/results/${cfg}__${t}.log
    [ -s "$out" ] && continue
    CWD=. python3 $M/run.py --useDollarVM=1 ${CFG[$cfg]} $M/after3.js -e "testList='$t'" cli-mem.js > $out 2>&1
    echo "done $cfg $t"
  done
done
