function foo(value, proto)
{
    return value instanceof proto;
}

noInline(foo);

for (var i = 0; i < testLoopCount; ++i) {
    var result = foo(Symbol("hello"), Symbol);
    if (result)
        throw "Error: bad result: " + result;
}

