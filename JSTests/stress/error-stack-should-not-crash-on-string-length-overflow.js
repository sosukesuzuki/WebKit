//@ skip if $addressBits <= 32
//@ memoryHog!
//@ runDefault
// Formatting a stack trace longer than the maximum string length should not crash.

function shouldBe(actual, expected, message) {
    if (actual !== expected)
        throw new Error(`${message}: expected length ${expected.length} but got ${String(actual).length}`);
}

const hugeName = "a".repeat(2 ** 30);
const maxName = "a".repeat(2 ** 31 - 1);

function call(n, callback) {
    if (n)
        return call(n - 1, callback);
    return callback();
}

// The sum of the frames overflows.
call.displayName = hugeName;
shouldBe(call(1, () => new Error).stack, "", "error.stack");

const plain = {};
call(1, () => Error.captureStackTrace(plain));
shouldBe(plain.stack, "", "captureStackTrace on a plain object");

const captured = new Error;
call(1, () => Error.captureStackTrace(captured));
shouldBe(captured.stack, "", "captureStackTrace on an error");

if (typeof WebAssembly !== "undefined" && WebAssembly.Tag)
    call(1, () => new WebAssembly.Exception(new WebAssembly.Tag({ parameters: [] }), [], { traceStack: true }));

// line and column are still available.
const error = call(1, () => new Error);
shouldBe(typeof error.line, "number", "error.line");
shouldBe(error.stack, "", "error.stack after error.line");

// A single frame overflows.
call.displayName = maxName;
shouldBe(call(0, () => new Error).stack, "", "single frame");

// The first frame exactly fits, the line break after it overflows, and the next frame is 16-bit.
function outerFrame() { return call(0, () => new Error); }
outerFrame.displayName = "\u3042";
call.displayName = "";
const frames = outerFrame().stack.split("\n");
const prefixLength = frames[0].length + 1 + frames[1].length;
call.displayName = "a".repeat(2 ** 31 - 1 - prefixLength);
shouldBe(outerFrame().stack, "", "overflow at the line break");

// A dead frame makes the GC format the trace.
function makeGarbageFrames() {
    const errors = [];
    for (let i = 0; i < 3; ++i) {
        const dying = new Function("n", "callback", "self", "return n ? self(n - 1, callback, self) : callback();");
        dying.displayName = hugeName;
        errors.push(dying(1, () => new Error, dying));
        const capturing = new Error;
        dying(1, () => Error.captureStackTrace(capturing), dying);
        errors.push(capturing);
    }
    return errors;
}
noInline(makeGarbageFrames);
const errors = makeGarbageFrames();
fullGC();
for (const error of errors)
    shouldBe(error.stack, "", "stack formatted by the GC");

// Normal traces are unaffected.
call.displayName = "renamed";
if (!call(0, () => new Error).stack.includes("\nrenamed@"))
    throw new Error("displayName should still be used");
