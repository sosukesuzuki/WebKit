function shouldBe(actual, expected) {
    if (actual !== expected)
        throw new Error(`expected ${expected} but got ${actual}`);
}

let other = createGlobalObject();

// Capturing stack traces dominates the execution time of this test.
Error.stackTraceLimit = 0;
other.Error.stackTraceLimit = 0;

let ReturnsNull = other.eval("(class ReturnsNull extends Object { constructor() { return null; } })");
let NoSuper = other.eval("(class NoSuper extends Object { constructor() { } })");
let AccessesThis = other.eval("(class AccessesThis extends Object { constructor() { this; } })");
let callFromOther = other.eval("(function (constructor) { new constructor; })");
class LocalNoSuper extends Object { constructor() { } }
let otherProxyOfLocalNoSuper = other.eval("(function (target) { return new Proxy(target, {}); })")(LocalNoSuper);
let otherBoundLocalNoSuper = other.Function.prototype.bind.call(LocalNoSuper);

function construct(constructor) {
    try {
        new constructor;
    } catch (error) {
        return error;
    }
    throw new Error("should throw");
}
noInline(construct);

function constructViaOther(constructor) {
    try {
        callFromOther(constructor);
    } catch (error) {
        return error;
    }
    throw new Error("should throw");
}
noInline(constructViaOther);

function constructViaReflect(constructor) {
    try {
        Reflect.construct(constructor, []);
    } catch (error) {
        return error;
    }
    throw new Error("should throw");
}
noInline(constructViaReflect);

function constructViaOtherReflect(constructor) {
    try {
        other.Reflect.construct(constructor, []);
    } catch (error) {
        return error;
    }
    throw new Error("should throw");
}
noInline(constructViaOtherReflect);

// Throwing is slow.
for (let i = 0; i < testLoopCount / 4; ++i) {
    shouldBe(construct(ReturnsNull).constructor, TypeError);
    shouldBe(construct(NoSuper).constructor, ReferenceError);
    // Evaluating `this` happens inside the callee's execution context.
    shouldBe(construct(AccessesThis).constructor, other.ReferenceError);
    shouldBe(construct(LocalNoSuper).constructor, ReferenceError);
    shouldBe(constructViaOther(LocalNoSuper).constructor, other.ReferenceError);
    shouldBe(constructViaOther(NoSuper).constructor, other.ReferenceError);
    shouldBe(constructViaReflect(ReturnsNull).constructor, TypeError);
    // The running execution context is the one of other realm's Reflect.construct.
    shouldBe(constructViaOtherReflect(ReturnsNull).constructor, other.TypeError);
    shouldBe(constructViaOtherReflect(LocalNoSuper).constructor, other.ReferenceError);
    // Proxies and bound functions do not have their own execution contexts.
    shouldBe(construct(otherProxyOfLocalNoSuper).constructor, ReferenceError);
    shouldBe(construct(otherBoundLocalNoSuper).constructor, ReferenceError);
}
