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

## Implementation supplement: A quality gate for parsed records

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
from dataclasses import dataclass

@dataclass
class ParsedPage:
    source: str
    page: int
    text: str
    table_rows: list[list[str]]

def validate(page):
    errors = []
    if not page.source or page.page < 1:
        errors.append("missing provenance")
    if len(page.text.strip()) < 20:
        errors.append("sparse text: OCR review required")
    if "\ufffd" in page.text:
        errors.append("replacement character")
    widths = {len(row) for row in page.table_rows}
    if len(widths) > 1:
        errors.append("ragged table")
    return errors

good = ParsedPage("policy.pdf", 1, "Hotel allowance: CNY 500 per night.",
                  [["city", "limit"], ["Shanghai", "500"]])
bad = ParsedPage("scan.pdf", 2, "\ufffd", [["city", "limit"], ["500"]])
assert validate(good) == []
assert len(validate(bad)) == 3
print(validate(bad))
```

### Implementation, acceptance and production boundaries

Inputs are structured records already returned by a parser; this code does not parse PDFs or run OCR. Sparse text, replacement characters and ragged tables go to review. Length checks cannot establish table semantics; sample headers, units, signs and footnotes.
