// Short arrays of distinct numbers, like the coordinates of a path.
var points = [];
for (var i = 0; i < 1 << 14; ++i)
    points.push([i / 7, i / 13]);

function test(array) {
    return array.join(" ");
}
noInline(test);

var total = 0;
for (var i = 0; i < 20; ++i) {
    for (var j = 0; j < points.length; ++j)
        total += test(points[j]).length;
}
if (total !== 10759140)
    throw new Error("bad result: " + total);
