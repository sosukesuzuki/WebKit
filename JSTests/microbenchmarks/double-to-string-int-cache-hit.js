function test(num) {
    return ("" + num * 0.5).length;
}
noInline(test);

let acc = 0;
for (let i = 0; i < 5e6; ++i)
    acc += test(2000000 + ((i & 7) << 1));
if (acc !== 35000000)
    throw new Error("bad result: " + acc);
