function shouldBe(actual, expected) {
    if (actual !== expected)
        throw new Error('bad value: ' + actual + ', expected: ' + expected);
}

function concat(num) {
    return '' + num;
}
noInline(concat);

function template(num) {
    return `${num}`;
}
noInline(template);

function callString(num) {
    return String(num);
}
noInline(callString);

function toStringDefault(num) {
    return num.toString();
}
noInline(toStringDefault);

function toString10(num) {
    return num.toString(10);
}
noInline(toString10);

function toString16(num) {
    return num.toString(16);
}
noInline(toString16);

// The multiplication makes the operand a double regardless of the argument's profile.
function computed(num) {
    return '' + num * 0.5;
}
noInline(computed);

function computed2x(num) {
    return computed(num * 2);
}

// [value, radix 10, radix 16]
let cases = [
    [0, '0', '0'],
    [-0, '0', '0'],
    [1, '1', '1'],
    [9, '9', '9'],
    [10, '10', 'a'],
    [99, '99', '63'],
    [1022, '1022', '3fe'],
    [1023, '1023', '3ff'],
    [1024, '1024', '400'],
    [1025, '1025', '401'],
    [-1, '-1', '-1'],
    [-1023, '-1023', '-3ff'],
    [-1024, '-1024', '-400'],
    [0.5, '0.5', '0.8'],
    [-0.5, '-0.5', '-0.8'],
    [9.5, '9.5', '9.8'],
    [1023.5, '1023.5', '3ff.8'],
    [1024.5, '1024.5', '400.8'],
    [0x7fffffff, '2147483647', '7fffffff'],
    [0x80000000, '2147483648', '80000000'],
    [-0x80000000, '-2147483648', '-80000000'],
    [-0x80000001, '-2147483649', '-80000001'],
    [0x100000000, '4294967296', '100000000'],
    [0x100000005, '4294967301', '100000005'],
    [0x1000003ff, '4294968319', '1000003ff'],
    [-0xfffffffb, '-4294967291', '-fffffffb'],
    [Number.MAX_SAFE_INTEGER, '9007199254740991', '1fffffffffffff'],
    [2 ** 64, '18446744073709552000', '10000000000000000'],
    [NaN, 'NaN', 'NaN'],
    [Infinity, 'Infinity', 'Infinity'],
    [-Infinity, '-Infinity', '-Infinity'],
];

for (let value of [5e-324, -5e-324, 1e-7, 0.9999999999999999, 1.0000000000000002, 1022.9999999999999, 1023.0000000000001, 1.7976931348623157e308])
    cases.push([value, JSON.stringify(value), null]);

for (let i = 0; i < testLoopCount; ++i) {
    let [value, decimal, hex] = cases[i % cases.length];
    shouldBe(concat(value), decimal);
    shouldBe(template(value), decimal);
    shouldBe(callString(value), decimal);
    shouldBe(toStringDefault(value), decimal);
    shouldBe(toString10(value), decimal);
    if (hex)
        shouldBe(toString16(value), hex);
    // Number.MAX_VALUE * 2 overflows.
    if (value !== Number.MAX_VALUE)
        shouldBe(computed(value * 2), decimal);
}

// A collection empties the caches, and the first conversion after it fills the entry again.
// Each function gets its own collection so that it sees the empty entries itself.
let integers = [];
for (let i = -1030; i < 1030; ++i)
    integers.push(i);
// More keys than the int cache has entries, so that they evict each other.
for (let i = 0; i < 3000; ++i)
    integers.push(100000 + i * 7919, -100000 - i * 7919);
let expectedStrings = integers.map(i => JSON.stringify(i));

for (let convert of [computed2x, concat, template, callString, toStringDefault, toString10]) {
    gc();
    for (let i = 0; i < integers.length; ++i) {
        for (let j = 0; j < 2; ++j)
            shouldBe(convert(integers[i]), expectedStrings[i]);
    }
}
