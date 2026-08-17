# JSC JIT Memory Ledger

`index.html` is a bilingual (English / 日本語, toggle in the top bar) report: a deep dive into JavaScriptCore's
JIT tiers, inline caches, GC and object model, and 20 evidence-backed memory reductions for JIT code and metadata,
each with `file:line` citations and measurements taken on this tree (7375405d8e, JSCOnly Release, x86_64 Linux).

- `build_data.py` merges the primary outputs in `data/` into `data/data.json`; `gen_report.py` renders `index.html` from it.
- `data/` — raw measurement summaries (LinkBuffer stats per JetStream2 test/config, retained DFG/FTL counts,
  per-opcode JIT size statistics).
- `scripts/sizeof/` — `sizeof`/record-layout harness compiled against the JSC headers.
- `scripts/measure/` — jsc driver (`run.py` reads the JIT pool RSS from `/proc/<pid>/smaps` while the shell blocks
  on `readline()`), the JetStream2 in-process driver (`cli-mem.js`, copy into `PerformanceTests/JetStream2/`),
  the configuration matrix and the aggregation scripts.
- `measurement-instrumentation.patch` — the temporary, env-gated (`WKMEAS_DUMP_RETAINED=1`) finalizer probe used
  to count retained DFG/FTL structures; build with `-DENABLE_METADATA_STATISTICS=1` for the metadata statistics.
  Not applied to the tree.
