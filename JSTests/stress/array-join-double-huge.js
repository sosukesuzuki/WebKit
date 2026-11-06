//@ memoryHog!
//@ skip if $memoryLimited
//@ runDefault

// Results that are huge or too long have to behave the same as without a growing buffer.
function shouldBe(actual, expected) {
    if (actual !== expected)
        throw new Error(`expected ${expected} but got ${actual}`);
}

function shouldThrowOutOfMemory(func) {
    let error;
    try {
        func();
    } catch (e) {
        error = e;
    }
    shouldBe(String(error), 'RangeError: Out of memory');
}

const holes = [0.5];
holes.length = 1024;
shouldThrowOutOfMemory(() => holes.join('x'.repeat(2 ** 22)));
shouldThrowOutOfMemory(() => [0.5, 1.5, 2.5].join('x'.repeat(2 ** 30)));
shouldBe([0.5, 1.5].join('x'.repeat(1100000000)).length, 1100000006);

const array = [];
for (let i = 0; i < 1000000; ++i)
    array.push(i + 0.5);
for (const separator of [',', '\u3042'.repeat(64)])
    shouldBe(array.join(separator).length, 5888890 + 2000000 + 999999 * separator.length);

// A separator that is short enough, but too many elements.
for (let i = 1000000; i < 5300000; ++i)
    array.push(i + 0.5);
shouldBe(array.join('\u3042'.repeat(64)).length, 5888890 + 4300000 * 7 + 5300000 * 2 + 5299999 * 64);

const hole = [0.5];
delete hole[0];
shouldBe(hole.join('x'.repeat(2 ** 31 - 1)), '');
