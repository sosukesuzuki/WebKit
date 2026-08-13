load("realm-lib.js", "caller relative");
// ArrayBuffer.prototype.slice / SharedArrayBuffer.prototype.slice on a foreign receiver.
// Spec (25.1.6.7 step 15-16): ctor = SpeciesConstructor(O, %ArrayBuffer%) => O.constructor
// = B.ArrayBuffer => @@species => B.ArrayBuffer; new = Construct(ctor, <<newLen>>) => realm B.
// (Unlike ArraySpeciesCreate there is NO "cross-realm %Array% => undefined" escape hatch.)
// JSC (JSArrayBufferPrototype.cpp speciesConstructArrayBuffer / arrayBufferSpeciesConstructorSlow):
// treats "constructor is *its own realm's* ArrayBuffer" as the fast path and then allocates
// with globalObject->arrayBufferStructure() of the calling realm A.
const bBuf = new B.ArrayBuffer(8);
check("realm of ArrayBuffer.prototype.slice.call(bBuf)", realmOf(ArrayBuffer.prototype.slice.call(bBuf, 0, 4)), "B");
const bRBuf = new B.ArrayBuffer(8, { maxByteLength: 16 });
check("realm of slice.call(resizable bBuf)", realmOf(ArrayBuffer.prototype.slice.call(bRBuf, 0, 4)), "B");
if (typeof SharedArrayBuffer !== "undefined") {
    const bS = new B.SharedArrayBuffer(8);
    check("realm of SharedArrayBuffer.prototype.slice.call(bS)", realmOf(SharedArrayBuffer.prototype.slice.call(bS, 0, 4)), "B");
}
// Contrast: typed arrays get it right in JSC.
check("realm of Uint8Array.prototype.slice.call(bTA) (control)", realmOf(Uint8Array.prototype.slice.call(new B.Uint8Array(4))), "B");
