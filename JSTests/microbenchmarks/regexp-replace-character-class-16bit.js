(function () {
    function strip(string) {
        return string.replace(/[<>&b/]/g, "");
    }
    noInline(strip);

    const string = "これは<b>太字</b>の文字列です。そして&まだまだ続きます。".repeat(20);
    const expected = string.length - 8 * 20;
    for (let i = 0; i < 1e4; ++i) {
        if (strip(string).length !== expected)
            throw new Error("bad");
    }
}());
