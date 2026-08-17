function report(tag) {
  print("@@WAIT " + tag); readline();
  var f = MemoryFootprint();
  print("=== " + tag + " footprint current=" + f.current + " peak=" + f.peak);
  var m = memoryUsageStatistics();
  print("=== " + tag + " heapSize=" + m.heapSize + " heapCapacity=" + m.heapCapacity + " extraMemorySize=" + m.extraMemorySize + " objectCount=" + m.objectCount);
  var t = m.objectTypeCounts;
  var interesting = ["FunctionCodeBlock","ProgramCodeBlock","EvalCodeBlock","ModuleProgramCodeBlock","UnlinkedFunctionCodeBlock","UnlinkedProgramCodeBlock","FunctionExecutable","Structure","StructureRareData","FunctionRareData","JSFunction"];
  var s = [];
  for (var k of interesting) if (t[k] !== undefined) s.push(k + "=" + t[k]);
  print("=== " + tag + " counts " + s.join(" "));
}
function afterRun() {
  report("beforeGC");
  $vm.gc(); $vm.gc();
  print("=== linkBufferStats ===");
  print($vm.linkBufferStats());
  report("afterGC");
}
