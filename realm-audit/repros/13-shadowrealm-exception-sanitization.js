//@ requireOptions("--useShadowRealm=1")
// Exceptions crossing a ShadowRealm boundary are only replaced by a fresh TypeError when the JS
// *unwinder* walks past the JSRemoteFunction frame (Interpreter.cpp:875-985). When the wrapper is
// invoked from C++ (getter, valueOf/toString, sort comparator, promise reaction, replace callback,
// ...), the target runs in a nested VM entry, remoteFunctionCallForJSFunction just does
// RETURN_IF_EXCEPTION (JSRemoteFunction.cpp:119-120), and the raw error object reaches the other realm.
if (typeof ShadowRealm !== "function") { print("SKIP: run with --useShadowRealm=1"); quit(); }
const r = new ShadowRealm();
const thrower = r.evaluate(`(function thrower() { throw { F: Function }; })`);   // F = shadow realm's %Function%
function verdict(how, e) {
    if (e instanceof TypeError) return "PASS " + how + ": sanitized TypeError";
    const escaped = e && e.F && e.F("return globalThis")() !== globalThis;
    return "FAIL " + how + ": raw shadow-realm object leaked" + (escaped ? " (its .F compiles code inside the ShadowRealm)" : "");
}
try { thrower(); } catch (e) { print(verdict("direct call", e)); }
try { Object.defineProperty({}, "x", { get: thrower }).x; } catch (e) { print(verdict("as getter", e)); }
try { +{ valueOf: thrower }; } catch (e) { print(verdict("as valueOf", e)); }
try { [2, 1].sort(thrower); } catch (e) { print(verdict("as sort comparator", e)); }
try { "abc".replace(/b/, thrower); } catch (e) { print(verdict("as replace callback", e)); }
Promise.resolve().then(thrower).catch((e) => print(verdict("as promise reaction", e)));
drainMicrotasks();
// Reverse direction: code *inside* the ShadowRealm catches a raw incubating-realm Error from any callback.
globalThis.secret = "INCUBATING-SECRET";
const inside = r.evaluate(`(function (cb) {
    try { +{ valueOf: cb }; } catch (e) {
        if (e instanceof TypeError) return "PASS inside: sanitized";
        try { return "FAIL inside: escaped, outer secret = " + e.constructor.constructor("return globalThis.secret")(); }
        catch (e2) { return "FAIL inside: raw foreign object (" + e2 + ")"; }
    }
    return "no throw?";
})`);
print(inside(JSON.parse));                        // JSON.parse(undefined) throws an incubating SyntaxError
print(inside(function (x) { return x.foo.bar; })); // ordinary incubating TypeError
