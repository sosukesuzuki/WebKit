//@ runDefault
//@ runNoJIT

function shouldBe(actual, expected, message) {
    if (actual !== expected)
        throw new Error((message || "") + " bad value: " + actual + " expected " + expected);
}

// Prototype cache on two receiver shapes sharing a holder, then the holder changes.
{
    function get(o) { return o.m; }
    class C { }
    C.prototype.m = 1;
    const a = new C();
    const b = new C();
    b.extra = 1;
    for (let i = 0; i < 100; i++) {
        shouldBe(get(a), 1);
        shouldBe(get(b), 1);
    }
    C.prototype.m = 2;
    for (let i = 0; i < 100; i++) {
        shouldBe(get(a), 2);
        shouldBe(get(b), 2);
    }
    Object.setPrototypeOf(a, { m: 3 });
    for (let i = 0; i < 100; i++) {
        shouldBe(get(a), 3);
        shouldBe(get(b), 2);
    }
}


// Deep prototype chains walked from the receiver's structure.
{
    function get(o) { return o.m; }
    class A { }
    A.prototype.m = "A";
    class B extends A { }
    class C extends B { }
    class D extends C { }
    const c = new C();
    const d = new D();
    const d2 = new D();
    d2.extra = 1;
    for (let i = 0; i < 100; i++) {
        shouldBe(get(c), "A");
        shouldBe(get(d), "A");
        shouldBe(get(d2), "A");
    }
    // Unrelated transition on an intermediate prototype keeps the cache valid.
    C.prototype.unrelated = 1;
    for (let i = 0; i < 100; i++) {
        shouldBe(get(d), "A");
        shouldBe(get(d2), "A");
    }
    // Shadowing on an intermediate invalidates it.
    B.prototype.m = "B";
    for (let i = 0; i < 100; i++) {
        shouldBe(get(c), "B");
        shouldBe(get(d), "B");
        shouldBe(get(d2), "B");
    }
    // Re-routing an intermediate's prototype invalidates it too.
    Object.setPrototypeOf(C.prototype, { m: "X" });
    for (let i = 0; i < 100; i++) {
        shouldBe(get(c), "X");
        shouldBe(get(d), "X");
        shouldBe(get(d2), "X");
    }
    // Deleting the holder's property makes the lookup fall through to the next holder.
    delete B.prototype.m;
    Object.setPrototypeOf(C.prototype, B.prototype);
    for (let i = 0; i < 100; i++) {
        shouldBe(get(c), "A");
        shouldBe(get(d), "A");
    }
}

// Two receivers with different holders at the same depth, plus a third unrelated one.
{
    function get(o) { return o.m; }
    class A { m() { return "A"; } }
    class B { m() { return "B"; } }
    class C { x = 1; m() { return "C"; } }
    const a = new A(), b = new B(), c = new C();
    for (let i = 0; i < 300; i++) {
        shouldBe(get(a)(), "A");
        shouldBe(get(b)(), "B");
        shouldBe(get(c)(), "C");
    }
}

// Primitive receivers keep working alongside objects.
{
    function get(o) { return o.toString; }
    const obj = new (class { toString() { return "obj"; } })();
    for (let i = 0; i < 100; i++) {
        shouldBe(get("str"), String.prototype.toString);
        shouldBe(get(obj)(), "obj");
        shouldBe(get(123), Number.prototype.toString);
    }
    String.prototype.toString2 = function () { return "patched"; };
    function get2(o) { return o.toString2; }
    for (let i = 0; i < 100; i++)
        shouldBe(get2("str")(), "patched");
}

// GC with prototype caches whose receivers die.
{
    function get(o) { return o.m; }
    for (let round = 0; round < 10; round++) {
        class K { }
        K.prototype.m = round;
        let a = new K();
        let b = new K();
        b["p" + round] = 1;
        for (let i = 0; i < 20; i++) {
            shouldBe(get(a), round);
            shouldBe(get(b), round);
        }
        a = b = null;
        fullGC();
        shouldBe(get({ __proto__: { m: "after" } }), "after");
    }
}
