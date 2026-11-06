// A RegExp which consists of exactly one character class is matched against 16-bit strings without Yarr when the class
// is made of a few ranges. Check it against the same class wrapped in a pattern which always goes to Yarr.

function shouldBe(actual, expected, message) {
    if (!Object.is(actual, expected))
        throw new Error(`${message}: expected ${String(expected)} but got ${String(actual)}`);
}

const sources = [
    // Single character classes. Some of them have too many ranges or no members at all.
    String.raw`[\u0000-\u001f"\\\ud800-\udfff]`,
    String.raw`[\u0000-\u001f\u0022\u005c\ud800-\udfff]`,
    String.raw`[^\u0000-\u001f"\\\ud800-\udfff]`,
    String.raw`[ab]`,
    String.raw`[ac]`,
    String.raw`[ace]`,
    String.raw`[aceg]`,
    String.raw`[acegi]`,
    String.raw`[^\0-\x1fa-z]`,
    String.raw`[^\0-\x3f]`,
    String.raw`[^\0-\x3e]`,
    String.raw`[^a-zA-Z0-9\x80-\uff00]`,
    String.raw`[^ab]`,
    String.raw`[^ac]`,
    String.raw`[^ace]`,
    String.raw`[^aceg]`,
    String.raw`[&<>"']`,
    String.raw`[&<>]`,
    String.raw`[a-cb-d]`,
    String.raw`[\xf0-\u0110]`,
    String.raw`[^\xf0-\u0110]`,
    String.raw`[\xff\u0100]`,
    String.raw`[\0-\x7f]`,
    String.raw`[^\0-\x7f]`,
    String.raw`[\0\uffff]`,
    String.raw`[^\0\uffff]`,
    String.raw`[\0-\uffff]`,
    String.raw`[^\0-\uffff]`,
    String.raw`[\0-\ufffe]`,
    String.raw`[\ufffe\uffff]`,
    String.raw`[^\ufffe\uffff]`,
    String.raw`[\u7fff\u8001]`,
    String.raw`[\u7ffe-\u8001]`,
    String.raw`[\ud800-\udbff]`,
    String.raw`[\udc00-\udfff]`,
    String.raw`[\ud83d\ude00]`,
    String.raw`[\s\S]`,
    String.raw`[]`,
    String.raw`[^]`,
    String.raw`.`,
    String.raw`\d`,
    String.raw`\D`,
    String.raw`\w`,
    String.raw`\W`,
    String.raw`\s`,
    String.raw`\S`,
    String.raw`[\d\x0a]`,
    String.raw`[k-l]`,
    String.raw`[ks]`,
    String.raw`[\u212a\u017f]`,
    String.raw`[^k-s]`,
    String.raw`[\u03b1-\u03c9]`,
    String.raw`[\u3040-\u30ff]`,
    // Not a single character class.
    String.raw`[ab]?`,
    String.raw`[ab]*`,
    String.raw`[ab]+`,
    String.raw`[ab]{2}`,
    String.raw`[ab]{0}`,
    String.raw`[ab]??`,
    String.raw`([ab])`,
    String.raw`(?:[ab])`,
    String.raw`(?<n>[ab])`,
    String.raw`(?=[ab])`,
    String.raw`(?![ab])`,
    String.raw`(?<=[ab])`,
    String.raw`(?<![ab])`,
    String.raw`(?i:[ab])`,
    String.raw`(?-i:[ab])`,
    String.raw`(?s:.)`,
    String.raw`^[ab]`,
    String.raw`[ab]$`,
    String.raw`[ab]\b`,
    String.raw`[ab]|`,
    String.raw`[ab]|[cd]`,
];

const unicodeSources = [
    String.raw`\p{ASCII}`,
    String.raw`\P{ASCII}`,
    String.raw`\p{Script=Hiragana}`,
    String.raw`\p{Script=Cyrillic}`,
    String.raw`\p{Lu}`,
    String.raw`[\u{1f600}-\u{1f64f}]`,
    String.raw`[a\u{1f600}]`,
    String.raw`[^\u{1f600}]`,
];

const unicodeSetsSources = [
    String.raw`[[a-z]--[aeiou]]`,
    String.raw`[[a-z]&&[a-c]]`,
    String.raw`[[a-z]--[b-y]]`,
    String.raw`[\q{abc|d}]`,
    String.raw`[^[a-z]&&[a-c]]`,
];

const singleClassCount = sources.indexOf("[ab]?");

let seed = 0x12345;
function random(n) {
    seed = (Math.imul(seed, 1103515245) + 12345) & 0x7fffffff;
    return (seed >>> 8) % n;
}

const interesting = [
    0x0, 0x1, 0x9, 0xa, 0xd, 0x1f, 0x20, 0x22, 0x26, 0x27, 0x2f, 0x30, 0x39, 0x3a, 0x3c, 0x3e, 0x41, 0x4b, 0x53, 0x5b, 0x5c, 0x5f,
    0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x69, 0x6b, 0x6c, 0x73, 0x7a, 0x7f, 0x80, 0xa0, 0xef, 0xf0, 0xff, 0x100, 0x110, 0x111,
    0x17f, 0x391, 0x3a9, 0x3b1, 0x3c9, 0x2028, 0x2029, 0x212a, 0x3042, 0x30a2, 0x7ffe, 0x7fff, 0x8000, 0x8001, 0x8002, 0xd7ff, 0xd800, 0xd83d, 0xdbff, 0xdc00,
    0xde00, 0xdfff, 0xe000, 0xfeff, 0xfffd, 0xfffe, 0xffff,
];

// Force a 16-bit string even if all the characters are Latin-1, by slicing it off a 16-bit string. This does not work only for
// one-character Latin-1 strings.
function make16Bit(codeUnits) {
    let string = "\u3042" + String.fromCharCode(...codeUnits);
    string[0]; // resolve
    return string.substring(1);
}

const subjects = [];
// One interesting character after a varying number of boring ones, for each length around the vector sizes.
for (let length of [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 15, 17]) {
    subjects.push(make16Bit(new Array(length).fill(0x4e00)));
    for (let i = random(3); i < length; i += 3) {
        let codeUnits = new Array(length).fill(0x4e00);
        codeUnits[i] = interesting[random(interesting.length)];
        subjects.push(make16Bit(codeUnits));
    }
}
// Contains every interesting character once, far from each other.
subjects.push(make16Bit(interesting.flatMap((c) => [c, 0x4e00, 0x4e00, 0x4e00])));

function check(source, flags) {
    const tested = new RegExp(source, flags);
    const testedGlobal = new RegExp(source, flags + "g");
    const testedIndices = new RegExp(source, flags + "d");
    const testedSticky = new RegExp(source, flags + "y");
    // A capturing group does not change what is matched, but it makes Yarr necessary.
    const reference = new RegExp(`(${source})`, flags);
    const referenceGlobal = new RegExp(`(${source})`, flags + "g");
    const referenceSticky = new RegExp(`(${source})`, flags + "y");
    const referenceSplit = new RegExp(`(?:${source})(?=[^]|$)`, flags);

    const canMatchEmpty = tested.exec("")?.[0] === "" || tested.exec("a")?.[0] === "" || tested.exec(".")?.[0] === "";

    for (let subjectIndex = 0; subjectIndex < subjects.length; ++subjectIndex) {
        const subject = subjects[subjectIndex];
        const message = `/${source}/${flags} against subjects[${subjectIndex}]`;
        const expected = reference.exec(subject);
        const expectedIndex = expected ? expected.index : -1;
        shouldBe(tested.test(subject), !!expected, message);
        shouldBe(subject.search(tested), expectedIndex, message);

        const actual = tested.exec(subject);
        shouldBe(actual === null, expected === null, message);
        if (actual) {
            shouldBe(actual.index, expectedIndex, message);
            shouldBe(actual[0], expected[0], message);
            shouldBe(actual.length, expected.length - 1, message);
            shouldBe(RegExp.lastMatch, expected[0], message);
            shouldBe(RegExp.leftContext, subject.substring(0, expectedIndex), message);
            const indices = testedIndices.exec(subject).indices[0];
            shouldBe(indices[0], expectedIndex, message);
            shouldBe(indices[1], expectedIndex + expected[0].length, message);
        }

        shouldBe(JSON.stringify(subject.match(testedGlobal)), JSON.stringify(subject.match(referenceGlobal)), message);
        shouldBe(subject.replace(testedGlobal, "<$&>"), subject.replace(referenceGlobal, "<$&>"), message);
        shouldBe(subject.replace(testedGlobal, ""), subject.replace(referenceGlobal, ""), message);
        if (!canMatchEmpty)
            shouldBe(JSON.stringify(subject.split(tested)), JSON.stringify(subject.split(referenceSplit)), message);

        for (const lastIndex of [1, subject.length - 1, subject.length, subject.length + 1]) {
            for (const [actualRegExp, expectedRegExp] of [[testedGlobal, referenceGlobal], [testedSticky, referenceSticky]]) {
                actualRegExp.lastIndex = lastIndex;
                expectedRegExp.lastIndex = lastIndex;
                shouldBe(actualRegExp.test(subject), expectedRegExp.test(subject), message);
                shouldBe(actualRegExp.lastIndex, expectedRegExp.lastIndex, message);
            }
        }
        testedGlobal.lastIndex = 0;
        referenceGlobal.lastIndex = 0;
    }
}

for (const source of sources) {
    check(source, "");
    check(source, "i");
}
check("[ac]", "ms");
check(".", "s");
for (const source of sources.slice(0, singleClassCount).concat(unicodeSources)) {
    check(source, "u");
    check(source, "iv");
}
for (const source of unicodeSetsSources)
    check(source, "v");

// Check all the code units around the boundaries.
for (const source of sources.slice(0, singleClassCount)) {
    const tested = new RegExp(source, "g");
    const reference = new RegExp(`(${source})`, "g");
    for (let base of [0, 0x100, 0x2000, 0xd780, 0xff00]) {
        let codeUnits = [];
        for (let i = 0; i < 0x100; ++i)
            codeUnits.push(base + i);
        const subject = make16Bit(codeUnits);
        shouldBe(subject.replace(tested, ""), subject.replace(reference, ""), `/${source}/ from ${base}`);
    }
}

// The same RegExp is used with 8-bit and 16-bit strings alternately, from hot code.
(function () {
    const regExp = /[\u0000-\u001f"\\\ud800-\udfff]/;
    const ascii = "the quick brown fox jumps over the lazy dog";
    function test(string) { return regExp.test(string); }
    noInline(test);
    for (let i = 0; i < 2000; ++i) {
        shouldBe(test(ascii), false, "8-bit");
        shouldBe(test(ascii + "\""), true, "8-bit");
        shouldBe(test(ascii + "\u3042"), false, "16-bit");
        shouldBe(test("\u3042" + ascii + "\""), true, "16-bit");
        shouldBe(test(ascii + "\ud800\u3042"), true, "16-bit");
    }
}());

// Constant folding by the compiler threads.
(function () {
    function test() { return /[\u0000-\u001f"\\]/.exec("\u3042\u3044\u3046\u3048\u304a\u304b\u304d\u304f\u3051\u3053\"\u3055").index; }
    noInline(test);
    for (let i = 0; i < 2000; ++i)
        shouldBe(test(), 10, "constant");
}());
