// Shared helpers for the realm reproducers (jsc shell; see ../README.md for Bun/Node).
// newRealm(name) makes another realm in the same VM via the shell's createGlobalObject() and
// registers it so realmOf() can name it; realm "A" is the realm running the script.
const realms = [["A", globalThis]];
function newRealm(name) { const g = createGlobalObject(); realms.push([name, g]); return g; }
const B = newRealm("B");
function realmOf(o) {                       // whose %Object.prototype% does o's prototype chain end at?
    let last = o;
    for (let p = o; p !== null; p = Object.getPrototypeOf(p)) last = p;
    for (const [name, g] of realms) if (last === g.Object.prototype) return name;
    return "?";
}
function realmOfThrown(f) { try { f(); } catch (e) { return realmOf(e); } return "no throw"; }
function check(label, actual, expected) {
    print((String(actual) === String(expected) ? "PASS " : "FAIL ") + label + ": got " + actual + ", expected " + expected);
}
