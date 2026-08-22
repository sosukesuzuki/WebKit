// Try to get the DFG to (a) flush an argument as Int32 (store32 into the argument slot) and
// (b) take a BadType exit in checkArgumentTypes, reporting the raw slot as a JSValue.
function sink(x) { return x; }
noInline(sink);
function f(a, b) {
    // use `a` as int32 heavily, and flush it across a call (PutStack) so the DFG writes the slot as unboxed int32
    var s = 0;
    for (var i = 0; i < 10; i++) { s += a | 0; sink(s); }
    // later reads of `a` after the call come from the (unboxed) stack slot
    return s + (a | 0) + (b | 0);
}
noInline(f);
var cr = 13; // '\r'
for (var i = 0; i < 20000; i++) f(cr, i);
// now call with a non-int32 `a` -> BadType exit at entry, value profile refinement reports the argument slot
for (var i = 0; i < 100; i++) { f("x", i); f(cr, i); }
// force predictions to be recomputed and re-optimized a few times
for (var r = 0; r < 5; r++) {
  for (var i = 0; i < 20000; i++) f(cr, i);
  for (var i = 0; i < 100; i++) f({}, i);
  fullGC();
}
print("ok");
