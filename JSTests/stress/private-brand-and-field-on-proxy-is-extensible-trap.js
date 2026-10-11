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

class Base {
    constructor(object) {
        return object;
    }
}

// The isExtensible trap can run arbitrary code while installing a private brand.
class StoresAroundBrand extends Base {
    #method() { }
    constructor(object, array, holder) {
        array[0] = 1.5;
        let before = holder.x;
        super(object);
        array[0] = 2.5;
        this.result = before + holder.x;
    }
}

class StoresAroundField extends Base {
    #field = 0;
    constructor(object, array, holder) {
        array[0] = 1.5;
        let before = holder.x;
        super(object);
        array[0] = 2.5;
        this.result = before + holder.x;
    }
}

for (let constructor of [StoresAroundBrand, StoresAroundField]) {
    for (let i = 0; i < testLoopCount; ++i) {
        let array = [0.5];
        let holder = { x: 1 };
        let isLast = i === testLoopCount - 1;
        let proxy = new Proxy({}, {
            isExtensible(target) {
                if (isLast) {
                    for (let j = 0; j < 1000; ++j)
                        array.push(7.5);
                    holder.x = 100;
                }
                return Reflect.isExtensible(target);
            }
        });
        let result = new constructor(proxy, array, holder);
        shouldBe(array[0], 2.5);
        shouldBe(result.result, isLast ? 101 : 2);
    }
}

// Extensibility of a Proxy must be checked every time.
class InstallsBrand extends Base {
    #method() { }
    static has(object) { return #method in object; }
}

class InstallsAnotherBrand extends Base {
    #another() { }
    static has(object) { return #another in object; }
}

for (let i = 0; i < testLoopCount; ++i) {
    let count = 0;
    let handler = { isExtensible(target) { count++; return Reflect.isExtensible(target); } };
    new InstallsBrand(new Proxy({}, handler));
    shouldBe(count, 1);
    let nonExtensible = new Proxy(Object.preventExtensions({}), handler);
    shouldThrowTypeError(() => new InstallsBrand(nonExtensible));
    shouldBe(count, 2);
    shouldBe(InstallsBrand.has(nonExtensible), false);
}

// The trap installs another brand on the same object.
for (let i = 0; i < testLoopCount; ++i) {
    let reentered = false;
    let proxy = new Proxy({}, {
        isExtensible(target) {
            if (!reentered) {
                reentered = true;
                new InstallsAnotherBrand(proxy);
            }
            return true;
        }
    });
    new InstallsBrand(proxy);
    shouldBe(InstallsBrand.has(proxy), true);
    shouldBe(InstallsAnotherBrand.has(proxy), true);

    let plain = new Proxy({}, {});
    new InstallsBrand(plain);
    shouldBe(InstallsBrand.has(plain), true);
    shouldBe(InstallsAnotherBrand.has(plain), false);
}
