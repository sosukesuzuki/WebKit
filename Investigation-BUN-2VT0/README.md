# BUN-2VT0 — garbage StructureIDs in op_call ArrayProfiles at GC end

Hands-on investigation of Sentry BUN-2VT0 (Windows, `CodeBlock::updateAllArrayProfilePredictions` →
`ArrayProfile::computeUpdatedPrediction` → `Structure::typeInfo` faults on `structureIDBase + <garbage>`)
and its macOS/Linux siblings BUN-3JDB / BUN-3K59 / BUN-2V2R / BUN-3KRT (ValueProfile readers on JIT threads).

Everything below was done against oven-sh/WebKit `b7f217b4` (bun HEAD pin) built from source with
`ENABLE_ASSERTS=ON`, plus a bun `release-local --assertions=on` build linked against it, on Linux x64.
The instrumentation patch, the proposed fix, and the scripts used are in this directory.

## Bottom line

1. **Cross-OS bytecode (#18416) is real but is not what the Sentry population is hitting.**
   The metadata layout mismatch is `OpCall::Metadata` = 96 bytes on Linux/mac (CallLinkInfo 80) vs
   112 on Windows (CallLinkInfo 96 under the MSVC bit-field ABI). I downloaded the actual Claude Code
   Windows binaries from npm (`@anthropic-ai/claude-code-win32-x64` 2.1.150 = bun 1.3.14+521eedd6d, the
   single biggest contributor with 108 events, and 2.1.240 = bun 1.4.0+fdb5e06cc) and decoded every
   `CachedMetadataTable` in their embedded bytecode: the op_call regions are exact multiples of **112**
   (Windows layout), the Linux binary's are multiples of **96**. CC ships Windows-native bytecode, so
   Robobun's "it runs, so it is layout-compatible" inference is confirmed by direct inspection.

2. **The Windows garbage splits into two classes**, and one of them has a concrete, demonstrated producer:
   - **Class A (~32 % of events): well-formed but dead StructureIDs.** `ArrayProfile::m_lastSeenStructureID`
     is untraced and is only folded/cleared by the GC-end reconcile pass, which runs **only for CodeBlocks
     visited in that collection**. An old CodeBlock that an eden collection does not re-visit keeps its
     samples across the cycle while the (young) Structures they name die. Structure blocks are `mi_free`'d
     into the mimalloc structure arena and purged; on Windows mimalloc purges with `MEM_DECOMMIT`, so the
     next full-GC reconcile decodes the stale ID and faults in `Structure::typeInfo`. On mac/Linux the same
     read returns `MADV_DONTNEED`/`MADV_FREE` zeros and is silent. I confirmed the window with a probe
     (old CodeBlock not reconciled in eden GCs; unmarked Structures decoded at the next full GC) and wrote
     a fix that decides liveness from the MarkedBlock set + mark bits without touching Structure memory
     (`bun-webkit-fix-gc-end-dead-array-profile-samples.patch`). This is not a "tryDecode guard": it is the
     liveness check the design assumed and never had; dropped samples are logged under `verboseOSR`.
   - **Class B (~45 %): ArrayModes/flag/u16/pointer-half shaped values in the StructureID slot.** These
     are not StructureIDs at all. The only writers of that slot copy `JSCell::m_structureID` of the call's
     `this` (LLInt `arrayProfileForCall`, baseline `compileSetupFrame`), so the `this` cell's first four
     bytes were metadata-shaped — i.e. the `this` pointer referred to memory that is not (or no longer) a
     live cell. That is a JS-object use-after-free / heap-corruption producer upstream of the profile, not
     a metadata-layout bug, and I could not reproduce it on Linux x64 (see "What did not reproduce").

3. **The macOS/Linux ValueProfile family is profile-only garbage, not bad JS values.** Searching Sentry for
   the fault address `0x100000012` shows it appears *only* in profile readers
   (`ValueProfileBase<1,0>`/`<1,1>::computeUpdatedPrediction`, `speculationFromCell`, one GC-end
   `finalizeUnconditionally`); no ordinary JS operation ever dereferences the value. The bucket content is a
   per-platform near-constant (`0x1_0000000D` on mac arm64 across 1.3.6→1.4.0 official builds, 2–6 TiB
   upper halves only on CC's `1.4.0+f6d0fcd24`, `0xFFFF_0000000D` on Linux arm64, single bits / `0x4_00000000`
   on mac x64). That shape — a 32-bit payload in the low half with a stale upper half — is what a raw
   register/slot value captured by a profiling store looks like, not a metadata-layout shift (every
   layout-shift hypothesis I checked is consistent between writers and readers). This family needs
   write-side instrumentation on an arm64 mac canary; details and the exact candidates are below.

## What was built and run

- oven-sh/WebKit `b7f217b4` JSCOnly, RelWithDebInfo, `ENABLE_ASSERTS=ON`, `USE_BUN_JSC_ADDITIONS`,
  `USE_BUN_EVENT_LOOP`, FTL on (clang 18, `/home/user/wkbuild/bin/jsc`).
- Loud checks (`bun-webkit-instrumentation.patch`):
  - `CodeBlock::updateAllArrayProfilePredictions` (GC end): every sampled StructureID must `tryDecode`, be
    atom-aligned, and its header StructureID must equal `vm.structureStructure`'s; otherwise dump the
    opcode, entry index, entry bytes, 64 preceding bytes, and `CRASH_WITH_INFO`.
  - `ArrayProfile::computeUpdatedPrediction(CodeBlock*)` (covers DFG-thread `getArrayMode` reads): same check.
  - `speculationFromCell` (ValueProfile/ArgumentValueProfile readers, all threads): cell must be 8-byte aligned
    and its header StructureID must `tryDecode` to an atom-aligned Structure; otherwise crash with the value.
- bun HEAD (`85deae03`, 1.4.1-canary) `release-local --assertions=on` linked against that WebKit
  (`build/release-local/bun-assertions`). Note: the JSC `ENABLE_ASSERTS=ON` build defines
  `ASSERT_ENABLED=1` as a compiler flag, not in `cmakeconfig.h`; a bun built without `--assertions=on`
  against it is an ODR mismatch and crashes at startup.
- Workloads (all clean on Linux x64, zero hits):
  - jsc shell: TypeScript compiler on its own source (×8), multi-realm polymorphic call/iterator/for-in
    stress, async/generator/Proxy/bound-call stress, DFG tail-call→LLInt argument profiling, argument
    `BadType` exits; each under bun's option set, `collectContinuously`, eager/forced old-age jettison,
    `useConcurrentJIT=0`, `deleteAllCodeWhenIdle`, `sweepSynchronously`+`scribbleFreeCells`.
  - ~7.5k JSTests/stress executions (call/iterator/enumerator/profile/osr/tail/arguments/spread filters,
    4 configs each). Only failures: fork-specific error-message wording.
  - The real Claude Code 2.1.240 bundle (extracted from the Linux standalone) under the instrumented bun:
    45 full agent sessions of ~40 tool turns each driven by a mock Anthropic Messages API
    (`scripts/mockapi.py`, `scripts/cc-mock-loop.sh`) cycling 7 GC/JIT stress option sets, plus 32
    `--help/doctor/-p` runs.
  - 25,386 bun tests (`test/js/{bun,node,web,third_party}` subsets) with the instrumented bun.

## Findings with references

### Layout facts (fork, Linux x64 / MSVC ABI)
- `OpCall::Metadata` = 96/112 bytes, align 8; `DataOnlyCallLinkInfo` = 80/96; `ArrayProfile` at +80/+96
  (`bytecode/BytecodeList.rb:465`, generated `BytecodeStructs.h`). `ArrayProfile` =
  `{lastSeenStructureID u32, speculationFailureStructureID u32, flags u32, observedArrayModes u32}`
  (`bytecode/ArrayProfile.h:273-276`). `ValueProfile` = `{EncodedJSValue bucket; SpeculatedType prediction}`
  = 16 bytes; `ArgumentValueProfile` = 24. MetadataTable buffer =
  `[ValueProfiles...][LinkingData 16][offset table][entries]` (`bytecode/MetadataTable.h:39-42`).
- The fork's only structural CallLinkInfo change is `uint32_t m_slowPathCount` (`bytecode/CallLinkInfo.h:309`),
  which fits in padding on Itanium (offset 20) and sits at 36 on MSVC without changing sizes.
- Cache key is `SuperFastHash(BUN_WEBKIT_VERSION)` only (`src/jsc/bindings/ZigGlobalObject.cpp:264`), and
  `CachedMetadataTable` stores the encoder binary's absolute offsets (`runtime/CachedTypes.cpp:1522-1559`).
  `bun build --compile --target=bun-windows-x64 --bytecode` on a mac/Linux host embeds host-layout bytecode
  with no target check (`src/runtime/cli/Arguments.rs:2060`). Worth fixing independently (mix OS/ABI into
  the version, or reject), but CC's shipped binaries are Windows-built so this is not their producer.

### Class A mechanism (file:line)
- GC-end reconcile only iterates CodeBlocks in `CodeBlockSpaceAndSet::set`
  (`heap/Heap.cpp:773-806`, `reconcileWeakReferencesInMarkedCells<CodeBlock>(space.set, ...)`).
- A CodeBlock is added to that set in `CodeBlock::visitChildren` (`bytecode/CodeBlock.cpp:1240`) and removed
  at the end of `CodeBlock::reconcileWeakReferencesAtGCEnd` (`bytecode/CodeBlock.cpp:1905`). Old CodeBlocks
  that an eden collection does not re-visit are therefore not reconciled in that cycle.
- `updateAllPredictions` is documented as "samples are untraced JSValues and StructureIDs, so this only runs
  while they are still readable: after marking, before sweep" (`bytecode/CodeBlock.cpp:3169-3172`). That
  precondition is false for a sample recorded before an eden GC that the CodeBlock skipped.
- `ArrayProfile::computeUpdatedPrediction` decodes unconditionally (`bytecode/ArrayProfile.cpp:128-132`).
- Structure blocks come from a dedicated, exclusive mimalloc arena inside the 4 GB structure reservation and
  are released with `mi_free` (`heap/StructureAlignedMemoryAllocator.cpp:144-147, 211-214`); the fork purges
  after every full GC (`heap/Heap.cpp:2657-2661`, `bmalloc::api::scavengeThisThread`) and mimalloc's own
  `purge_delay` purges freed pages anyway. On Windows that is `MEM_DECOMMIT`, so a decode of a dead ID faults at
  `Structure::typeInfo` (`runtime/TypeInfoBlob.h:56`, the `structure+9` byte Robobun measured); on mac/Linux it
  reads zeros.
- Evidence from Sentry: every Windows fault address is `structureIDBase + id + 9` with 4 GB-aligned bases
  (0x1xx–0x2xx ·4 GB, i.e. the structure reservation); 32 of 100 sampled ids are 16-aligned offsets well inside
  the arena (e.g. `0xC46FD960`, `0x46072E0`), exactly what a dead Structure's former address looks like.
- Probe run (jsc shell, `scripts/stale-id3.js`, `--useJIT=0 --sweepSynchronously=1 --scribbleFreeCells=1`,
  `BUN_PROBE=1`): `forEach`'s CodeBlock was never reconciled in eden collections, and at the following full GCs
  it decoded ids whose Structures were unmarked (dead) 30 times. With the fix applied, those 30 samples are
  dropped ("Dropping dead ArrayProfile sample ...") and all workloads still pass.

### Class B and the mac/Linux ValueProfile family
- 100 Windows events classified (`scripts/` notes): 45 ArrayModes-shaped bit sets (e.g. `0x1FA`, `0x378`,
  `0x88`, `1<<26`, `1<<30`), 32 structure-offset-like, 4 zero/nuked, 5 negative-int-like, 14 other
  (u16 pairs like `0x640064`, flag-like `0x4`).
- The slot's only writers copy the `this` cell header: `llint/LowLevelInterpreter64.asm:2463-2470`
  (`arrayProfileForCall`), `jit/JITCall.cpp:121-130`; DFG OSR exits write only `m_speculationFailureStructureID`
  and OR `m_observedArrayModes` (`dfg/DFGOSRExit.cpp:316-370`), via absolute addresses into the baseline
  CodeBlock that the DFG block keeps alive (`bytecode/CodeBlock.cpp:1993-2011`). So class B means `this`
  pointed at non-cell memory (dangling object into fastMalloc'd/reused memory) at the time of the call, or the
  cell header was corrupted — a use-after-free/heap-corruption family that the profile is merely the first
  reader of. It could not be reproduced here.
- Mac/Linux: `0x100000012` (and the 2–6 TiB variants) never appears outside profile readers. Values are
  `{lo = 13 | 0, hi = 1 | 0xFFFF | mimalloc-range | 4}` by platform/arch. A `{int32, stale upper half}` word
  is what a 32-bit store into an 8-byte slot leaves behind, or a raw register captured by a profiling store;
  it is not a `SpeculatedType` (bit 3 is unused in every relevant WebKit revision) and not a decoded
  StructureID. Everything that writes ValueProfile buckets (`llint/LowLevelInterpreter64.asm:77-81`,
  `jit/JITInlines.h:312-319`, `llint/LLIntSlowPaths.cpp:168-170`, `bytecode/MethodOfGettingAValueProfile.cpp`,
  `jit/JIT.cpp:801` for arguments) stores a 64-bit JSValue register; the candidates for the register
  itself being `{int32, stale}` are the DFG `checkArgumentTypes` `JSValueSource(addressFor(arg))` path
  (`dfg/DFGSpeculativeJIT.cpp:2264`), the tail-call `CallFrameShuffler` (`jit/CallFrameShuffler64.cpp:37-48`
  stores unboxed int32 with `store32` into spill slots), and DFG `PutStack` of `FlushedInt32` arguments —
  all upstream-identical and all exercised without a hit here. Being arm64-heavy, this needs a canary on
  macOS arm64 with write-side checks (below).

### Ruled out (with how)
- Cross-OS bytecode for the CC population: decoded the shipped bytecode (above).
- Metadata layout/offset disagreements: LLInt `metadata()` macro vs `MetadataTable::get` round identically;
  `LinkingData`/`ValueProfile` sizes agree across LLInt, baseline, DFG; `ASSERT_ENABLED`/`USE_MIMALLOC`
  consistent between bun TUs and the prebuilt library in production profiles.
- MetadataTable lifetime: `link()/unlink()` buffer reuse, `~MetadataTable` running entry destructors,
  `CallLinkInfoBase` intrusive-list removal, `PolymorphicCallNode` `m_cleared` guard, DFG plan cancellation at
  safepoints, `visitOSRExitTargets` keeping alternatives and inlined baseline blocks alive — all consistent.
- Yarr SIMD using xmm6–xmm12 on x86-64 (callee-saved on Win64): JIT'd regex entry points are `SYSV_ABI`
  (`yarr/YarrJIT.h:286-289`), so callers save them; not a bug.
- bun stack walkers (`ErrorStackTrace.cpp`, `CallSite`): never read `this`/argument slots of arbitrary frames.
- Rust `JSValue` encoders (`src/jsc/JSValue.rs:460-463`) and host-fn result wrappers (`src/jsc/host_fn.rs`).
- Old-age jettison of `m_alternative` baseline blocks: `visitChildren` always visits all children
  (`bytecode/CodeBlock.cpp:1219-1241`); only the executable→CodeBlock edge is conditional.

## Repro / how to use the artifacts

    git clone https://github.com/oven-sh/WebKit vendor/WebKit && (cd vendor/WebKit && git checkout b7f217b4)
    cd vendor/WebKit && git apply .../bun-webkit-instrumentation.patch      # loud checks
    cmake -G Ninja -DPORT=JSCOnly -DENABLE_STATIC_JSC=ON -DENABLE_BUN_SKIP_FAILING_ASSERTIONS=ON \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo -DENABLE_ASSERTS=ON -DUSE_BUN_JSC_ADDITIONS=ON -DUSE_BUN_EVENT_LOOP=ON \
      -DENABLE_FTL_JIT=ON -DENABLE_REMOTE_INSPECTOR=ON -B build . && ninja -C build jsc
    BUN_PROBE=1 build/bin/jsc --useDollarVM=1 --useJIT=0 --sweepSynchronously=1 --scribbleFreeCells=1 \
      scripts/stale-id3.js | grep PROBE | grep forEach      # dead (unmarked) samples decoded at full GC
    # bun: add ENABLE_ASSERTS: "ON" to scripts/build/deps/webkit.ts, then
    bun scripts/build.ts --profile=release-local --assertions=on --build-dir=build/release-local
    # CC workload: extract cli.js from a claude standalone (scripts/parsegraph.py), run scripts/mockapi.py,
    # then scripts/cc-mock-loop.sh
    # Check a shipped CC binary's bytecode layout:
    scripts/checkcc2.sh win32-x64 2.1.240 50 /tmp/ops-<webkit-sha>.txt   (ops file from scripts/genops.sh)

## Proposed fix and next steps

1. Apply `bun-webkit-fix-gc-end-dead-array-profile-samples.patch` to oven-sh/WebKit
   (`ArrayProfile::computeUpdatedPrediction(CodeBlock*)`): at GC end, validate each sampled StructureID via
   `MarkedSpace::blocks().set()` membership, subspace check, and `MarkedBlock::isMarked(markingVersion)` before
   decoding; drop dead samples and log them under `verboseOSR`. Compiler-thread callers are unchanged (they
   only see samples written since the last reconcile). This removes the Windows fault for class A and makes
   the condition observable instead of silent on mac/Linux. An alternative with the same effect is to
   reconcile every live CodeBlock in eden collections, but that costs a full CodeBlock-space walk per eden GC.
2. For class B / the mac family, ship a canary with write-side checks so the producer is caught with a JS stack:
   in `arrayProfileForCall` (LLInt) and `JIT::compileSetupFrame`, validate `this`'s header StructureID before
   storing it; in the LLInt `valueProfile` macro and `JIT::emitValueProfilingSite`, branch to a slow path when
   the value is cell-tagged but not 8-byte aligned or its header does not `tryDecode`. This is a handful of
   instructions on a profiling store and only needs to run on a canary. Prioritise macOS arm64 for the
   ValueProfile family and Windows x64 for class B; the `this` check will also surface the UAF family that
   BUN-2VT0 class B is a symptom of.
3. Independently fix #18416: mix the target OS/ABI into `getWebKitBytecodeCacheVersion` (or the standalone
   graph's cache validation) and reject `--bytecode` for cross-OS `--compile` targets.
