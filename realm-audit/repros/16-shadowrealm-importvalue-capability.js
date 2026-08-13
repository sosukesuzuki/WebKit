//@ requireOptions("--useShadowRealm=1", "-m")
// importInRealm (ShadowRealmPrototype.cpp:73-85) resolves an *incubating-realm* JSPromise with the shadow
// realm's module-namespace promise. When that promise fulfils with a thenable, the generic
// PromiseResolveThenableJob creates the resolving functions in the incubating realm and passes them to
// the shadow realm's `then` - two raw incubating functions cross the boundary. A module only has to
// make its namespace's fulfilment value look thenable on the second read of "then".
if (typeof ShadowRealm !== "function") { print("SKIP: run with --useShadowRealm=1"); quit(); }
globalThis.secret = "INCUBATING-SECRET";
const r = new ShadowRealm();
r.importValue("./resources/evil-module.js", "x")
    .then((v) => print("importValue fulfilled: " + v), (e) => print("importValue rejected: " + e.constructor.name))
    .then(() => print(r.evaluate("report")));
if (typeof drainMicrotasks === "function")
    drainMicrotasks();
