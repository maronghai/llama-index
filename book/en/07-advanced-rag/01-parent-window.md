# 07.01 Parent recovery and sentence windows

[返回全书目录 / Contents](../00-contents.md)

Retrieval and generation need not use the same granularity. Sentence-window retrieval matches short text then expands neighboring sentences. Parent recovery retrieves leaves and restores a broader parent passage. Both retain conditions without embedding entire chapters.

Window text is often stored in metadata and substituted during postprocessing. Exclude the window field from embedding to preserve narrow retrieval. Hierarchical methods require persisted nodes and parent-child relations. Merge overlapping parents before budgeting context.

Expanded context must still satisfy authorization and version constraints. Visibility of one sentence does not authorize its whole parent document. Align chunk boundaries with access boundaries when documents contain mixed permissions.

## Key points and difficulties

Key: narrow matching with broader synthesis. Difficulty: deduplication, permissions, and token budgets after expansion.

## Interview question and answer

Q: Why not embed parents directly? A: large parents may dilute semantics; leaves locate evidence and parents supply context, subject to measured benefit.

## Production pitfalls and mitigation

Pitfall: leaf vectors survive but parent text is missing. Validate relationships at build time and test parent restoration.

## Exercise and acceptance criteria

Compare sentence-only, window, and parent retrieval on a rule followed by an exception. Acceptance: preserve the exception without duplicated context.
