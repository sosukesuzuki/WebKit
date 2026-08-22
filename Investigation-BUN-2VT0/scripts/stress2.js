// CC-shaped stress: async/await, generators, iterators, for-in, native callbacks, proxies, call/apply/bind,
// class hierarchies, closures, eval churn, frequent GC, deleteAllCode.
function mkClasses(n) {
  class Base { constructor(i){ this.i = i; this.tag = "b"+(i%7); } m(a){ return this.i + a; } get g(){ return this.i; } *it(){ yield this.i; yield this.i+1; } async am(x){ await null; return this.m(x); } }
  const out = [Base];
  for (let k = 1; k < n; k++) { const P = out[k-1]; out.push(class extends P { constructor(i){ super(i); this["p"+k] = k; } m(a){ return super.m(a) + k; } }); }
  return out;
}
const classes = mkClasses(9);
const objs = [];
for (let i = 0; i < 200; i++) objs.push(new classes[i % classes.length](i));
objs.push(new Proxy({i:1, m(a){return a;}, tag:"p"}, {}));
objs.push(Object.create(objs[3]));
objs.push({ i: 5, m: objs[0].m, tag: "x", [Symbol.iterator]: function*(){ yield 1; } });

function callAll(o, a) { return o.m(a) + o.m.call(o, a) + o.m.apply(o, [a]) + o.m.bind(o)(a); }
function iterAll(o) { let s = 0; for (const k in o) s += (o[k] | 0); for (const v of (o.it ? o.it() : [1,2])) s += v; for (const [k,v] of Object.entries(o)) s += k.length; return s; }
function natives(o, i) { return [o, i, "s"].map((x, j) => typeof x === "object" ? j : 1).reduce((a,b)=>a+b, 0) + JSON.stringify({i}).length + [3,1,2].sort((a,b)=>a-b)[0] + Array.from({length: 3}, (_, j) => j).filter(Boolean).length; }
async function asyncWork(o, i) {
  const r = await o.am?.(i) ?? i;
  const p = await Promise.all([Promise.resolve(r), new Promise(res => res(i)), (async () => { await null; return o.i; })()]);
  try { await Promise.reject(new Error("x")); } catch (e) { }
  return p[0] + p[1] + p[2];
}
async function* agen(n) { for (let i = 0; i < n; i++) { await null; yield i; } }
async function asyncIter() { let s = 0; for await (const v of agen(5)) s += v; return s; }

let total = 0;
async function round(r) {
  for (let i = 0; i < 3000; i++) {
    const o = objs[(i * 7 + r) % objs.length];
    total += callAll(o, i);
    total += iterAll(o);
    total += natives(o, i);
    if (i % 50 == 0) total += await asyncWork(o, i);
    if (i % 300 == 0) total += await asyncIter();
  }
  // code churn
  const f = new Function("o", "i", "return o.m(i) + (function(){ return this.i }).call(o) + [i].map(x=>x)[0];");
  for (let i = 0; i < 500; i++) total += f(objs[i % objs.length], i);
  total += (0, eval)("(function(o){ var s=0; for (var k in o) s+=1; return s; })")(objs[r % objs.length]);
}
(async () => {
  for (let r = 0; r < 24; r++) {
    await round(r);
    if (r % 3 == 0) fullGC(); else edenGC();
    if (r % 8 == 7 && typeof $vm !== "undefined") { $vm.deleteAllCodeWhenIdle(); fullGC(); }
    drainMicrotasks();
  }
  print("ok", total);
})().catch(e => { print("ERR", e, e.stack); });
drainMicrotasks();
