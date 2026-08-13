load("realm-lib.js", "caller relative");
// WebAssembly.Memory.prototype.buffer materialises the JSArrayBuffer wrapper lazily,
// using the realm of whichever `buffer` getter touches the Memory first, and caches it.
// Wasm JS API: the buffer object is created together with the Memory ("create a fixed
// length memory buffer" is called from the Memory constructor / instantiate), i.e. realm B.
if (typeof WebAssembly === "undefined") { print("SKIP no WebAssembly"); quit(); }
const getterA = Object.getOwnPropertyDescriptor(WebAssembly.Memory.prototype, "buffer").get;
const readInB = B.eval("(m) => m.buffer");
const m1 = new B.WebAssembly.Memory({ initial: 1 });
check("A's getter first: realm of buffer", realmOf(getterA.call(m1)), "B");
check("...B now also sees", realmOf(readInB(m1)), "B");
const m2 = new B.WebAssembly.Memory({ initial: 1 });
readInB(m2);
check("B first (control): realm of buffer via A getter", realmOf(getterA.call(m2)), "B");
const m3 = new B.WebAssembly.Memory({ initial: 1, maximum: 2, shared: true });
check("shared memory, A first: realm", realmOf(getterA.call(m3)), "B");
if (WebAssembly.Memory.prototype.toResizableBuffer) {
    const m4 = new B.WebAssembly.Memory({ initial: 1, maximum: 2 });
    check("A toResizableBuffer.call(bMem): realm", realmOf(WebAssembly.Memory.prototype.toResizableBuffer.call(m4)), "B");
    check("...and B's own m.buffer afterwards", realmOf(readInB(m4)), "B");
}
