// Bun port of 18-realm-leak-cached-structures.js. Bun tends to keep the most recently used vm context
// alive regardless, so instead of one throw-away realm we use K of them and count survivors.
import vm from "node:vm"; import { heapStats } from "bun:jsc";
const K = 40;
const alive = () => { Bun.gc(true); Bun.gc(true); return heapStats().objectTypeCounts.NodeVMGlobalObject | 0; };
const tick = () => new Promise(r => setTimeout(r, 10));
function report(label, survivors, expectedMax) {
    console.log((survivors <= expectedMax ? "PASS " : "FAIL ") + label + ": " + survivors + " of " + K + " dropped vm contexts still alive");
}
// control: contexts that run a regexp WITHOUT named groups, patterns also used by the main realm
const plain = Array.from({ length: K }, (_, i) => new RegExp("(\\d{4})-(\\d{2})#" + i));
plain.forEach((re, i) => re.exec("2024-05#" + i));
for (let i = 0; i < K; i++) vm.runInContext(`/(\\d{4})-(\\d{2})#${i}/.exec("2024-05#${i}")`, vm.createContext({}));
await tick(); const base = alive();
report("control (no named groups)", base, 2);
// (a) same, WITH named groups: RegExp::ensureGroupsStructure caches a context-realm Structure on the shared RegExp cell
const named = Array.from({ length: K }, (_, i) => new RegExp("(?<y>\\d{4})-(?<m>\\d{2})#" + i));
named.forEach((re, i) => re.exec("2024-05#" + i));
for (let i = 0; i < K; i++) vm.runInContext(`/(?<y>\\d{4})-(?<m>\\d{2})#${i}/.exec("2024-05#${i}")`, vm.createContext({}));
await tick(); report("(a) contexts that ran a named-group regexp the main realm also uses", alive() - base, 2);
named.forEach((re, i) => re.exec("2024-05#" + i));      // main realm re-matches: caches point back at the main realm
await tick(); report("(a) ...after the main realm matches those patterns again", alive() - base, 2);
// (b) bind() borrowed from a context, applied to main-realm functions
const targets = Array.from({ length: K }, () => function target() {});
for (let i = 0; i < K; i++) vm.runInContext("Function.prototype.bind", vm.createContext({})).call(targets[i], null);
await tick(); report("(b) contexts whose Function.prototype.bind was applied to a main-realm function", alive() - base, 2);
