# JavaScriptCore realm audit

Report: `jsc-realm-audit.html` (self-contained; the published copy lives at
https://claude.ai/code/artifact/0c3f0c7f-8fb8-44d3-9283-a938c5610bef).
Japanese edition: `jsc-realm-audit.ja.html`
(https://claude.ai/code/artifact/c01aeac3-445a-4832-a7b5-34f4dab105ec).

`repros/` holds one jsc-shell reproducer per finding (F1-F18). Each prints
`PASS`/`FAIL` lines; `FAIL` means the bug reproduced. Per-script shell flags are
declared in the first-line `//@ requireOptions(...)` header (the
run-jsc-stress-tests convention), and `load()`s are caller-relative, so scripts
run from any directory:

```
Tools/Scripts/build-jsc --jsc-only --release
realm-audit/repros/run-all.sh /absolute/path/to/jsc      # everything
jsc --useConcurrentJIT=0 realm-audit/repros/09-dfg-promise-then.js
```

`bun/` runs the same scripts under Bun (or Node, `RUNTIME=node`) by mapping the
shell primitives onto `node:vm` (`createGlobalObject()` -> a fresh
`vm.createContext()` global) and the `//@` flags onto `BUN_JSC_*` environment
variables:

```
realm-audit/bun/run-bun.sh
```

| Script | Finding |
| --- | --- |
| 01-string-regexp-fastpath.js | F6 `String.prototype` x foreign RegExp fast paths |
| 02-promise-then-species.js | F7 `Promise.prototype.then/catch/finally` species |
| 03-arraybuffer-slice-species.js | F8 `ArrayBuffer.prototype.slice` species |
| 04-wasm-memory-buffer.js | F9 `WebAssembly.Memory.prototype.buffer` realm |
| 05-function-caller-cross-realm.js | F1 `Function.prototype.caller` (ShadowRealm escape) |
| 06-masquerader-cross-realm.js | F12 masquerades-as-undefined is realm-relative |
| 07-generator-result-realm.js | F10 generator result objects |
| 08-typeerror-realm-misc.js | F11 wrong-realm TypeErrors |
| 09-dfg-promise-then.js | F2 DFG `PromiseThen` intrinsic |
| 10-dfg-string-regexp-intrinsics.js | F3 DFG String/RegExp intrinsics |
| 11-dfg-unguarded-alloc-intrinsics.js | F4 unguarded DFG intrinsics |
| 12-dfg-math-random-realm.js | F5 DFG `Math.random` |
| 13-shadowrealm-exception-sanitization.js | F13 ShadowRealm exception sanitisation |
| 14-shadowrealm-generic-wrap-realm.js | F14 ShadowRealm generic call wrapping |
| 15-shadowrealm-message-tostring.js | F15 ShadowRealm `evaluate` message copy |
| 16-shadowrealm-importvalue-capability.js (+ resources/evil-module.js) | F16 ShadowRealm `importValue` capability |
| 17-getfunctionrealm-structure-vs-scope.js | F17 `getFunctionRealm()` |
| 18-realm-leak-cached-structures.js | F18 realm leaks via cached Structures |

`realm-lib.js` (realm registry, `realmOf`, `check`) and `tier-lib.js`
(cold-vs-hot `tierCheck`) are the shared helpers.
