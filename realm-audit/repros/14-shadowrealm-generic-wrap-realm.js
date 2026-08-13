//@ requireOptions("--useShadowRealm=1")
// remoteFunctionCallGeneric (used when the wrapped target is not a JSFunction: callable Proxy,
// InternalFunction, API object) wraps the *return value* with
// wrapReturnValue(globalObject, targetGlobalObject, result)  (JSRemoteFunction.cpp:158)
// while remoteFunctionCallForJSFunction correctly uses (globalObject, globalObject) at :122.
// The caller therefore receives a JSRemoteFunction that belongs to the *other* realm.
if (typeof ShadowRealm !== "function") { print("SKIP: run with --useShadowRealm=1"); quit(); }
const r = new ShadowRealm();
const viaJSFunction = r.evaluate(`(function () { return function inner() {}; })`);
const viaProxy      = r.evaluate(`new Proxy(function () {}, { apply() { return function inner() {}; } })`);
print((Object.getPrototypeOf(viaJSFunction()) === Function.prototype ? "PASS" : "FAIL") + " JSFunction target: returned wrapper uses our Function.prototype");
const w = viaProxy();
const ok = Object.getPrototypeOf(w) === Function.prototype;
print((ok ? "PASS" : "FAIL") + " Proxy target: returned wrapper uses our Function.prototype");
if (!ok) {
    const ShadowFunction = Object.getPrototypeOf(w).constructor;
    const innerGlobal = ShadowFunction("return globalThis")();
    print("      -> Object.getPrototypeOf(wrapper).constructor is a foreign %Function%; it hands us the ShadowRealm's raw globalThis: " + (innerGlobal !== globalThis && typeof innerGlobal === "object"));
}
