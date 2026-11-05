# 03.03 PDFs, tables, images, and parsing quality

[返回全书目录 / Contents](../00-contents.md)

Complex parsing is about preserving structure, not maximizing extracted character count. Two-column PDFs need reading order, tables need headers and units, scans need OCR, and chart descriptions need page provenance. Compare hosted and local parsers on representative samples, including cost, privacy, latency, and layout fidelity.

A value such as sales 120 becomes misleading when its unit and reporting year disappear. Preserve headers, row keys, time, units, and footnotes. When useful, serialize rows with explicit column names. For financial calculations, compute from structured data deterministically and let the model explain the result.

Validate parsing against business tasks: clause completeness, table-cell alignment, reliable page locations, and image-only evidence. Multimodal retrieval differs from indexing generated image descriptions: the former needs compatible representations, while the latter can lose facts during captioning.

## Key points and difficulties

Key: layout, units, and provenance. Difficulty: cross-page tables and caption omissions are parsing losses that a larger top-k cannot repair.

## Interview question and answer

Q: Why is PDF RAG difficult? A: visual layout does not guarantee logical structure. Evaluate reading order, tables, OCR, and provenance explicitly.

## Production pitfalls and mitigation

Pitfall: treating generated table explanations as source facts. Distinguish original content, structured extraction, and derived descriptions, with provenance for each.

## Exercise and acceptance criteria

Select samples with columns, cross-page tables, and scanned pages; verify ten facts manually. Acceptance: source-page traceability, preserved units, and explicit handling for failures.
