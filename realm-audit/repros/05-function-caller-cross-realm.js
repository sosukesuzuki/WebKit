//@ requireOptions("--useShadowRealm=1")
// Function.prototype.caller hands out functions that belong to *other* realms.
// The de-facto spec JSC cites in FunctionPrototype.cpp
// (github.com/claudepache/es-legacy-function-reflection) says:
//   get Function.prototype.caller, step 13: If caller.[[Realm]] is not currentRealm, return null.
// JSC implements steps 11, 12 and 14 around it but not 13, and RetrieveCallerFunctionFunctor
// additionally *skips over* JSRemoteFunction (ShadowRealm wrapper) frames instead of stopping
// at them.  With --useShadowRealm=1 this is a complete callable-boundary escape.
load("realm-lib.js", "caller relative");
const innerProbe = B.eval("(function probe() { return probe.caller; })");
function outerSloppy() { return innerProbe(); }
const leaked = outerSloppy();
check("plain realms: B function's .caller for a caller from realm A", leaked && "function " + leaked.name + " from realm " + realmOf(leaked), null);

if (typeof ShadowRealm === "function") {
    const r = new ShadowRealm();
    const probe = r.evaluate(`(function g() { globalThis.leak = g.caller; })`);
    (function hostSloppy() { return probe(); })();
    const verdict = r.evaluate(`(function () {
        if (typeof leak !== "function") return "PASS no object crossed the boundary";
        const OuterFunction = leak.constructor;               // incubating realm's %Function%
        const outerGlobal = OuterFunction("return globalThis")();
        return "FAIL escaped ShadowRealm: outer globalThis reachable, outer ShadowRealm ctor is " + typeof outerGlobal.ShadowRealm;
    })`)();
    print(verdict);
    // Reverse direction: the incubating realm grabs a function object living inside the ShadowRealm.
    let innerFn = null;
    function hostCallback() { innerFn = hostCallback.caller; }
    r.evaluate(`(cb) => (function innerSloppy() { cb(); })()`)(hostCallback);
    print(innerFn === null ? "PASS reverse direction: hostCallback.caller is null"
                           : "FAIL reverse escape: got inner function '" + innerFn.name + "', inner globalThis.leak type = " + typeof innerFn.constructor("return globalThis")().leak);
} else
    print("NOTE run with --useShadowRealm=1 to see the ShadowRealm boundary escape");
