function shouldBe(actual, expected) {
    if (actual !== expected)
        throw new Error(`expected ${expected} but got ${actual}`);
}

function replaceWithString(string, regexp) {
    return string.replace(regexp, "X");
}
noInline(replaceWithString);

function replaceWithFunction(string, regexp) {
    return string.replace(regexp, (match) => match.toUpperCase());
}
noInline(replaceWithFunction);

function replaceWithEmptyString(string, regexp) {
    return string.replace(regexp, "");
}
noInline(replaceWithEmptyString);

function replaceConstant() {
    let regexp = /b/y;
    regexp.lastIndex = 1;
    let result = "abc".replace(regexp, "X");
    return result + regexp.lastIndex;
}
noInline(replaceConstant);

for (let i = 0; i < testLoopCount; ++i) {
    let regexp = /ab/y;
    shouldBe(replaceWithString("ababcab", regexp), "Xabcab");
    shouldBe(regexp.lastIndex, 2);
    shouldBe(replaceWithString("ababcab", regexp), "abXcab");
    shouldBe(regexp.lastIndex, 4);
    shouldBe(replaceWithString("ababcab", regexp), "ababcab");
    shouldBe(regexp.lastIndex, 0);

    regexp.lastIndex = 5;
    shouldBe(replaceWithFunction("ababcab", regexp), "ababcAB");
    shouldBe(regexp.lastIndex, 7);
    regexp.lastIndex = 100;
    shouldBe(replaceWithFunction("ababcab", regexp), "ababcab");
    shouldBe(regexp.lastIndex, 0);

    regexp.lastIndex = 2;
    shouldBe(replaceWithEmptyString("ababcab", regexp), "abcab");
    shouldBe(regexp.lastIndex, 4);
    shouldBe(replaceWithEmptyString("ababcab", regexp), "ababcab");
    shouldBe(regexp.lastIndex, 0);

    let observedLastIndex;
    regexp.lastIndex = 2;
    shouldBe("ababcab".replace(regexp, () => { observedLastIndex = regexp.lastIndex; return "-"; }), "ab-cab");
    shouldBe(observedLastIndex, 4);

    let trim = /\s+/y;
    trim.lastIndex = 1;
    shouldBe(replaceWithEmptyString("  a", trim), " a");
    shouldBe(trim.lastIndex, 2);

    shouldBe(replaceConstant(), "aXc2");

    let globalSticky = /ab/gy;
    globalSticky.lastIndex = 3;
    shouldBe(replaceWithString("ababcab", globalSticky), "XXcab");
    shouldBe(globalSticky.lastIndex, 0);
}
