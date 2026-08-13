//@ requireOptions("--useConcurrentJIT=0")
load("tier-lib.js", "caller relative");
// Intrinsics that allocate but were left out of the calleeMayBeCrossRealm() sweep.
// Their siblings (Object.keys/getOwnPropertyNames/getOwnPropertySymbols, Array iterators, ...)
// are guarded; these are not, so the realm of the result changes on tier-up.
const ownKeys = B.Reflect.ownKeys, keys = B.Object.keys, gpo = B.Object.getPrototypeOf, assign = B.Object.assign;
tierCheck("realm of B.Reflect.ownKeys(o)", (o) => realmOf(ownKeys(o)), { a: 1 }, "B");
tierCheck("realm of B.Object.keys(o)      (guarded sibling, control)", (o) => realmOf(keys(o)), { a: 1 }, "B");
tierCheck("B.Object.getPrototypeOf(1) === B.Number.prototype", (v) => gpo(v) === B.Number.prototype, 1, true);
tierCheck("B.Object.getPrototypeOf('s') === B.String.prototype", (v) => gpo(v) === B.String.prototype, "s", true);
tierCheck("realm of B.Object.assign(5, null) (ToObject wrapper)", (v) => realmOf(assign(v, null)), 5, "B");
// ...and the TypeErrors/RangeErrors thrown by unguarded intrinsics move realm too:
const create = B.Object.create, fromCodePoint = B.String.fromCodePoint;
tierCheck("realm of TypeError from B.Object.create(42)", (v) => realmOfThrown(() => create(v)), 42, "B");
tierCheck("realm of RangeError from B.String.fromCodePoint(-1)", (v) => realmOfThrown(() => fromCodePoint(v)), -1, "B");
