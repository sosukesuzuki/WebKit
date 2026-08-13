load("realm-lib.js", "caller relative");
// String.prototype.{match,matchAll,search,split,replace} + a RegExp from realm B.
// Spec: these methods just Invoke(regexp, @@match/@@split/...), i.e. realm B's
// RegExp.prototype[@@match] runs, so every object it allocates (the matches
// array, the RegExpStringIterator, the species-cloned RegExp) is a realm-B
// object, and the legacy RegExp statics (RegExp.lastMatch, $1, ...) of realm B
// are the ones that get updated.
// JSC: isSymbolMatchFastAndNonObservable() is evaluated against the RegExp's own
// realm (B) but the fast path then runs regExpMatchFast(globalObject = A, ...).
const re = new B.RegExp("a(b)?");
check("realm of 'ab'.match(reB)", realmOf("ab".match(re)), "B");
check("realm of 'abab'.matchAll(/a/g from B)", realmOf("abab".matchAll(new B.RegExp("a", "g"))), "B");
check("realm of 'a,b'.split(/,/ from B)", realmOf("a,b".split(new B.RegExp(","))), "B");
"xaby".replace(new B.RegExp("a(b)"), "-");
check("B.RegExp.$1 after 'xaby'.replace(/a(b)/ from B)", B.RegExp.$1, "b");
check("A.RegExp.$1 is untouched", RegExp.$1 === "b" ? "clobbered" : "untouched", "untouched");

// The behaviour is not even self-consistent: fire an unrelated watchpoint in B
// (re-install the very same exec function) and the same calls flip realm.
B.eval("const e = RegExp.prototype.exec; delete RegExp.prototype.exec; RegExp.prototype.exec = e;");
check("after no-op reshuffle in B: realm of 'ab'.match(reB)", realmOf("ab".match(re)), "B");
check("after no-op reshuffle in B: realm of split result", realmOf("a,b".split(new B.RegExp(","))), "B");
