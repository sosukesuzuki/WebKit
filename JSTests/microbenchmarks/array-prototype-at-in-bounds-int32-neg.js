function test(array) {
    var result;
    for (let i = 0; i < 1e6; i++) {
        result = array.at(-4);
    }
    return result;
}

noInline(test);

var array = [12,4,4,66,56,44,44,38,65,89,2,45,789,56,432,677,2234,77,3457,133,6544,76,17,322,34];
var result = test(array);
if (result != 76)
    throw "Bad result: " + result;

