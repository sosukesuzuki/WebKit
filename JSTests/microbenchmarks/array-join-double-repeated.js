// Few enough distinct numbers that their strings could all stay in a cache.
var array = [];
for (var i = 0; i < 1000; ++i)
    array.push((i % 100) / 7);

function test(array) {
    return array.join();
}
noInline(test);

var expected = test(array).length;
var total = 0;
for (var i = 0; i < 1000; ++i)
    total += test(array).length;
if (total !== expected * 1000)
    throw new Error("bad result: " + total);
