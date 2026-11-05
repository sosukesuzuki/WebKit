var bytes = new Uint8Array(64);
for (var i = 0; i < bytes.length; ++i)
    bytes[i] = (i * 37 + 11) & 0xff;

function test(array) {
    return array.join(",");
}
noInline(test);

var expected = Array.from(bytes).join(",");
for (var i = 0; i < 2e4; ++i) {
    if (test(bytes).length !== expected.length)
        throw new Error("bad result");
}
if (test(bytes) !== expected)
    throw new Error("bad result");
