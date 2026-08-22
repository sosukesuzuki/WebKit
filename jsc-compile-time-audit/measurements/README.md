# Measurements for the FTL/B3/Air compile-time audit

Everything here was produced on a 4-vCPU x86_64 VM (Ubuntu 24.04, clang 18.1.3)
from a JSCOnly release build (`Tools/Scripts/build-jsc --jsc-only --release`).

* `instrumentation.patch` — the counters (`addCompileStat`, reported next to
  `JSC_reportTotalPhaseTimes=1` totals) used to confirm or refute each finding.
  Apply on top of the commit before the fixes; the timings of that build are
  inflated by the counters and were not used.
* `scripts/run.sh <jsc> <label> <outdir> [js|wasm|pglite|all]` — runs the three
  workloads with `JSC_useConcurrentJIT=0 JSC_reportTotalPhaseTimes=1` and records
  rusage; `scripts/compare.py <outdir> <labelA> <labelB> <suite>` averages the
  per-phase totals over runs; `scripts/stress.sh` runs the 400-test sample in
  `stress-list.txt` in FTL-eager mode.
* `results/` — raw outputs. Labels: `baseline*` unmodified tree; `control*`,
  `ctrlB*`, `ctrlC*` baseline plus the two FTL timing scopes; `instr1` counters
  before the fixes; `fix1_*` after the mechanical fixes; `fix2_*`, `fix2C*`
  after the constant pool; `final*`, `final2_*`..`final7instr` the final tree
  (the `final3`..`final6` runs carry temporary sub-scopes around
  `freeUnneededB3ValuesAfterLowering`); `fix2instr1`, `fix3instr1`,
  `final7instr` counters after the fixes; `*-stress.txt` per-test exit codes.

Workloads: JetStream2 `cli.js` with the 28-test list in `run.sh` (1,283 FTL
compiles), `JSTests/wasm/stress/pglite.js` with lowered OMG thresholds (2,288 OMG
compiles), and JetStream2's five wasm tests (counters only).
