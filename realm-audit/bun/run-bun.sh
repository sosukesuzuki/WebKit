#!/bin/sh
# Runs the realm reproducers under Bun (or Node: RUNTIME=node) via the node:vm harness.
# JSC shell flags in each script's //@ requireOptions header become BUN_JSC_* environment variables.
RUNTIME=${RUNTIME:-bun}
HERE=$(cd "$(dirname "$0")" && pwd)
REPROS=${REPROS:-$HERE/../repros}
for f in "$REPROS"/[0-9][0-9]-*.js; do
    name=$(basename "$f")
    envs=$(sed -n '1s#^//@ requireOptions(\(.*\))$#\1#p' "$f" | tr -d '",' | tr ' ' '\n' | sed -n 's/^--\(.*\)$/BUN_JSC_\1/p' | tr '\n' ' ')
    echo "== $RUNTIME $name ${envs}"
    case "$name" in
        06-*) echo "N/A  (needs the shell's makeMasquerader(); Bun/Node expose no [[IsHTMLDDA]] object)"; continue ;;
        18-*) [ "$RUNTIME" = bun ] && bun "$HERE/18-bun-realm-leak.mjs" || echo "N/A"; continue ;;
        16-*) env $envs "$RUNTIME" "$HERE/run16.mjs" "$f" 2>&1; continue ;;
    esac
    env $envs "$RUNTIME" "$HERE/harness.js" "$f" 2>&1
done
