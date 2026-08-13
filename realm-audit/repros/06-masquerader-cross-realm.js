load("realm-lib.js", "caller relative");
// [[IsHTMLDDA]] ("masquerades as undefined", i.e. document.all) is realm-scoped in JSC:
// Structure::masqueradesAsUndefined(lexicalGlobalObject) only answers true when the
// object's own realm == the realm of the code doing typeof / == / ToBoolean.  LLInt,
// Baseline, DFG and FTL all implement the same rule.  HTML/ECMA-262 (B.3.6) attach the
// behaviour to the object, not to the observer's realm.
const m = makeMasquerader();           // jsc shell stand-in for document.all
check("own realm: typeof", typeof m, "undefined");
const probe = B.eval("(m) => [typeof m, m == null, m == undefined, !m]");
const [t, eqNull, eqUndef, not] = probe(m);
check("other realm: typeof m", t, "undefined");
check("other realm: m == null", eqNull, true);
check("other realm: m == undefined", eqUndef, true);
check("other realm: !m", not, true);
const hot = B.eval("(m) => { let r; for (let i = 0; i < 1e6; ++i) r = [typeof m, m == null, !m]; return r; }");
check("other realm after JIT tier-up: [typeof, ==null, !m]", hot(m).join(), "undefined,true,true");
