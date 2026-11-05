function shouldBe(actual, expected) {
    if (actual !== expected)
        throw new Error(`expected ${expected} but got ${actual}`);
}

function expectedJoin(length, at, separator) {
    var result = "";
    for (var i = 0; i < length; ++i) {
        if (i)
            result += separator;
        result += String(at(i));
    }
    return result;
}

// The only element is a hole which is filled by the prototype, so Array.prototype.join gets it with [[Get]].
function withElementInPrototype(value) {
    var object = Object.create({ 0: value });
    object[1] = 0;
    object.length = 1;
    return object;
}

// The strings for [0, 1023] live as long as the VM does. The others can be evicted from the cache.
var boundaries = [-1, 0, 1, 9, 10, 99, 100, 1022, 1023, 1024, 1025, 65535, -1024, 2147483647, -2147483648];

function testTypedArrays() {
    for (var constructor of [Int8Array, Uint8Array, Uint8ClampedArray, Int16Array, Uint16Array, Int32Array, Uint32Array, Float16Array, Float32Array, Float64Array]) {
        let array = new constructor(boundaries);
        shouldBe(array.join(), expectedJoin(array.length, (i) => array[i], ","));

        for (var value of boundaries) {
            var single = new constructor([value]);
            shouldBe(single.join(), String(single[0]));
        }
        shouldBe(new constructor(0).join(), "");
        shouldBe(new constructor(3).join(), "0,0,0");
    }

    var bytes = new Uint8Array(256);
    for (var i = 0; i < bytes.length; ++i)
        bytes[i] = i;
    shouldBe(bytes.join(), expectedJoin(256, (i) => i, ","));

    var int32s = new Int32Array(boundaries);
    shouldBe(int32s.join(""), "-10191099100102210231024102565535-10242147483647-2147483648");
    shouldBe(int32s.join(", "), "-1, 0, 1, 9, 10, 99, 100, 1022, 1023, 1024, 1025, 65535, -1024, 2147483647, -2147483648");
    shouldBe(int32s.join("\u3042"), "-1\u30420\u30421\u30429\u304210\u304299\u3042100\u30421022\u30421023\u30421024\u30421025\u304265535\u3042-1024\u30422147483647\u3042-2147483648");

    var fractions = new Float64Array([0.5, 1, 1.5, 1023, 1023.5, 1024, -0, NaN, Infinity, 1e21]);
    shouldBe(fractions.join(), "0.5,1,1.5,1023,1023.5,1024,0,NaN,Infinity,1e+21");
}

// There are more numbers than the slots of the caches, so they evict each other while the joiner still has them.
// They are mixed with the numbers which are never evicted.
function testEviction() {
    var length = 3000;
    var int32s = new Int32Array(length);
    for (var i = 0; i < length; ++i)
        int32s[i] = (i & 1) ? (i & 1023) : 1024 + i * 7;
    shouldBe(int32s.join(), expectedJoin(length, (i) => int32s[i], ","));

    length = 10000;
    var doubles = [];
    for (var i = 0; i < length; ++i)
        doubles.push((i & 1) ? (i & 1023) : i + 0.25);
    shouldBe(doubles.join(), expectedJoin(length, (i) => doubles[i], ","));
}

function testArrays() {
    // ArrayWithDouble.
    shouldBe([0.5, 1, 1023, 1024, 2.5, 0, -1].join(), "0.5,1,1023,1024,2.5,0,-1");
    var singleDouble = [0.5];
    for (var value of [42, 4096, 7, 1023, 1024, -1]) {
        singleDouble[0] = value;
        shouldBe(singleDouble.join(), String(value));
    }

    // ArrayWithInt32 which has a hole.
    shouldBe([1, 2, , 1023, 1024, 5].join(), "1,2,,1023,1024,5");

    // ArrayWithContiguous which has a double, so that the length of each element is not known in advance.
    var mixed = [true, false, 1, 1023, 1024, 0.5, "string", null, undefined, true];
    shouldBe(mixed.join(), "true,false,1,1023,1024,0.5,string,,,true");
    shouldBe(mixed.join(""), "truefalse1102310240.5stringtrue");
    shouldBe(mixed.join("\u3042"), "true\u3042false\u30421\u30421023\u30421024\u30420.5\u3042string\u3042\u3042\u3042true");
    shouldBe([true, 0.5].join(), "true,0.5");
    shouldBe([0.5, false].join(), "0.5,false");

    // ArrayWithContiguous which has an object.
    var object = { toString() { return "object"; } };
    shouldBe([true, object, false, 12, object, 2048, 0.5].join(), "true,object,false,12,object,2048,0.5");
    shouldBe(String([[1, 0.5], [true, 1024.5]]), "1,0.5,true,1024.5");

    // The length is larger than the number of the elements, so each element is gotten with [[Get]].
    shouldBe(Array.prototype.join.call({ 0: true, 1: 7, 2: false, 3: 1024, 4: 0.5, 5: "string", length: 8 }), "true,7,false,1024,0.5,string,,");
    shouldBe(Array.prototype.join.call({ 0: 0.5, 1: 1023, 2: true, length: 4 }, ""), "0.51023true");
    for (var value of [true, false, 0, 9, 10, 512, 1023, 1024, -1, 1.5])
        shouldBe(Array.prototype.join.call(withElementInPrototype(value)), String(value));

    // Array.prototype.toString of ArrayWithArrayStorage.
    var arrayStorage = [true, 5, false, 1023, 1024];
    arrayStorage[100000] = 1;
    arrayStorage.length = 5;
    shouldBe(arrayStorage.toString(), "true,5,false,1023,1024");
    for (var value of [true, false, 0, 512, 1023, 2048, 0.5]) {
        arrayStorage.length = 0;
        arrayStorage[0] = value;
        shouldBe(arrayStorage.toString(), String(value));
    }
}

// toString() of an element overwrites the caches and collects garbage while the joiner has the other elements.
function testCachesOverwrittenWhileJoining() {
    var int32s = new Int32Array(3000);
    var fractions = new Float64Array(6000);
    for (var i = 0; i < int32s.length; ++i)
        int32s[i] = 1024 + i * 13;
    for (var i = 0; i < fractions.length; ++i)
        fractions[i] = i + 0.75;
    var object = {
        toString() {
            int32s.join();
            fractions.join();
            gc();
            return "object";
        }
    };
    var array = [1, 1023, true, 2048, 0.5, object, false, 7, 4096, 1.5, 512, -3];
    shouldBe(array.join(), "1,1023,true,2048,0.5,object,false,7,4096,1.5,512,-3");
}

// The results must stay valid after the joiner is gone and the caches are overwritten.
function testResultsOutliveCaches() {
    var results = [];
    for (var i = 0; i < 30; ++i) {
        results.push(new Int32Array([i, i + 1024, i * 1000003]).join());
        // The result of a single element shares the string with the cache.
        results.push(new Int32Array([i + 100]).join());
        results.push(new Int32Array([i + 2048]).join());
        results.push(new Float64Array([i + 0.5]).join());
        results.push(Array.prototype.join.call(withElementInPrototype(i & 1 ? true : false)));
    }
    var int32s = new Int32Array(3000);
    var fractions = new Float64Array(6000);
    for (var i = 0; i < int32s.length; ++i)
        int32s[i] = 1024 + i * 13;
    for (var i = 0; i < fractions.length; ++i)
        fractions[i] = i + 0.75;
    int32s.join();
    fractions.join();
    gc();
    for (var i = 0; i < 30; ++i) {
        shouldBe(results[i * 5], i + "," + (i + 1024) + "," + (i * 1000003));
        shouldBe(results[i * 5 + 1], String(i + 100));
        shouldBe(results[i * 5 + 2], String(i + 2048));
        shouldBe(results[i * 5 + 3], String(i + 0.5));
        shouldBe(results[i * 5 + 4], i & 1 ? "true" : "false");
    }
}

testTypedArrays();
testEviction();
testArrays();
testCachesOverwrittenWhileJoining();
testResultsOutliveCaches();

var smallInts = new Uint8Array([0, 9, 10, 255]);
var largeInts = new Int32Array([1023, 1024, -1, 65536]);
var smallDoubles = [0.5, 1, 1023, 1024];
var booleans = [true, false, 0.5];
var singleInt = new Uint16Array([512]);
var singleBoolean = withElementInPrototype(true);

function test() {
    shouldBe(smallInts.join(), "0,9,10,255");
    shouldBe(largeInts.join(""), "10231024-165536");
    shouldBe(smallDoubles.join(), "0.5,1,1023,1024");
    shouldBe(booleans.join("-"), "true-false-0.5");
    shouldBe(singleInt.join(), "512");
    shouldBe(Array.prototype.join.call(singleBoolean), "true");
}
noInline(test);

for (var i = 0; i < testLoopCount; ++i)
    test();
