// Runs the TypeScript compiler (big, call-heavy, polymorphic) inside the jsc shell repeatedly.
// typescript.js is a CJS/UMD bundle; provide a minimal `module`/`require` shim.
var module = { exports: {} };
var exports = module.exports;
var require = function(name) { throw new Error("require " + name); };
var process = undefined;
var __filename = "/typescript.js", __dirname = "/";
var globalThis_ = globalThis;
load("/home/user/work/node_modules/typescript/lib/typescript.js");
var ts = module.exports;
var src = readFile("/home/user/work/node_modules/typescript/lib/typescript.js");
var smallSrc = src.slice(0, 400000);
var iterations = parseInt(arguments[0] || "3", 10);
for (var i = 0; i < iterations; ++i) {
    var out = ts.transpileModule(smallSrc, { compilerOptions: { target: ts.ScriptTarget.ES5, module: ts.ModuleKind.CommonJS } });
    var sf = ts.createSourceFile("x.ts", smallSrc, ts.ScriptTarget.Latest, true);
    var count = 0;
    function walk(n) { count++; ts.forEachChild(n, walk); }
    walk(sf);
    print("iter", i, "out", out.outputText.length, "nodes", count);
    if (typeof fullGC === "function") fullGC();
}
print("done");
