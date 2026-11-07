function test(num) {
    return ("" + num * 0.5).length;
}
noInline(test);

let acc = 0;
for (let i = 0; i < 5e6; ++i)
    acc += test((i & 511) << 1);
if (acc !== 13925740)
    throw new Error("bad result: " + acc);
