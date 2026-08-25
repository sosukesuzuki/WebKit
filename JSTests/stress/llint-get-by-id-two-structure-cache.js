//@ runDefault
//@ runNoJIT

function shouldBe(actual, expected, message) {
    if (actual !== expected)
        throw new Error((message || "") + " bad value: " + actual + " expected " + expected);
}

// Two own-property shapes alternating at one site.
{
    function get(o) { return o.x; }
    const a = { x: 1 };
    const b = { y: 0, x: 2 };
    for (let i = 0; i < 100; i++) {
        shouldBe(get(a), 1);
        shouldBe(get(b), 2);
    }
    // Transition both structures and keep reading.
    a.z = 3;
    b.z = 4;
    for (let i = 0; i < 100; i++) {
        shouldBe(get(a), 1);
        shouldBe(get(b), 2);
    }
    // Delete the property on one of them (dictionary / different structure).
    delete a.x;
    for (let i = 0; i < 100; i++) {
        shouldBe(get(a), undefined);
        shouldBe(get(b), 2);
    }
    a.x = 5;
    for (let i = 0; i < 100; i++) {
        shouldBe(get(a), 5);
        shouldBe(get(b), 2);
    }
}

// Three shapes cycling; the cache only holds two, every value must still be right.
{
    function get(o) { return o.x; }
    const objs = [{ x: 1 }, { a: 0, x: 2 }, { a: 0, b: 0, x: 3 }, { a: 0, b: 0, c: 0, x: 4 }];
    for (let i = 0; i < 400; i++)
        shouldBe(get(objs[i % objs.length]), (i % objs.length) + 1);
}

// A structure whose offset does not fit in the second entry.
{
    function get(o) { return o.x; }
    const big = {};
    for (let i = 0; i < 40000; i++)
        big["p" + i] = i;
    big.x = "big";
    const small = { x: "small" };
    for (let i = 0; i < 100; i++) {
        shouldBe(get(big), "big");
        shouldBe(get(small), "small");
    }
    // Reverse the order so the big structure is the one being demoted.
    for (let i = 0; i < 100; i++) {
        shouldBe(get(small), "small");
        shouldBe(get(big), "big");
    }
}

// Own hit first, then prototype hits: the prototype cache must still be created and stay correct.
{
    function get(o) { return o.m; }
    class C { }
    C.prototype.m = "proto";
    const own = { m: "own" };
    const c = new C();
    shouldBe(get(own), "own");
    for (let i = 0; i < 100; i++)
        shouldBe(get(c), "proto");
    // Invalidate the prototype cache by replacing the holder's value...
    C.prototype.m = "proto2";
    for (let i = 0; i < 100; i++)
        shouldBe(get(c), "proto2");
    // ...and by shadowing it on the instance.
    c.m = "shadow";
    for (let i = 0; i < 100; i++)
        shouldBe(get(c), "shadow");
    delete c.m;
    for (let i = 0; i < 100; i++)
        shouldBe(get(c), "proto2");
}

// Own/prototype alternation with prototype chain mutation in between (exercises re-arming).
{
    function get(o) { return o.m; }
    class Base { }
    Base.prototype.m = "base";
    class Derived extends Base { }
    const own = { m: "own" };
    const d = new Derived();
    for (let round = 0; round < 5; round++) {
        for (let i = 0; i < 50; i++) {
            shouldBe(get(d), "base", "round " + round);
            shouldBe(get(own), "own");
        }
        // Make the property appear on the intermediate prototype, which fires the absence watchpoint.
        Derived.prototype.m = "derived";
        for (let i = 0; i < 50; i++) {
            shouldBe(get(d), "derived", "round " + round);
            shouldBe(get(own), "own");
        }
        delete Derived.prototype.m;
        for (let i = 0; i < 50; i++)
            shouldBe(get(d), "base", "round " + round);
    }
}

// GC while cached structures die.
{
    function get(o) { return o.x; }
    for (let round = 0; round < 20; round++) {
        let a = {};
        a["k" + round] = 0;
        a.x = round;
        let b = {};
        b["j" + round] = 0;
        b["k" + round] = 0;
        b.x = -round;
        for (let i = 0; i < 20; i++) {
            shouldBe(get(a), round);
            shouldBe(get(b), -round);
        }
        a = null;
        b = null;
        fullGC();
        const c = { x: "c" + round };
        shouldBe(get(c), "c" + round);
    }
}

// Array length and own "length" mixed.
{
    function len(o) { return o.length; }
    const arr = [1, 2, 3];
    const obj = { length: 7 };
    const str = "abcd";
    for (let i = 0; i < 100; i++) {
        shouldBe(len(arr), 3);
        shouldBe(len(obj), 7);
        shouldBe(len(str), 4);
    }
    arr.push(4);
    for (let i = 0; i < 100; i++)
        shouldBe(len(arr), 4);
}
