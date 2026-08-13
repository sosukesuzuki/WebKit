load("realm-lib.js", "caller relative");
// %GeneratorPrototype%.next from realm A driving a generator created in realm B.
// Spec: the {value, done} objects produced by `yield` (27.5.3.7 GeneratorYield gets
// CreateIteratorResultObject evaluated *inside genContext*, whose Realm is the generator
// function's realm) and by the final return (GeneratorStart step "Return
// CreateIteratorResultObject(resultValue, true)", also in genContext) are realm-B objects.
// Only the "already completed" result (GeneratorResume step 2) is created in the caller's realm.
// JSC's @generatorResume builtin builds every result object as an object literal in the
// realm of the `next` function (A).  V8/SpiderMonkey allocate them in the generator's frame.
const gen = B.eval("(function* g() { yield 1; return 2; })")();
const nextA = Object.getPrototypeOf(function* () {}).prototype.next;   // A's %GeneratorPrototype%.next
check("realm of yield result", realmOf(nextA.call(gen)), "B");
check("realm of completion result", realmOf(nextA.call(gen)), "B");
check("realm of post-completion result", realmOf(nextA.call(gen)), "A");
