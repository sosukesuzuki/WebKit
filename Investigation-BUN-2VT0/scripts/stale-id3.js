var shared = function m() { return 1; };
var arr = [1];
function drive(o) { arr.forEach(shared, o); }
noInline(drive);
function scrub(n) { var a = 1, b = 2, c = 3, d = 4, e = 5, f = 6, g = 7, h = 8; if (n > 0) return scrub(n - 1) + a + b + c + d + e + f + g + h; return 0; }
noInline(scrub);
var base = {};
for (var i = 0; i < 3000; i++) drive(base);
fullGC(); fullGC();
function mk(i) { var o = {}; o["unique_" + i] = i; return o; }
for (var round = 0; round < 30; round++) {
    for (var i = 0; i < 300; i++) drive(mk(round * 1000 + i));
    scrub(200);
    edenGC();
    var keep = [];
    for (var i = 0; i < 5000; i++) { var o = {}; o["k" + i] = i; keep.push(o); }
    scrub(200);
    edenGC();
    fullGC();
    keep = null;
}
print("done");
