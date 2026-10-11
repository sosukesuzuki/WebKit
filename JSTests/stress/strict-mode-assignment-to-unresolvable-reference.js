// Capturing stack traces dominates the execution time of this test.
Error.stackTraceLimit = 0;

function shouldBe(actual, expected) {
    if (actual !== expected)
        throw new Error(`expected ${expected} but got ${actual}`);
}

function shouldThrowReferenceError(func) {
    let error;
    try {
        func();
    } catch (e) {
        error = e;
    }
    if (!(error instanceof ReferenceError))
        throw new Error(`expected a ReferenceError but got ${error}`);
}

function strictAssign(name) {
    "use strict";
    unresolvableAtResolveTime = (globalThis.unresolvableAtResolveTime = name);
}
noInline(strictAssign);

function sloppyAssign(value) {
    sloppyUnresolvable = (globalThis.sloppyUnresolvable = value) + 1;
}
noInline(sloppyAssign);

function strictTypeof() {
    "use strict";
    return typeof neverDeclaredVariable;
}
noInline(strictTypeof);

function strictAssignToExisting(value) {
    "use strict";
    existingGlobal = value;
}
noInline(strictAssignToExisting);

var existingGlobal = 0;

// Throwing is slow.
for (let i = 0; i < testLoopCount / 4; ++i) {
    shouldThrowReferenceError(() => strictAssign(i));
    // The right hand side is evaluated before PutValue throws.
    shouldBe(globalThis.unresolvableAtResolveTime, i);
    delete globalThis.unresolvableAtResolveTime;

    sloppyAssign(i);
    shouldBe(globalThis.sloppyUnresolvable, i + 1);
    delete globalThis.sloppyUnresolvable;

    shouldBe(strictTypeof(), "undefined");

    strictAssignToExisting(i);
    shouldBe(existingGlobal, i);
}

// Once the binding exists when the reference is resolved, the assignment succeeds.
globalThis.unresolvableAtResolveTime = -1;
strictAssign(42);
shouldBe(globalThis.unresolvableAtResolveTime, 42);
