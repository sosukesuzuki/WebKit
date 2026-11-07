function test(num) {
    return ("" + num * 0.5).length;
}
noInline(test);

let acc = 0;
for (let i = 0; i < 1e6; ++i)
    acc += test(i & 511);
if (acc !== 3570256)
    throw new Error("bad result: " + acc);
