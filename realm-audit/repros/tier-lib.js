load("realm-lib.js", "caller relative");
// Runs f(arg) once cold (LLInt) and then 1e5 times, enough to reach DFG/FTL with the default
// thresholds, and reports whether the answer changed with the tier. Run with --useConcurrentJIT=0
// (the //@ requireOptions line of each script) so the optimizing compile has landed by the last call.
function tierCheck(label, f, arg, expected) {
    const cold = f(arg);
    let hot; for (let i = 0; i < 100000; ++i) hot = f(arg);
    const flip = String(cold) !== String(hot);
    const ok = String(hot) === String(expected) && String(cold) === String(expected);
    print((ok ? "PASS " : "FAIL ") + label + ": LLInt=" + cold + " DFG/FTL=" + hot + " expected=" + expected + (flip ? "   <== changes with JIT tier" : ""));
    if (typeof numberOfDFGCompiles === "function" && !numberOfDFGCompiles(f))
        print("NOTE " + label + ": the probe never reached DFG; rerun with --useConcurrentJIT=0");
}
