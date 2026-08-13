// Runs a jsc-shell realm reproducer under Bun or Node by mapping the shell primitives onto node:vm.
//   bun harness.js ../repros/01-string-regexp-fastpath.js      (or: node harness.js ...)
// createGlobalObject()  ->  the global object of a fresh vm.createContext() realm (same JSC::VM / V8 isolate)
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

globalThis.print = (...a) => console.log(a.map(String).join(" "));
globalThis.createGlobalObject = () => vm.runInContext("globalThis", vm.createContext({}));
globalThis.quit = () => process.exit(0);
if (typeof globalThis.drainMicrotasks !== "function") globalThis.drainMicrotasks = () => {}; // exit-time flush is enough for the scripts we run

const file = path.resolve(process.argv[2]);
const dir = path.dirname(file);
function inline(f) {                       // expand load("x.js") the way the jsc shell does: as more global code
    return fs.readFileSync(f, "utf8").replace(/^load\("([^"]+)"(?:, "caller relative")?\);?$/mg, (_, dep) => inline(path.join(dir, dep)));
}
vm.runInThisContext(inline(file), { filename: file });
