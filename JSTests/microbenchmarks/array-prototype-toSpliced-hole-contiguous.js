const arr = [];
for (let i = 0; i < 1024; i++) {
    arr.push({ i });
}
delete arr[512];

function test(deleteCount) {
    arr.toSpliced(400, deleteCount, { i: 9999 }, { i: 8888 });
}
noInline(test);

for (let i = 0; i < 1e4; i++) {
    test(i % 100);
}
