function shouldBe(actual, expected) {
    if (actual !== expected)
        throw new Error(`expected ${expected} but got ${actual}`);
}

let valueGetterCount = 0;
function makeIterable(count) {
    let results = [];
    return {
        results,
        [Symbol.iterator]() {
            let index = 0;
            return {
                next(sent) {
                    let result = { sent, extra: index, done: index++ >= count, get value() { valueGetterCount++; return index; } };
                    results.push(result);
                    return result;
                },
                return(value) {
                    let result = { value, done: false, fromReturn: true };
                    results.push(result);
                    return result;
                },
                throw(value) {
                    let result = { value, done: false, fromThrow: true };
                    results.push(result);
                    return result;
                },
            };
        }
    };
}

function* delegate(iterable) {
    let before = yield "before";
    let result = yield* iterable;
    let after = yield "after";
    return [before, result, after];
}

for (let i = 0; i < testLoopCount / 2; ++i) {
    valueGetterCount = 0;
    let iterable = makeIterable(3);
    let generator = delegate(iterable);

    let first = generator.next();
    shouldBe(first.value, "before");
    shouldBe(first.done, false);

    for (let j = 0; j < 3; ++j) {
        let result = generator.next(j);
        shouldBe(result, iterable.results[j]);
        shouldBe(result.extra, j);
    }
    shouldBe(iterable.results[0].sent, undefined);
    shouldBe(iterable.results[1].sent, 1);
    shouldBe(valueGetterCount, 0);

    shouldBe(generator.return("r"), iterable.results[3]);
    shouldBe(iterable.results[3].fromReturn, true);
    shouldBe(generator.throw("t"), iterable.results[4]);
    shouldBe(iterable.results[4].fromThrow, true);
    shouldBe(valueGetterCount, 0);

    let after = generator.next();
    shouldBe(valueGetterCount, 1);
    shouldBe(after.value, "after");
    shouldBe(after.done, false);
    shouldBe(Object.keys(after).join(), "value,done");

    let last = generator.next("x");
    shouldBe(last.done, true);
    shouldBe(last.value.join(), "0,4,x");
    shouldBe(generator.next().done, true);
}
