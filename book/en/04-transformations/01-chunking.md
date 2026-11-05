# 04.01 Sentence, semantic, and hierarchical chunking

[返回全书目录 / Contents](../00-contents.md)

Chunking trades retrieval precision against context completeness. Small chunks isolate facts but can lose subjects, conditions, and exceptions. Large chunks retain context but dilute similarity and increase generation input. chunk_size generally refers to tokenizer tokens rather than characters; Chinese, code, and tables have different ratios.

SentenceSplitter favors sentence and paragraph boundaries. Overlap reduces boundary loss but increases vector counts, duplicate candidates, and cost. Semantic splitting uses changes in text representations, adding embedding cost and sensitivity to thresholds, language, and style. For well-structured manuals, exploit headings before adding semantic complexity.

Compare chunk sizes, overlaps, and structural strategies on a fixed corpus and question set. Measure evidence coverage, context tokens, and answer quality. For cross-boundary evidence, try neighboring expansion or parent recovery rather than enlarging everything. Hierarchical parsing requires retaining parent nodes and relationships even when only leaves are indexed.

## Example and execution scope

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

```python
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
text = "Receipts are required. Exceptions need written approval. " * 80
parser = SentenceSplitter(chunk_size=256, chunk_overlap=32)
nodes = parser.get_nodes_from_documents([Document(text=text, id_="policy")])
print(len(nodes), {n.ref_doc_id for n in nodes})
```

## Key points and difficulties

Key: match chunks to evidence boundaries. Difficulty: retrieval and generation can use different granularities, and tokenizer counts must respect embedding truncation limits.

## Interview question and answer

Q: Is 512 the best chunk size? A: no universal optimum exists; choose using corpus structure, questions, models, and measured context budgets.

## Production pitfalls and mitigation

Pitfall: verbose metadata consumes chunk budget, leaving little content. Keep model-visible metadata concise and retain operational fields in storage and filters.

## Exercise and acceptance criteria

Compare three chunk sizes on a policy containing conditions, rules, and exceptions. Acceptance: find a boundary failure and explain when neighbor expansion is preferable.
