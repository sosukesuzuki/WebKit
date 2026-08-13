//@ requireOptions("--useDollarVM=1")
load("realm-lib.js", "caller relative");
// Structures remember their realm, and a few Structures are cached on cells that outlive or never
// belonged to that realm - so the cache pins the whole JSGlobalObject (an iframe's window and everything
// reachable from it) after the realm is otherwise dead:
//  (a) RegExp::ensureGroupsStructure (RegExp.cpp:228-255) caches the `groups` object Structure of the
//      last named-capture match on the JSC::RegExp cell, which is shared VM-wide by pattern+flags
//      (RegExpCache) and by every realm's RegExpObject / code block using that pattern.
//  (b) JSBoundFunction (JSBoundFunction.cpp:141-174) caches the bound-function Structure - realm of the
//      `bind` that ran - on the *target* function's FunctionRareData; InternalFunctionAllocationProfile
//      does the same for Reflect.construct(OtherRealm.Array, [], target).
function liveRealms() { fullGC(); fullGC(); return $vm.globalObjectCount(); }
const base = liveRealms();                                   // A and B from realm-lib

/(?<y>\d{4})-(?<m>\d{2})/.exec("2024-05");                   // main realm uses a named-group regexp...
(function () {
    let R = createGlobalObject();
    R.eval('/(?<y>\\d{4})-(?<m>\\d{2})/.exec("2024-05")');  // ...a short-lived realm uses the same pattern
    R = null;
})();
check("(a) realms alive after dropping R that ran the same named-group regexp", liveRealms(), base);
/(?<y>\d{4})-(?<m>\d{2})/.exec("2024-05");                   // re-matching here re-caches an A structure
check("(a) ...after realm A matches the pattern again", liveRealms(), base);

function target() {}
(function () {
    let R = createGlobalObject();
    R.Function.prototype.bind.call(target, null);            // "borrow clean intrinsics from a throwaway realm"
    R = null;
})();
check("(b) realms alive after dropping R whose bind() was applied to an A function", liveRealms(), base);
