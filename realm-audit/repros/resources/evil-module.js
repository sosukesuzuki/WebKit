export const x = 42;
globalThis.report = "PASS evilThen never received a foreign function";
let reads = 0;
function evilThen(resolve) {
    // `resolve` should be a function of *this* realm. If it is an incubating-realm function,
    // its .constructor is the incubating %Function% and the sandbox is gone.
    const g = resolve.constructor("return globalThis")();
    globalThis.report = (g === globalThis ? "PASS" : "FAIL evilThen got an incubating-realm resolve(); outer secret = " + g.secret);
    resolve("done");
}
const V = { get then() { return ++reads >= 2 ? evilThen : undefined; } };
export function then(resolve) { resolve(V); }     // makes the module namespace object itself a thenable
