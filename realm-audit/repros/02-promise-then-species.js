load("realm-lib.js", "caller relative");
// Promise.prototype.then/catch/finally applied to a promise from realm B.
// Spec (27.2.5.4): C = SpeciesConstructor(promise, %Promise%) => promise.constructor
// is B.Promise => B.Promise[@@species] => B.Promise, so the derived promise is a
// realm-B promise. JSC (JSPromise::then / promiseSpeciesConstructor): if B's species
// watchpoint is intact it skips the lookup and allocates with
// globalObject->promiseStructure() of the *calling* realm A.
const bP = B.Promise.resolve(1);
check("realm of Promise.prototype.then.call(bP)", realmOf(Promise.prototype.then.call(bP)), "B");
check("realm of Promise.prototype.catch.call(bP, f)", realmOf(Promise.prototype.catch.call(bP, () => {})), "B");
check("realm of Promise.prototype.finally.call(bP, f)", realmOf(Promise.prototype.finally.call(bP, () => {})), "B");
check("derived instanceof B.Promise", Promise.prototype.then.call(bP) instanceof B.Promise, true);
// Contrast: JSC's own Promise.resolve / Promise.all handle the foreign realm correctly.
check("Promise.resolve(bP) !== bP (correctly wraps)", Promise.resolve(bP) !== bP, true);
// And it flips once B's species watchpoint is invalidated by a semantic no-op:
B.eval("const c = Promise.prototype.constructor; delete Promise.prototype.constructor; Promise.prototype.constructor = c;");
check("after no-op reshuffle in B: realm of then.call(bP)", realmOf(Promise.prototype.then.call(bP)), "B");
