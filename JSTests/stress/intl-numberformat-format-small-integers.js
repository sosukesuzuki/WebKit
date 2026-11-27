function shouldBe(actual, expected, message) {
    if (actual !== expected)
        throw new Error(`${message}: expected ${JSON.stringify(expected)} but got ${JSON.stringify(actual)}`);
}

// formatToParts always goes through ICU, so it is the reference for format.
function viaParts(format, value) {
    return format.formatToParts(value).map((part) => part.value).join("");
}

const values = [0, 1, 2, 9, 10, 11, 99, 100, 123, 405, 678, 998, 999, 1000, 1001, 1023, 1024, 9999, 10000,
    -0, -1, -999, 0.5, 1.5, 998.9996, 999.4, 999.9999, 0.0001, -0.0001, 2 ** 31, 2 ** 32, 2 ** 32 + 1, -(2 ** 31), 1e21, NaN, Infinity, -Infinity];

// One of each kind: ASCII digits, other digits by default or by request, and ASCII digits by request.
const locales = ["en", "tok", "en-IN", "de", "fa", "ar-EG", "my", "en-u-nu-hanidec", "ar-EG-u-nu-latn", "ja-u-nu-jpanyear"];

const optionsList = [
    undefined,
    { useGrouping: false },
    { useGrouping: "always" },
    { useGrouping: "min2" },
    { maximumFractionDigits: 0 },
    { minimumFractionDigits: 1 },
    { minimumFractionDigits: 2, trailingZeroDisplay: "stripIfInteger" },
    { minimumIntegerDigits: 2 },
    { minimumSignificantDigits: 2 },
    { maximumSignificantDigits: 1 },
    { maximumSignificantDigits: 2, maximumFractionDigits: 0, roundingPriority: "morePrecision" },
    { maximumSignificantDigits: 2, maximumFractionDigits: 0, roundingPriority: "lessPrecision" },
    { maximumFractionDigits: 0, roundingIncrement: 5 },
    { roundingMode: "ceil" },
    { roundingMode: "expand", maximumFractionDigits: 0 },
    { signDisplay: "always" },
    { signDisplay: "exceptZero" },
    { signDisplay: "negative" },
    { signDisplay: "never" },
    { notation: "compact" },
    { notation: "scientific" },
    { style: "percent" },
    { style: "currency", currency: "USD" },
    { style: "unit", unit: "liter" },
    { numberingSystem: "latn" },
    { numberingSystem: "hanidec" },
];

function check(locale, options, values, first = 1) {
    const format = new Intl.NumberFormat(locale, options);
    // The small integers formatted earlier decide how the later ones are formatted.
    format.format(first);
    for (const value of values) {
        const actual = format.format(value);
        const expected = viaParts(format, value);
        if (actual !== expected)
            throw new Error(`${locale} ${JSON.stringify(options)} ${first} then ${Object.is(value, -0) ? "-0" : value}: expected ${JSON.stringify(expected)} but got ${JSON.stringify(actual)}`);
    }
}

const fewValues = [0, -0, 5, 10, 123, 1000];

for (const locale of locales)
    check(locale, undefined, locale === "en" ? values : fewValues);
for (const options of optionsList)
    check("en", options, fewValues);
for (const useGrouping of [false, "always", "min2"])
    check("tok", { useGrouping }, [5, 10, 100]);

// Whichever integer comes first. tok has a grouping separator before the last two digits.
for (const locale of ["en", "tok"]) {
    for (const first of [1, 10, 100, 1000, -0])
        check(locale, undefined, [1, 100, 10, 999], first);
}

// Literal expectations. Each formatter is reused, since the first call differs from the later ones.
function checkLiterals(locale, options, pairs) {
    const format = new Intl.NumberFormat(locale, options);
    for (let i = 0; i < 4; ++i) {
        for (const [value, expected] of pairs)
            shouldBe(format.format(value), expected, `${locale} ${JSON.stringify(options)} ${String(value)}`);
    }
}
checkLiterals("en", undefined, [[999, "999"], ["999", "999"], [999n, "999"], [5n, "5"], [true, "1"], [null, "0"], ["-0", "-0"]]);
checkLiterals("ar-EG", undefined, [[12, "\u0661\u0662"], [12n, "\u0661\u0662"]]);
checkLiterals("en", { signDisplay: "always" }, [[5, "+5"], [0, "+0"]]);
checkLiterals("en", { signDisplay: "exceptZero" }, [[0, "0"], [5, "+5"]]);
checkLiterals("en", { minimumIntegerDigits: 2 }, [[12, "12"], [5, "05"]]);
checkLiterals("en", { style: "percent" }, [[0, "0%"], [5, "500%"]]);
checkLiterals("en", { minimumSignificantDigits: 2 }, [[123, "123"], [5, "5.0"]]);
checkLiterals("en", { maximumSignificantDigits: 1 }, [[5, "5"], [123, "100"]]);
checkLiterals("en", { maximumFractionDigits: 0, roundingIncrement: 5 }, [[5, "5"], [123, "125"]]);
checkLiterals("en", { notation: "compact" }, [[5, "5"], [999, "999"]]);
for (let i = 0; i < 4; ++i) {
    shouldBe((7).toLocaleString(), viaParts(new Intl.NumberFormat, 7), "toLocaleString 7");
    shouldBe((7).toLocaleString("en"), "7", "toLocaleString en 7");
    shouldBe((1234).toLocaleString("en"), "1,234", "toLocaleString en 1234");
    shouldBe((-0).toLocaleString("en"), "-0", "toLocaleString en -0");
    shouldBe((999n).toLocaleString("en"), "999", "BigInt toLocaleString en 999");
}
for (let i = 0; i < 4; ++i)
    shouldBe((12).toLocaleString("ar-EG"), "\u0661\u0662", "toLocaleString ar-EG 12");

{
    const signed = new Intl.NumberFormat("en");
    for (let i = 0; i < 4; ++i) {
        shouldBe(signed.format(0), "0", "warm 0");
        shouldBe(signed.format(-0), "-0", "warm -0");
        shouldBe(signed.format(999), "999", "warm 999");
        shouldBe(signed.format(1000), "1,000", "warm 1000");
    }
}

// The numbering system that resolvedOptions reports does not depend on whether format was called first.
for (const locale of ["en", "ar-EG", "ar-EG-u-nu-latn"]) {
    const fresh = new Intl.NumberFormat(locale);
    const used = new Intl.NumberFormat(locale);
    for (let i = 0; i < 3; ++i)
        used.format(1);
    shouldBe(used.resolvedOptions().numberingSystem, fresh.resolvedOptions().numberingSystem, `${locale} numberingSystem`);
}

// The cached strings survive, or are recreated after, a collection.
{
    const format = new Intl.NumberFormat("en");
    for (let round = 0; round < 2; ++round) {
        for (const value of [0, 9, 10, 99, 100, 999])
            shouldBe(format.format(value), viaParts(format, value), `round ${round} ${value}`);
        fullGC();
    }
}
