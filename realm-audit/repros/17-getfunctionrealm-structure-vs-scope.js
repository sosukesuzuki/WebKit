load("realm-lib.js", "caller relative");
// getFunctionRealm() (InternalFunction.cpp:198-227) answers `object->realm()`, i.e. the realm recorded in
// the function's *Structure*. A JSFunction's [[Realm]] is really its scope's global object, and the two
// differ for functions created by `Reflect.construct(OtherRealm.Function, [src], newTarget)`: the structure
// comes from GetPrototypeFromConstructor(newTarget) (realm C) while the function is created by, scoped to,
// and runs in realm B. Ordinary [[Construct]] (op_create_this -> prototypeForConstruction) uses the scope
// realm, InternalFunction constructors use getFunctionRealm(), so JSC disagrees with itself.
const C = newRealm("C");
const nt = C.eval("(function nt() {})"); nt.prototype = null;
const f = Reflect.construct(B.Function, ["return 1"], nt);   // f.[[Realm]] = B, f.[[Prototype]] = C.Function.prototype
f.prototype = 42;                                             // force the GetFunctionRealm(f) fallback
check("new f()                          -> %Object.prototype% of", realmOf(new f()), "B");
check("Reflect.construct(Object, [], f) -> %Object.prototype% of", realmOf(Reflect.construct(Object, [], f)), "B");
check("Reflect.construct(Array, [], f)  -> %Array.prototype% of", realmOf(Reflect.construct(Array, [], f)), "B");
check("Reflect.construct(Date, [], f)   -> %Date.prototype% of", realmOf(Reflect.construct(Date, [], f)), "B");
