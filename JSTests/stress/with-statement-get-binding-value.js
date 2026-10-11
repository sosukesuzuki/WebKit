function shouldBe(actual, expected) {
    if (actual !== expected)
        throw new Error(`expected ${expected} but got ${actual}`);
}

function readInWith(object) {
    with (object) {
        return binding;
    }
}
noInline(readInWith);

function strictReadInWith(object) {
    with (object) {
        return (function () {
            "use strict";
            return binding;
        })();
    }
}
noInline(strictReadInWith);

for (let i = 0; i < testLoopCount; ++i) {
    let log = [];
    let proxy = new Proxy({ binding: i }, {
        has(target, key) { log.push("has:" + String(key)); return Reflect.has(target, key); },
        get(target, key, receiver) { log.push("get:" + String(key)); return Reflect.get(target, key, receiver); },
    });
    shouldBe(readInWith(proxy), i);
    shouldBe(log.join(), "has:binding,get:Symbol(Symbol.unscopables),has:binding,get:binding");

    shouldBe(readInWith({ binding: i }), i);

    let deleting = {
        binding: i,
        get [Symbol.unscopables]() {
            delete this.binding;
            return undefined;
        }
    };
    shouldBe(readInWith(deleting), undefined);

    deleting.binding = i;
    let error;
    try {
        strictReadInWith(deleting);
    } catch (e) {
        error = e;
    }
    shouldBe(error instanceof ReferenceError, true);
}
