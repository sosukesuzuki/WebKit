function shouldBe(actual, expected) {
    if (actual !== expected)
        throw new Error(`expected ${expected} but got ${actual}`);
}

let other = createGlobalObject();
let callable = other.eval("new Proxy(function () { }, { apply(target, thisValue, args) { return args; }, construct(target, args) { return args; } })");
let otherProxyOfCallable = other.eval("(function (target) { return new Proxy(target, {}); })")(callable);
let otherBoundCallable = other.Function.prototype.bind.call(callable);
let callFromOther = other.eval("(function (f) { return f(); })");

function call(f) { return f(1, 2); }
noInline(call);
function construct(f) { return new f(1, 2); }
noInline(construct);

for (let i = 0; i < testLoopCount; ++i) {
    // Proxy's [[Call]] and [[Construct]] do not switch the realm.
    shouldBe(Object.getPrototypeOf(call(callable)), Array.prototype);
    shouldBe(Object.getPrototypeOf(construct(callable)), Array.prototype);
    shouldBe(Object.getPrototypeOf(callFromOther(callable)), other.Array.prototype);
    // Built-in functions have their own realms.
    shouldBe(Object.getPrototypeOf(Reflect.apply(callable, null, [])), Array.prototype);
    shouldBe(Object.getPrototypeOf(other.Reflect.construct(callable, [])), other.Array.prototype);
    shouldBe(Object.getPrototypeOf([0].map(callable)[0]), Array.prototype);
    shouldBe(Object.getPrototypeOf(other.Array.prototype.map.call([0], callable)[0]), other.Array.prototype);
    // Proxies and bound functions do not have their own execution contexts.
    shouldBe(Object.getPrototypeOf(call(otherProxyOfCallable)), Array.prototype);
    shouldBe(Object.getPrototypeOf(call(otherBoundCallable)), Array.prototype);
}
