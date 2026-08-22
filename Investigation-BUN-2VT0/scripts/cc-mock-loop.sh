#!/bin/bash
BUN=/home/user/bun/build/release-local/bun-assertions
mkdir -p /home/user/work/cc-mock-logs
i=0
while true; do
for opts in "" "BUN_JSC_collectContinuously=1" "BUN_JSC_useEagerCodeBlockJettisonTiming=1 BUN_JSC_useExecutionCountForCodeBlockAging=1" "BUN_JSC_thresholdForJITAfterWarmUp=10 BUN_JSC_thresholdForOptimizeAfterWarmUp=20 BUN_JSC_thresholdForFTLOptimizeAfterWarmUp=100" "BUN_JSC_collectContinuously=1 BUN_JSC_useEagerCodeBlockJettisonTiming=1" "BUN_JSC_useConcurrentJIT=0 BUN_JSC_forceCodeBlockToJettisonDueToOldAge=1" "BUN_JSC_largeHeapSize=1048576 BUN_JSC_collectContinuously=1"; do
  i=$((i+1)); log=/home/user/work/cc-mock-logs/sess-$i.log
  (cd /tmp/ccwork && env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy -u NO_PROXY -u no_proxy $opts ANTHROPIC_API_KEY=sk-ant-bogus ANTHROPIC_BASE_URL=http://127.0.0.1:8787 HOME=/tmp/cchome CI=1 TERM=dumb DISABLE_AUTOUPDATER=1 CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 timeout 900 $BUN /tmp/src-cc-linux-x64.js -p "do the work" --max-turns 45 --output-format stream-json --verbose < /dev/null > $log 2>&1); rc=$?
  turns=$(grep -c '"type":"assistant"' $log)
  if grep -q "BUN-2VT0\|garbage cell\|panic(\|Segmentation\|ASSERTION FAILED\|RELEASE_ASSERT" $log; then echo "!!! HIT sess=$i opts=[$opts] rc=$rc log=$log"; grep -n "BUN-2VT0\|garbage\|panic(\|ASSERTION" $log | head -5; fi
  echo "sess=$i opts=[$opts] rc=$rc assistant_turns=$turns $(date +%T)"
done
done
