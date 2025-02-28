function shouldThrow(run, errorType) {
    let actual;
    var hadError = false;

    try {
        actual = run();
    } catch (e) {
        hadError = true;
        actual = e;
    }

    if (!hadError)
        throw new Error("Expected " + run + "() to throw " + errorType.name + ", but did not throw.");
    if (!(actual instanceof errorType))
        throw new Error("Expeced " + run + "() to throw " + errorType.name + " , but threw '" + actual + "'");
}

{
    const re = /abc/;
    Object.defineProperty(re, "lastIndex", { value: -1, writable: false });
    shouldThrow(() => {
        re[Symbol.search]("a")
    }, TypeError);
}

{
    const re = /abc/g;
    Object.defineProperty(re, "lastIndex", { value: 0, writable: false });
    shouldThrow(() => {
        re[Symbol.search]("a")
    }, TypeError);
}

{
    const re = /abc/y;
    Object.defineProperty(re, "lastIndex", { value: 0, writable: false });
    shouldThrow(() => {
        re[Symbol.search]("a")
    }, TypeError);
}
