//@ requireOptions("--useMathClamp=1")

function shouldBe(a, b) {
  if (a !== b)
    throw new Error(`Expected ${b} but got ${a}`);
}

function shouldThrow(func, errorType, message) {
    let error;
    try { func(); } catch (e) { error = e; }
    if (!(error instanceof errorType))
        throw new Error(`Expected ${errorType.name}!`);
    if (message !== undefined)
        shouldBe(String(error), message);
}

shouldThrow(() => Math.clamp("1", 0, 1), TypeError);
shouldThrow(() => Math.clamp(1, "0", 1), TypeError);
shouldThrow(() => Math.clamp(1, 0, "1"), TypeError);

shouldBe(Number.isNaN(Math.clamp(1, NaN, 2)), true);
shouldBe(Number.isNaN(Math.clamp(1, -2, NaN)), true);
shouldBe(Number.isNaN(Math.clamp(NaN, -2, 2)), true);

shouldBe(Object.is(Math.clamp(+0, -0, -0), -0), true);
shouldBe(Object.is(Math.clamp(-0, +0, 1), +0), true);
shouldBe(Object.is(Math.clamp(+0, -0, 1), +0), true);
shouldBe(Object.is(Math.clamp(-0, -1, +0), -0), true);
shouldBe(Object.is(Math.clamp(+0, -1, -0), -0), true);

shouldBe(Object.is(Math.clamp(5, 2, 2), 2), true);
shouldBe(Math.clamp(-5, -2, 2), -2);
shouldBe(Math.clamp(5, -2, 2), 2);
shouldBe(Math.clamp(1, -2, 2), 1);
