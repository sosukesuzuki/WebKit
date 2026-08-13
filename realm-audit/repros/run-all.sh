#!/bin/sh
# Runs every realm reproducer against a jsc shell, taking per-script flags from the
# `//@ requireOptions(...)` header (the run-jsc-stress-tests convention).
# Usage: ./run-all.sh [/absolute/path/to/jsc]
JSC=${1:-jsc}
cd "$(dirname "$0")" || exit 1
for f in [0-9][0-9]-*.js; do
    flags=$(sed -n '1s#^//@ requireOptions(\(.*\))$#\1#p' "$f" | tr -d '",')
    echo "== $f $flags"
    "$JSC" $flags "$f"
done
