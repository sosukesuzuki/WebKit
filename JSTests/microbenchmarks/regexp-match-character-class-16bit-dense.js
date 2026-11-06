(function () {
    // All of the characters match, so each match ends immediately.
    function count(string) {
        return string.match(/./g).length;
    }
    noInline(count);

    const string = "ひらがなばかりのもじれつではほとんどのもじがすぐにまっちします。".repeat(10);
    for (let i = 0; i < 5e3; ++i) {
        if (count(string) !== string.length)
            throw new Error("bad");
    }
}());
