function foo() {
    var array = [];
    for (let x = 0, [] = []; x < 10; ++x) { array.push(x); }
    return array;
}

var result = foo();
if (result.length != 10)
    throw "Error: bad length: " + result.length;
for (var i = 0; i < 10; ++i) {
    if (result[i] != i)
        throw "Error: bad entry at i = " + i + ": " + result[i];
}
if (result.length != 10)
    throw "Error: bad length: " + result.length;

// A destructuring pattern requires an initializer unless it is the head of for-in / for-of.
var error;
try {
    new Function("for (let x = 0, []; x < 10; ++x) { }");
} catch (e) {
    error = e;
}
if (!(error instanceof SyntaxError))
    throw "Error: should be a SyntaxError: " + error;
