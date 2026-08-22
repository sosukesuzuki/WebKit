#!/bin/bash
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
# usage: stress.sh <jsc> <label> <outdir>  — runs a fixed sample of JSTests/stress in ftl-eager mode
JSC=$1; LABEL=$2; OUT=$3; mkdir -p "$OUT"
cd $ROOT/JSTests/stress
OPTS="--useConcurrentJIT=false --thresholdForJITAfterWarmUp=10 --thresholdForJITSoon=10 --thresholdForOptimizeAfterWarmUp=20 --thresholdForOptimizeAfterLongWarmUp=20 --thresholdForOptimizeSoon=20 --thresholdForFTLOptimizeAfterWarmUp=20 --thresholdForFTLOptimizeSoon=20 --maximumEvalCacheableSourceLength=150000 --useEagerCodeBlockJettisonTiming=true"
: > "$OUT/$LABEL-stress.txt"
while read -r t; do
  timeout 120 "$JSC" $OPTS "$t" > /dev/null 2>&1; rc=$?
  echo "$rc $t" >> "$OUT/$LABEL-stress.txt"
done < $HERE/stress-list.txt
echo "$LABEL: $(grep -c '^0 ' "$OUT/$LABEL-stress.txt") passed of $(wc -l < "$OUT/$LABEL-stress.txt")"
