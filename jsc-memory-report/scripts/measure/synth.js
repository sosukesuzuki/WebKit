// Synthetic workload: many small functions with property access + calls, forcing baseline/DFG/FTL tiers.
// N functions, each with K get_by_id sites and a call; run to tier up.
var N = (typeof NFUNCS !== "undefined") ? NFUNCS : 2000;
var src = "";
for (var i = 0; i < N; i++) {
  src += "function f" + i + "(o, p) { var s = 0; s += o.a + o.b + o.c + o.d; s += p.x * p.y; if (o.a > " + i + ") s += g" + i + "(o); return s; }\n";
  src += "function g" + i + "(o) { return o.e + o.f; }\n";
}
src += "var fns = [" + Array.from({length: N}, (_, i) => "f" + i).join(",") + "];\n";
eval(src);
var objs = [{a:1,b:2,c:3,d:4,e:5,f:6},{a:1,b:2,c:3,d:4,e:5,f:6,g:7},{b:2,a:1,c:3,d:4,e:5,f:6}];
var pt = {x:1.5,y:2.5};
var ITER = (typeof ITERS !== "undefined") ? ITERS : 3000;
var sum = 0;
for (var it = 0; it < ITER; it++) {
  for (var i = 0; i < N; i++) sum += fns[i](objs[(i + it) % 3], pt);
}
print("sum=" + sum);
