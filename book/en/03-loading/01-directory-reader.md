# 03.01 Using SimpleDirectoryReader

[返回全书目录 / Contents](../00-contents.md)

SimpleDirectoryReader supports directory ingestion, explicit file lists, recursion, and extension filters. Format support depends on installed readers; it is not universal OCR. A successfully loaded PDF does not prove tables, scanned text, or reading order were preserved.

Define ingestion boundaries first: approved directories and extensions, with temporary files, secrets, duplicate copies, and caches excluded. Metadata hooks can supply business identifiers, but filenames are not automatically unique. Relative paths change when folders move; prefer business keys when available.

Record file count, document count, character count, failures, and parser versions. Route blank output to an exception queue. Garbled text requires investigating encoding, font mappings, or parsing rather than simply deleting characters. Silent skips turn ingestion failures into misleading knowledge gaps.

## Example and execution scope

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

```python
# Requires an existing approved input directory.
from llama_index.core import SimpleDirectoryReader
reader = SimpleDirectoryReader(
    input_dir="./approved_data",
    recursive=True,
    required_exts=[".txt", ".md"],
    filename_as_id=True,
)
documents = reader.load_data()
for doc in documents:
    if not doc.text.strip():
        raise ValueError(f"Blank source: {doc.id_}")
print("documents:", len(documents))
```

## Key points and difficulties

Key: bound inputs and validate parsing. Difficulty: one file may create multiple Documents, so file counts and document counts are not interchangeable.

## Interview question and answer

Q: Why does QA fail after loading succeeds? A: text may be blank, tables scrambled, headers dominant, or relevant content omitted. Inspect parsed text before tuning generation.

## Production pitfalls and mitigation

Pitfall: recursively ingesting a project captures secrets and obsolete copies. Use allowlists, manifests, deduplication, and permission checks.

## Exercise and acceptance criteria

Prepare UTF-8 text, Markdown, an empty file, and duplicate filenames in different folders. Acceptance: unique provenance, blank-file alerts, and explicit failures.
