//@ requireOptions("--useConcurrentJIT=0")
load("tier-lib.js", "caller relative");
// foreignPromise.then(...) — perfectly ordinary code when promises cross iframes.
// LLInt/Baseline call realm B's Promise.prototype.then, which allocates the derived
// promise in realm B.  DFG inlines PromisePrototypeThenIntrinsic into a PromiseThen node
// (DFGByteCodeParser.cpp ~5564, no calleeMayBeCrossRealm guard; PromiseObjectUse is only a
// JSType check) and the backend calls operationPromiseThen(lexical realm A) ->
// JSPromise::then(A) -> JSPromise::create(vm, A->promiseStructure()).
const bP = B.Promise.resolve(1);
tierCheck("realm of bPromise.then()", (p) => realmOf(p.then()), bP, "B");
tierCheck("realm of bPromise.then(f, g)", (p) => realmOf(p.then(x => x, e => e)), bP, "B");
tierCheck("bPromise.then() instanceof B.Promise", (p) => p.then() instanceof B.Promise, bP, true);
