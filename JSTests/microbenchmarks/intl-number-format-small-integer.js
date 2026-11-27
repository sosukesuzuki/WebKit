const format = new Intl.NumberFormat("en-US");

function test(value)
{
    return format.format(value);
}
noInline(test);

let length = 0;
for (let i = 0; i < 1e5; ++i)
    length += test(i % 1000).length;

// 10 one-digit, 90 two-digit and 900 three-digit integers, 100 times each.
if (length !== (10 + 90 * 2 + 900 * 3) * 100)
    throw new Error("bad length: " + length);
