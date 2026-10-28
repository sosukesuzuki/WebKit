function shouldBe(actual, expected) {
    if (actual !== expected)
        throw new Error(`expected ${expected} but got ${actual}`);
}

function parameter(v) {
    switch (v) {
    case (v = 2, 0): return "zero:" + v;
    case 1: return "one:" + v;
    case 2: return "two:" + v;
    default: return "default:" + v;
    }
}

function letVariable() {
    let v = 1;
    switch (v) {
    case (v = 2, 0): return "zero:" + v;
    case 1: return "one:" + v;
    case 2: return "two:" + v;
    default: return "default:" + v;
    }
}

function varVariable() {
    var v = 1;
    switch (v) {
    case (v = 2, 0): return "zero:" + v;
    case 1: return "one:" + v;
    case 2: return "two:" + v;
    default: return "default:" + v;
    }
}

function postfixInOwnClause(v) {
    switch (v) {
    case v++: return "same:" + v;
    default: return "default:" + v;
    }
}

function prefixInOwnClause(v) {
    switch (v) {
    case ++v: return "incremented:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

function postfixDecrement(v) {
    switch (v) {
    case (v--, 5): return "five:" + v;
    case 0: return "zero:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

function compound(v) {
    switch (v) {
    case (v += 1, 0): return "zero:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

function logical(v) {
    switch (v) {
    case (v &&= 2, 0): return "zero:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

function arrayDestructuring(v) {
    switch (v) {
    case ([v] = [2], 0): return "zero:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

function objectDestructuring(v) {
    switch (v) {
    case ({ v } = { v: 2 }, 0): return "zero:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

function afterDefault(v) {
    switch (v) {
    default: return "default:" + v;
    case (v = 2, 0): return "zero:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    }
}

function beforeDefault(v) {
    switch (v) {
    case (v = 2, 0): return "zero:" + v;
    default: return "default:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    }
}

function fallsToDefault(v) {
    switch (v) {
    case (v = 2, 0): return "zero:" + v;
    case 2: return "two:" + v;
    default: return "default:" + v;
    }
}

function commaDiscriminant(v) {
    switch (0, v) {
    case (v = 2, 0): return "zero:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

function assignmentDiscriminant(v) {
    switch (v = 1) {
    case (v = 2, 0): return "zero:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

function compoundDiscriminant(v) {
    switch (v += 1) {
    case (v = 2, 0): return "zero:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

function logicalDiscriminant(v) {
    switch (v ||= 5) {
    case (v = 2, 0): return "zero:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

function prefixDiscriminant(v) {
    switch (++v) {
    case (v = 2, 0): return "zero:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

function severalAssignments(v) {
    switch (v) {
    case (v = 2, 0):
    case (v = 3, 2):
    case (v = 4, 3):
        return "wrong:" + v;
    case 1:
        return "one:" + v;
    }
}

function nestedInCall(v) {
    switch (v) {
    case Math.max(v = 2, 5): return "five:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

function nestedSwitch(v, w) {
    switch (v) {
    case 0:
        return "zero:" + v;
    case w:
        switch (w) {
        case (w = 2, v = 3, 0): return "inner zero:" + v + w;
        case 2: return "inner two:" + v + w;
        case 1: return "inner one:" + v + w;
        }
        return "none";
    default:
        return "default:" + v;
    }
}

function stringDiscriminant(v) {
    switch (v) {
    case (v = "b", "c"): return "c:" + v;
    case "b": return "b:" + v;
    case "a": return "a:" + v;
    default: return "default:" + v;
    }
}

function assignmentOnlyInBody(v) {
    switch (v) {
    case Math.PI: v = 5; return "pi:" + v;
    case 1: v = 2;
    case 2: return "two:" + v;
    default: return "default:" + v;
    }
}

function* generator(v) {
    switch (v) {
    case (v = yield v): return "sent:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

function runGenerator() {
    let iterator = generator(1);
    iterator.next();
    return iterator.next(2).value;
}

function closure(v) {
    function set() { v = 2; return 0; }
    switch (v) {
    case set(): return "zero:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

function directEval(v) {
    switch (v) {
    case eval("v = 2, 0"): return "zero:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

function mappedArguments(v) {
    switch (v) {
    case (arguments[0] = 2, 0): return "zero:" + v;
    case 2: return "two:" + v;
    case 1: return "one:" + v;
    default: return "default:" + v;
    }
}

let programResult;
{
    let v = 1;
    switch (v) {
    case (v = 2, 0): programResult = "zero:" + v; break;
    case 2: programResult = "two:" + v; break;
    case 1: programResult = "one:" + v; break;
    default: programResult = "default:" + v; break;
    }
}
shouldBe(programResult, "one:2");

for (let i = 0; i < testLoopCount; ++i) {
    shouldBe(parameter(1), "one:2");
    shouldBe(parameter(0), "zero:2");
    shouldBe(parameter(2), "two:2");
    shouldBe(parameter(3), "default:2");
    shouldBe(letVariable(), "one:2");
    shouldBe(varVariable(), "one:2");
    shouldBe(postfixInOwnClause(1), "same:2");
    shouldBe(prefixInOwnClause(1), "one:2");
    shouldBe(postfixDecrement(1), "one:0");
    shouldBe(compound(1), "one:2");
    shouldBe(logical(1), "one:2");
    shouldBe(arrayDestructuring(1), "one:2");
    shouldBe(objectDestructuring(1), "one:2");
    shouldBe(afterDefault(1), "one:2");
    shouldBe(afterDefault(3), "default:2");
    shouldBe(beforeDefault(1), "one:2");
    shouldBe(fallsToDefault(1), "default:2");
    shouldBe(commaDiscriminant(1), "one:2");
    shouldBe(assignmentDiscriminant(0), "one:2");
    shouldBe(compoundDiscriminant(0), "one:2");
    shouldBe(logicalDiscriminant(1), "one:2");
    shouldBe(prefixDiscriminant(0), "one:2");
    shouldBe(severalAssignments(1), "one:4");
    shouldBe(nestedInCall(1), "one:2");
    shouldBe(nestedSwitch(1, 1), "inner one:32");
    shouldBe(stringDiscriminant("a"), "a:b");
    shouldBe(assignmentOnlyInBody(1), "two:2");
    shouldBe(runGenerator(), "one:2");
    shouldBe(closure(1), "one:2");
    shouldBe(directEval(1), "one:2");
    shouldBe(mappedArguments(1), "one:2");
}
