//@ requireOptions("--useConcurrentJIT=0")
load("tier-lib.js", "caller relative");
// String.prototype.{match,search,split} and RegExp.prototype[@@split] from realm C, called
// directly from realm A (e.g. a parent frame that borrowed String methods from a child frame).
// DFG inlines StringPrototype{Match,Search,Split}Intrinsic after consulting only the *caller's*
// stringSymbol{Match,Search,Split}WatchpointSet / regExpPrimordialPropertiesWatchpointSet
// (DFGByteCodeParser.cpp ~3399-3468) and lowers to operationStringMatch/Search/Split(lexical A).
// So a monkey-patch installed in the callee's realm is honoured by LLInt/Baseline and silently
// ignored by DFG/FTL, and every allocation / legacy RegExp static goes to the wrong realm.
const C = newRealm("C");
String.prototype.cmatch = C.String.prototype.match;
String.prototype.csearch = C.String.prototype.search;
String.prototype.csplit = C.String.prototype.split;
RegExp.prototype.csplit = C.RegExp.prototype[Symbol.split];
C.eval(`RegExp.prototype[Symbol.match]  = function () { return "patched @@match"; };
        RegExp.prototype[Symbol.search] = function () { return 42; };`);
tierCheck("'abc'.cmatch('b') sees C's RegExp.prototype[@@match] override", (s) => s.cmatch("b"), "abc", "patched @@match");
tierCheck("'abc'.csearch('b') sees C's RegExp.prototype[@@search] override", (s) => s.csearch("b"), "abc", 42);
tierCheck("realm of 'a,b'.csplit(',')", (s) => realmOf(s.csplit(",")), "a,b", "C");
tierCheck("realm of /,/.csplit('a,b') (RegExp.prototype[@@split] lacks GetGlobalObject(callee))", (s) => realmOf(/,/.csplit(s)), "a,b", "C");
