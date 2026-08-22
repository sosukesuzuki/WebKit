#!/bin/bash
# usage: run.sh <jsc> <label> <outdir> [which: js|wasm|pglite|all]
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
JSC=$1; LABEL=$2; OUT=$3; WHICH=${4:-all}
mkdir -p "$OUT"
JS_TESTS='["Box2D","crypto","delta-blue","earley-boyer","gbemu","navier-stokes","pdfjs","raytrace","richards","splay","typescript","octane-zlib","mandreel","FlightPlanner","OfflineAssembler","UniPoker","float-mm.c","hash-map","ai-astar","gaussian-blur","stanford-crypto-aes","stanford-crypto-sha256","Air","Basic","ML","Babylon","cdjs","async-fs"]'
WASM_TESTS='["HashSet-wasm","tsf-wasm","quicksort-wasm","gcc-loops-wasm","richards-wasm"]'
COMMON="JSC_reportTotalPhaseTimes=1"
if [ "$WHICH" = js ] || [ "$WHICH" = all ]; then
  ( cd $ROOT/PerformanceTests/JetStream2 && python3 $HERE/rusage.py env $COMMON JSC_useConcurrentJIT=0 "$JSC" -e "testList=$JS_TESTS" cli.js ) > "$OUT/$LABEL-js.txt" 2>&1
fi
if [ "$WHICH" = wasm ] || [ "$WHICH" = all ]; then
  ( cd $ROOT/PerformanceTests/JetStream2 && python3 $HERE/rusage.py env $COMMON JSC_useConcurrentJIT=0 JSC_numberOfWasmCompilerThreads=1 "$JSC" -e "testList=$WASM_TESTS" cli.js ) > "$OUT/$LABEL-wasm.txt" 2>&1
fi
if [ "$WHICH" = pglite ] || [ "$WHICH" = all ]; then
  ( cd $ROOT/JSTests/wasm/stress && python3 $HERE/rusage.py env $COMMON JSC_useConcurrentJIT=0 JSC_numberOfWasmCompilerThreads=1 JSC_thresholdForOMGOptimizeAfterWarmUp=200 JSC_thresholdForOMGOptimizeSoon=20 "$JSC" pglite.js ) > "$OUT/$LABEL-pglite.txt" 2>&1
fi
echo done $LABEL
