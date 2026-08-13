//@ requireOptions("--useShadowRealm=1")
// ShadowRealm.prototype.evaluate converts an abrupt completion into a TypeError of the caller realm by
// *copying the message*: createTypeErrorCopy (Error.cpp:273-292) reads the thrown value's own "message"
// data property and calls toWTFString() on it - i.e. runs shadow-realm user code - and if that throws,
// evalInRealm (ShadowRealmPrototype.cpp:128-130) propagates the new, raw shadow-realm exception.
// importValue's rejection handler @crossRealmThrow (ShadowRealmPrototype.js:57-63) does @toString(error)
// with the same effect.
if (typeof ShadowRealm !== "function") { print("SKIP: run with --useShadowRealm=1"); quit(); }
const r = new ShadowRealm();
function verdict(how, e) {
    if (e instanceof TypeError || e instanceof SyntaxError) return "PASS " + how + ": " + e.constructor.name + " from our realm";
    let extra = "";
    try { const F = typeof e === "function" ? e : e.constructor.constructor; extra = "; typeof shadow ShadowRealm via leaked %Function%: " + F("return typeof ShadowRealm")(); } catch { }
    return "FAIL " + how + ": raw shadow-realm value leaked (typeof " + typeof e + ")" + extra;
}
try { r.evaluate(`throw new Error("plain")`); } catch (e) { print(verdict("throw new Error('plain')", e)); }
try { r.evaluate(`throw { message: { toString() { throw Function; } } }`); } catch (e) { print(verdict("message.toString() throws %Function%", e)); }
try { r.evaluate(`throw { message: { [Symbol.toPrimitive]() { throw globalThis; } } }`); } catch (e) { print(verdict("message[@@toPrimitive] throws globalThis", e)); }
try { r.evaluate(`const e = new Error(); e.message = { toString() { throw Object; } }; throw e;`); } catch (e) { print(verdict("ErrorInstance with object message", e)); }
