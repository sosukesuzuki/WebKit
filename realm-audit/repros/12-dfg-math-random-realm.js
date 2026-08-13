//@ requireOptions("--useConcurrentJIT=0", "--forceWeakRandomSeed=1", "--forcedWeakRandomSeed=42")
load("realm-lib.js", "caller relative");
// Math.random has per-realm PRNG state (JSGlobalObject::m_weakRandom). LLInt/Baseline's Math.random
// thunk loads the realm from the *callee* (AssemblyHelpers::emitRandomThunk(VM&)); DFG/FTL's ArithRandom
// bakes in m_graph.globalObjectFor(origin), the *caller's* realm (DFGSpeculativeJIT64.cpp compileArithRandom),
// and RandomIntrinsic has no calleeMayBeCrossRealm() guard.
// Method: with --forceWeakRandomSeed every realm starts from the same stream. Draw N+1 numbers through
// `() => B.Math.random()` from realm A (the last draws are DFG-compiled), then replay N+1 draws inside a
// fresh realm E. If every draw advanced B's generator the last values agree; if the hot draws came from
// A's generator instead, they cannot.
const N = 100000;
function lastOfStreamVia(f) { let x; for (let i = 0; i <= N; ++i) x = f(); return x; }
const randomB = B.Math.random;
const cold = B.eval("(n) => { let v; for (let i = 0; i <= n; ++i) v = Math.random(); return v; }");   // runs inside B: control
const viaA = () => randomB();                                                                       // called from A: the probe
const expected = newRealm("E").eval("(n) => { let v; for (let i = 0; i <= n; ++i) v = Math.random(); return v; }")(N);
check("control: N+1 draws of Math.random inside B match a fresh realm's stream", cold(N) === expected, true);
const B2 = newRealm("B2"), randomB2 = B2.Math.random, viaA2 = () => randomB2();
check("N+1 draws of B2.Math.random() from A (hot) match a fresh realm's stream", lastOfStreamVia(viaA2) === expected, true);
