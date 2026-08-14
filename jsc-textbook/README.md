# JSC textbook chapters

Self-contained, textbook-style chapters about JavaScriptCore internals, written by
reading the source tree at a specific revision. Each chapter is a single HTML file
(inline CSS and SVG, no external resources) that can be opened directly in a browser.
Source references are given as `path:line` relative to `Source/JavaScriptCore/` and
are valid for the revision named in the chapter's colophon.

| Chapter | File | Revision |
|---|---|---|
| Inline caches (`PropertyInlineCache`): LLInt metadata caches, Handler ICs (Baseline/DFG), Repatching ICs (FTL), `MegamorphicCache`, invalidation, GC, and use as profiling input for the DFG/FTL. Japanese. | [`inline-cache.ja.html`](inline-cache.ja.html) | `f8225fcd97` |
