// Short arrays of a few numbers that come up again and again, like colors.
function test(a, b, c) {
    return [a, b, c, 0.75].join(",");
}
noInline(test);

var total = 0;
for (var i = 0; i < 4e5; ++i)
    total += test((i & 7) + 0.25, (i & 3) + 0.5, (i & 1) + 0.125).length;
if (total !== 7600000)
    throw new Error("bad result: " + total);
