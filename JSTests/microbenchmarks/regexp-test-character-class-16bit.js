(function () {
    // What fast-json-stringify style serializers ask for each string.
    const needsEscape = /[\u0000-\u001f\u0022\u005c\ud800-\udfff]/;

    function test(string) {
        return needsEscape.test(string);
    }
    noInline(test);

    const string = "これは JSON にシリアライズされる日本語の文字列です。".repeat(20);
    for (let i = 0; i < 1e5; ++i) {
        if (test(string))
            throw new Error("bad");
    }
}());
