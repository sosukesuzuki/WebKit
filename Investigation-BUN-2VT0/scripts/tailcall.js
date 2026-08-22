"use strict";
// Callee stays in LLInt (never hot enough to JIT) and profiles its args at entry; caller is DFG/FTL and tail-calls it.
function makeCallee() { return function callee(a, b, c) { return a === 13 ? b : c; }; }
var callees = [];
for (var k = 0; k < 64; k++) callees.push(makeCallee());  // many distinct LLInt callees (each sees few calls)
function caller(i, x) {
    var a = (i & 3) === 0 ? 13 : (i | 0);   // int32
    var b = (x * 2) | 0;                    // int32 derived
    var c = i + 0.5;                        // double
    var f = callees[i & 63];
    return f(a, b, c);                      // tail call in strict mode
}
noInline(caller);
var s = 0;
for (var i = 0; i < 2000000; i++) s += caller(i, i % 7);
fullGC();
for (var i = 0; i < 200000; i++) s += caller(i, i % 7);
fullGC();
print("ok", s);
