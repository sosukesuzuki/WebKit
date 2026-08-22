// Stress: same source evaluated in many realms + many evals (CodeCache shares UnlinkedCodeBlocks),
// polymorphic calls with varied `this`, iterators, for-in, and frequent GC + code block churn.
var body = `
  function Obj(k){ this.k = k; }
  Obj.prototype.m = function(a){ return this.k + a; };
  function callIt(o, a){ return o.m(a); }
  function* gen(n){ for (var i=0;i<n;i++) yield i; }
  function iter(n){ var s=0; for (var v of gen(n)) s+=v; for (var v of [1,2,3]) s+=v; return s; }
  function forin(o){ var s=0; for (var k in o) s += o[k]|0; return s; }
  function apply(f, t, args){ return f.apply(t, args); }
  var objs = [new Obj(1), {k:2, m(a){return a*2}}, new (class extends Obj{})(3), Object.create(new Obj(4)), new Proxy(new Obj(5), {})];
  for (var j=0;j<3;j++) objs.push({['p'+j]: j, k: j, m: Obj.prototype.m});
  var total = 0;
  for (var i=0;i<4000;i++) {
    var o = objs[i % objs.length];
    total += callIt(o, i);
    total += apply(o.m, o, [i]);
    total += iter(5);
    total += forin(o);
    total += "abc".charCodeAt(i%3);
    total += [i,i+1].map(x=>x*2)[1];
  }
  total;
`;
var results = [];
var realms = [];
for (var r = 0; r < 30; r++) {
  var g = typeof $vm !== "undefined" ? $vm.createGlobalObject() : globalThis;
  realms.push(g);
  var f = new g.Function(body);
  results.push(f());
  // evaluate identical eval text in several globals -> CodeCache reuse
  results.push(g.eval(body));
  if (r % 5 == 0) { fullGC(); realms.length = 0; }
  if (r % 7 == 0) edenGC();
}
print("ok", results.length, results[0]);
