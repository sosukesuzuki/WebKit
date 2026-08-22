#!/bin/bash
BUN=/home/user/bun/build/release-local/bun-assertions
cd /home/user/bun/test
export BUN_DEBUG_QUIET_LOGS=1
for d in js/bun/jsc-stress js/bun/gc js/bun/jsc js/bun/util js/bun/globals.test.js js/node/util js/node/events js/node/stream js/node/buffer js/node/path js/node/url js/node/string_decoder js/node/querystring js/node/assert js/web/encoding js/web/url js/web/streams js/bun/console js/bun/test js/bun/http js/bun/fetch js/node/fs js/node/http js/node/child_process js/web/fetch js/bun/net js/bun/util js/third_party js/first_party; do
  log=/home/user/work/test-logs/$(echo $d | tr '/' '_').log
  mkdir -p /home/user/work/test-logs
  echo "=== $d $(date +%T)"
  timeout 1800 $BUN test --timeout 20000 $d > $log 2>&1; rc=$?
  if grep -q "BUN-2VT0\|garbage cell\|ASSERTION FAILED\|RELEASE_ASSERT\|panic(main" $log; then echo "!!! HIT in $d rc=$rc"; grep -n "BUN-2VT0\|garbage cell\|ASSERTION FAILED\|panic(main" $log | head -5; fi
  echo "done $d rc=$rc $(grep -E '^ *[0-9]+ pass|^ *[0-9]+ fail' $log | tr '\n' ' ')"
done
echo "TESTS FINISHED"
