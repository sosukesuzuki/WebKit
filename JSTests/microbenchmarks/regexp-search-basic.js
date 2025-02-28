function shouldBe(a, b) {
    if (a !== b)
        throw new Error(`Expected ${b} but got ${a}`);
}

const re = /foo/;
for (let i = 0; i < 1e5; i++) {
    shouldBe(re[Symbol.search]("abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzfoo"), 78);
}
