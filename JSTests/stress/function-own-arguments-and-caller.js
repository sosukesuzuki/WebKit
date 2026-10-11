function shouldBe(actual, expected) {
    if (actual !== expected)
        throw new Error(`expected ${expected} but got ${actual}`);
}

function shouldThrowTypeError(func) {
    let error;
    try {
        func();
    } catch (e) {
        error = e;
    }
    if (!(error instanceof TypeError))
        throw new Error(`expected a TypeError but got ${error}`);
}

let thrower = Object.getOwnPropertyDescriptor(function () { "use strict"; return arguments; }(), "callee").get;
for (let name of ["arguments", "caller"]) {
    let descriptor = Object.getOwnPropertyDescriptor(Function.prototype, name);
    shouldBe(descriptor.get, thrower);
    shouldBe(descriptor.set, thrower);
    shouldBe(descriptor.enumerable, false);
    shouldBe(descriptor.configurable, true);
}

{
    function sloppy() { }
    sloppy.foo = 1;
    shouldBe(Reflect.ownKeys(sloppy).join(), "length,name,prototype,arguments,caller,foo");
    shouldBe(sloppy.arguments, null);
    shouldBe(sloppy.caller, null);
    // The order of the keys is not affected by reification.
    shouldBe(Reflect.ownKeys(sloppy).join(), "length,name,prototype,arguments,caller,foo");

    let descriptor = Object.getOwnPropertyDescriptor(sloppy, "caller");
    shouldBe(descriptor.value, null);
    shouldBe(descriptor.writable, false);
    shouldBe(descriptor.enumerable, false);
    shouldBe(descriptor.configurable, true);

    sloppy.caller = 42;
    shouldBe(sloppy.caller, null);
    shouldThrowTypeError(() => { "use strict"; sloppy.caller = 42; });

    shouldBe(delete sloppy.caller, true);
    shouldBe(Reflect.ownKeys(sloppy).join(), "length,name,prototype,arguments,foo");
    shouldBe(sloppy.hasOwnProperty("caller"), false);
    shouldThrowTypeError(() => sloppy.caller);
    shouldBe(sloppy.arguments, null);
}

{
    function deletedBeforeReification() { }
    shouldBe(delete deletedBeforeReification.arguments, true);
    shouldBe(Reflect.ownKeys(deletedBeforeReification).join(), "length,name,prototype,caller");
}

for (let func of [function () { "use strict"; }, () => { }, { method() { } }.method, class { }, function* () { }, async function () { }, async () => { }, Math.max, function () { }.bind()]) {
    shouldBe(func.hasOwnProperty("arguments"), false);
    shouldBe(func.hasOwnProperty("caller"), false);
    shouldThrowTypeError(() => func.arguments);
    shouldThrowTypeError(() => func.caller);
}

function callee() { return [callee.caller, callee.arguments]; }
function caller() { return callee(1, 2); }
noInline(callee);
for (let i = 0; i < testLoopCount; ++i) {
    let [observedCaller, observedArguments] = caller();
    shouldBe(observedCaller, caller);
    shouldBe(observedArguments.length, 2);
    shouldBe(observedArguments[1], 2);
}
shouldBe(callee.caller, null);
shouldBe(callee.arguments, null);
