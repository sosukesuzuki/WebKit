//@ $skipModes << :lockdown if $buildType == "debug"

function first(a, b) {
    return a;
}

function test(p, q, r, s, args) {
    let result = 0;
    for (let i = 0; i < 100; ++i) {
        result += args.length;
        result += first(...args) + p.x + q.x + r.x + s.x;
        result += first(...args) + p.x + q.x + r.x + s.x;
        result += first(...args) + p.x + q.x + r.x + s.x;
        result += first(...args) + p.x + q.x + r.x + s.x;
    }
    return result;
}
noInline(test);

// Adding a property fires the transition watchpoint of the structure of { x }, so the compiler has to
// rely on checks for it instead of watching it.
({ x: 1 }).extra = 1;

// Spread returns the storage of this copy-on-write array without allocating.
const args = [1, "a"];
const p = { x: 1 };
const q = { x: 2 };
const r = { x: 3 };
const s = { x: 4 };
for (let i = 0; i < 2e4; ++i) {
    if (test(p, q, r, s, args) !== 4600)
        throw new Error("bad result");
}
