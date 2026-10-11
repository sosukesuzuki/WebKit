// Capturing stack traces dominates the execution time of this test.
Error.stackTraceLimit = 0;

function shouldBe(actual, expected) {
    if (actual !== expected)
        throw new Error(`expected ${expected} but got ${actual}`);
}

function makeEnvironment(log) {
    return new Proxy({}, {
        has(target, key) {
            if (typeof key === "string" && key.startsWith("target"))
                log.push("resolve:" + key);
            return false;
        }
    });
}

var targetA, targetB, targetC, targetRest;

function objectPattern(environment, log) {
    with (environment) {
        var { a: targetA, [(log.push("key:b"), "b")]: targetB = (log.push("default:b"), 1), ...targetRest } = {
            get a() { log.push("get:a"); return 0; },
            get b() { log.push("get:b"); },
            get c() { log.push("get:c"); return 2; },
        };
    }
}
noInline(objectPattern);

function arrayPattern(environment, log) {
    let iterable = {
        [Symbol.iterator]() {
            log.push("iterator");
            let index = 0;
            return {
                next() {
                    log.push("next:" + index);
                    return { done: index >= 3, value: index++ };
                }
            };
        }
    };
    with (environment) {
        var [targetA, targetB, ...targetRest] = iterable;
    }
}
noInline(arrayPattern);

function strictArrayAssignment() {
    "use strict";
    [unresolvableArrayElement] = { [Symbol.iterator]() { return { next() { globalThis.unresolvableArrayElement = 1; return { done: false, value: 2 }; } }; } };
}
noInline(strictArrayAssignment);

function strictObjectRestAssignment() {
    "use strict";
    ({ ...unresolvableObjectRest } = { get a() { globalThis.unresolvableObjectRest = 1; return 2; } });
}
noInline(strictObjectRestAssignment);

function shouldThrowReferenceError(func) {
    let error;
    try {
        func();
    } catch (e) {
        error = e;
    }
    shouldBe(error instanceof ReferenceError, true);
}

for (let i = 0; i < testLoopCount / 4; ++i) {
    let log = [];
    objectPattern(makeEnvironment(log), log);
    shouldBe(log.join(), "resolve:targetA,get:a,key:b,resolve:targetB,get:b,default:b,resolve:targetRest,get:c");

    log = [];
    arrayPattern(makeEnvironment(log), log);
    shouldBe(log.join(), "iterator,resolve:targetA,next:0,resolve:targetB,next:1,resolve:targetRest,next:2,next:3");
}

// Throwing is slow.
for (let i = 0; i < testLoopCount / 8; ++i) {
    shouldThrowReferenceError(strictArrayAssignment);
    delete globalThis.unresolvableArrayElement;
    shouldThrowReferenceError(strictObjectRestAssignment);
    delete globalThis.unresolvableObjectRest;
}
