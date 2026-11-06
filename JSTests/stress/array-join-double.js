function shouldBe(actual, expected) {
    if (actual !== expected)
        throw new Error(`expected ${expected} but got ${actual}`);
}

const separators = [undefined, '', ',', '--', '\u00e9', '\u3042', 'ab\u3042cd'];
// Around the limits for formatting on the stack (two elements) and in a growing buffer.
for (const length of [64, 65, 985, 986, 2009, 2010])
    separators.push('x'.repeat(length), '\u3042'.repeat(length));

function reference(array, separator = ',') {
    let result = '';
    for (let i = 0; i < array.length; ++i) {
        if (i)
            result += separator;
        if (array[i] !== undefined)
            result += String(array[i]);
    }
    return result;
}

function join(array, separator) {
    return array.join(separator);
}
noInline(join);

function check(array) {
    // The long separators take too long to test with everything.
    for (const separator of array.length > 128 ? [undefined, '', '\u3042', 'x'.repeat(65)] : separators)
        shouldBe(join(array, separator), reference(array, separator));
    shouldBe(array.toString(), reference(array));
    shouldBe(String(array), reference(array));
}

function shouldBeDouble(array) {
    if (!describe(array).includes('ArrayWithDouble'))
        throw new Error(`not an ArrayWithDouble: ${describe(array)}`);
}

// Leaves the array with a double butterfly and the given elements, where undefined means a hole.
// JSON.parse does not have an allocation profile, which could choose another indexing type.
function makeDouble(elements) {
    const array = JSON.parse('[0.5]');
    array.length = 0;
    array.length = elements.length;
    for (let i = 0; i < elements.length; ++i) {
        if (elements[i] !== undefined)
            array[i] = elements[i];
    }
    shouldBeDouble(array);
    return array;
}

let seed = 42;
function next() {
    seed = (seed + 0x9e3779b9) | 0;
    let t = seed ^ (seed >>> 16);
    t = Math.imul(t, 0x21f0aaad);
    t = t ^ (t >>> 15);
    t = Math.imul(t, 0x735a2d97);
    return (t ^ (t >>> 15)) >>> 0;
}

const values = [
    0, -0, 1, -1, 0.5, 0.1, -0.1, 1 / 3, 1e21, 1e-7, 123456789.125, 1e20, 123e-20,
    2 ** 31 - 1, 2 ** 31, -(2 ** 31), -(2 ** 31) - 1, 2 ** 32,
    2 ** 53 - 1, 2 ** 53, 2 ** 53 + 2, -(2 ** 53), 2 ** 60, 2 ** 64,
    Number.MAX_VALUE, -Number.MAX_VALUE, Number.MIN_VALUE, -1.2345678901234567e-300, Infinity, -Infinity,
];

{
    const array = makeDouble(values);
    check(array);
}
for (const value of values) {
    check(makeDouble([value]));
    check(makeDouble([value, value]));
    check(makeDouble([undefined, value]));
    check(makeDouble([value, undefined]));
    check(makeDouble([undefined, value, undefined]));
}

// NaN is the hole, so it can not be stored in a double butterfly.
check([0.5, NaN, 1.5]);
check([NaN]);

// Only holes.
check(makeDouble([]));
for (const length of [1, 2, 65, 1000])
    check(makeDouble(new Array(length).fill(undefined)));

// Around the number of elements that are sampled to estimate the length of the result.
for (const length of [1, 2, 3, 13, 39, 40, 41, 63, 64, 65, 66, 102, 103, 128, 1024]) {
    const numbers = [];
    for (let i = 0; i < length; ++i)
        numbers.push((next() / 0x100000000 - 0.5) * 10 ** ((next() % 40) - 20));
    check(makeDouble(numbers));
    check(makeDouble(numbers.map((value, i) => i & 1 ? undefined : value)));
    check(makeDouble(numbers.map((value, i) => i & 1 ? value : undefined)));
    // The sample is nothing like the rest.
    check(makeDouble(numbers.map((value, i) => i < 64 ? undefined : -1.2345678901234567e-300)));
    check(makeDouble(numbers.map((value, i) => i < 64 ? 1 : -1.2345678901234567e-300)));
    check(makeDouble(numbers.map((value, i) => i < 64 ? -1.2345678901234567e-300 : 1)));
    check(makeDouble(numbers.map((value, i) => i < 64 ? -1.2345678901234567e-300 : undefined)));
}

// Each number is formatted the first time, gets a cached string the second time, and is copied from
// that afterwards.
{
    const numbers = [0.625, -1.2345678901234567e-300, 1e21, NaN, Infinity, 1 / 3];
    for (let i = 0; i < 4; ++i) {
        for (const separator of [',', '\u3042']) {
            shouldBe(makeDouble([0.625, 1e21, 1 / 3]).join(separator), ['0.625', '1e+21', '0.3333333333333333'].join(separator));
            shouldBe(new Float64Array(numbers).join(separator), ['0.625', '-1.2345678901234568e-300', '1e+21', 'NaN', 'Infinity', '0.3333333333333333'].join(separator));
            shouldBe(new Float32Array([0.625, 1.1]).join(separator), ['0.625', '1.100000023841858'].join(separator));
        }
        shouldBe(String(numbers[i]), ['0.625', '-1.2345678901234568e-300', '1e+21', 'NaN'][i]);
        gc();
    }
}

// The sampled elements decide whether the rest is looked up.
for (const f of [i => 1.1, i => 1.1 + i, i => i < 64 ? 1.1 : i + 0.1, i => i < 64 ? i + 0.1 : 1.1, i => i & 1 ? 1.1 : i / 7]) {
    for (let i = 0; i < 3; ++i) {
        const array = Array.from({ length: 200 }, (_, i) => f(i));
        const expected = array.map(value => JSON.stringify(value));
        for (const separator of ['', ',', '--', '\u3042']) {
            shouldBe(makeDouble(array).join(separator), expected.join(separator));
            shouldBe(new Float64Array(array).join(separator), expected.join(separator));
        }
    }
}

// Numbers that have the same entry in the cache, which hashes both halves with xor.
{
    const words = new Uint32Array(2);
    const double = new Float64Array(words.buffer);
    const colliding = [];
    for (let i = 0; i < 16; ++i) {
        words[0] = (0x1234567 + i * 0x1000) ^ i;
        words[1] = 0x3ff80000 ^ i;
        colliding.push(double[0]);
    }
    const expected = colliding.map(value => JSON.stringify(value));
    for (let i = 0; i < 4; ++i) {
        shouldBe(makeDouble(colliding).join(), expected.join());
        for (let j = 0; j < colliding.length; ++j) {
            const pair = makeDouble([colliding[j], colliding[j], colliding[(j + 1) % 16]]);
            shouldBe(pair.join(), [expected[j], expected[j], expected[(j + 1) % 16]].join());
            shouldBe(String(colliding[j]), expected[j]);
            shouldBe(`${colliding[(j + 1) % 16]}`, expected[(j + 1) % 16]);
        }
    }
}

// Copy on write literals, whose result is cached, and one with a hole.
function literal() {
    return [0.5, 1.5, 2.5, 1e21];
}
function literalWithHole() {
    return [0.5, , 2.5];
}
for (let i = 0; i < 10; ++i) {
    shouldBe(literal().toString(), '0.5,1.5,2.5,1e+21');
    shouldBe(literal().join('-'), '0.5-1.5-2.5-1e+21');
    shouldBe(literalWithHole().toString(), '0.5,,2.5');
}

// The separator's toString changes the array.
{
    const array = makeDouble([0.5, 1.5, 2.5]);
    shouldBe(array.join({ toString() { array.length = 1; return '-'; } }), '0.5--');
}
{
    const array = makeDouble([0.5, 1.5, 2.5]);
    shouldBe(array.join({ toString() { array.push(3.5); return '-'; } }), '0.5-1.5-2.5');
}
{
    const array = makeDouble([0.5, 1.5, 2.5]);
    shouldBe(array.join({ toString() { delete array[1]; return '\u3042'; } }), '0.5\u3042\u30422.5');
}

// Not a JSArray.
{
    const object = { 0: 0.5, 1: 1.5, 2: 2.5, length: 3 };
    for (const separator of separators)
        shouldBe(Array.prototype.join.call(object, separator), reference([0.5, 1.5, 2.5], separator));
    object.length = 2;
    shouldBe(Array.prototype.join.call(object), '0.5,1.5');
    object.length = 5;
    shouldBe(Array.prototype.join.call(object), '0.5,1.5,2.5,,');
}

// Hot enough for the DFG's and the FTL's ArrayJoin.
{
    const array = makeDouble([0.5, undefined, -0, 1e21, 2 ** 40]);
    for (let i = 0; i < testLoopCount; ++i)
        shouldBe(join(array, ','), '0.5,,0,1e+21,1099511627776');
}

// The result is too long.
{
    const array = makeDouble(new Array(1024).fill(undefined));
    array[0] = 0.5;
    let error;
    try {
        array.join('x'.repeat(2 ** 22));
    } catch (e) {
        error = e;
    }
    shouldBe(String(error), 'RangeError: Out of memory');
}

// Holes that have to be looked up in the prototype chain.
function checkForwarding(length) {
    const array = makeDouble(Array.from({ length }, (_, i) => i === 1 || i === length - 1 ? undefined : i + 0.5));
    Array.prototype[1] = 'proto';
    shouldBeDouble(array);
    const expected = reference(array, '-');
    shouldBe(expected.startsWith('0.5-proto-2.5'), true);
    shouldBe(expected.endsWith('-'), true);
    shouldBe(array.join('-'), expected);
    shouldBe(makeDouble([0.5, 1.5]).join(), '0.5,1.5');
    shouldBe(makeDouble([undefined]).join(), '');
    delete Array.prototype[1];
    shouldBe(array.join('-'), reference(array, '-'));
}
checkForwarding(4);
checkForwarding(1000);

// These change how makeDouble allocates, so keep them last.
{
    const array = makeDouble([0.5, 1.5, 2.5]);
    shouldBe(array.join({ toString() { array[1] = 'x'; return '-'; } }), '0.5-x-2.5');
}
