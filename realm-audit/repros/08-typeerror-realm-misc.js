load("realm-lib.js", "caller relative");
// A grab bag of TypeErrors created in the wrong realm.
// (a) `new` on a non-constructor: EvaluateNew step 7 throws in the *caller's* realm.
//     JSC routes host functions through the callee's construct trampoline
//     (callHostFunctionAsConstructor) so the error comes from the callee's realm,
//     while non-constructor *JS* functions correctly throw from the caller's realm.
check("new B.Math.max()  (host fn)", realmOfThrown(() => new B.Math.max()), "A");
check("new (B arrow fn)   (JS fn, control)", realmOfThrown(() => new (B.eval("() => 1"))()), "A");
// (b) Calling a revoked Proxy: ProxyCreate'd in B, called from A. [[Call]] step 2 throws in the
//     current (caller's) realm; JSC throws from the proxy's realm for [[Call]] but from the
//     caller's realm for [[Construct]] - inconsistent with itself.
const { proxy, revoke } = B.Proxy.revocable(function () {}, {}); revoke();
check("call revoked B proxy", realmOfThrown(() => proxy()), "A");
check("construct revoked B proxy (control)", realmOfThrown(() => new proxy()), "A");
// (c) Array.prototype.toString fast path: `func = Get(array, "join")` is B's join for a B array,
//     so B's join runs and its ToString(Symbol) TypeError is a realm-B error. JSC recognises
//     "join is the native arrayProtoFuncJoin" by C function pointer (any realm) and runs the
//     fast join in realm A instead.
check("Array.prototype.toString.call(bArrayWithSymbol)", realmOfThrown(() => Array.prototype.toString.call(new B.Array(Symbol()))), "B");
