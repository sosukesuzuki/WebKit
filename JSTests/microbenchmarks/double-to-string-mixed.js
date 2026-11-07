function test(num) {
    return ("" + num * 0.5).length;
}
noInline(test);

let acc = 0;
for (let i = 0; i < 5e6; ++i)
    acc += test(i & 511);
if (acc !== 17851480)
    throw new Error("bad result: " + acc);
