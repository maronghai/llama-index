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

## Code Implementation Supplement:Multi-Granularity Chunking Strategy Comparison and Source Traceability

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

Offline fixtures validate interfaces, provenance, and control flow, not semantic quality or security. Real-model branches additionally require `llama-index-llms-openai`, `llama-index-embeddings-openai`, and, for reranking, `llama-index-postprocessor-sbert-rerank`; set `RUN_REAL_MODELS=1`, `OPENAI_API_KEY`, `LLM_MODEL`, and `EMBED_MODEL` as required by the block. External-model branches have not been executed in this revision.

```python
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter

doc = Document(
    text=(
        "Section 1: Annual Leave entitlement is 15 business days.\n\n"
        "Section 2: Sick Leave requires hospital certificate after 2 consecutive days.\n\n"
        "Section 3: Compassionate Leave allows 3 to 5 days with manager approval."
    ),
    id_="policy_doc_2025"
)

# 1. 紧凑小块策略：专注于局部独立事实
small_splitter = SentenceSplitter(chunk_size=40, chunk_overlap=8)
small_nodes = small_splitter.get_nodes_from_documents([doc])

# 2. 宏观大块策略：专注于完整保留条款上下文
large_splitter = SentenceSplitter(chunk_size=120, chunk_overlap=20)
large_nodes = large_splitter.get_nodes_from_documents([doc])

assert len(small_nodes) >= len(large_nodes)
for node in small_nodes + large_nodes:
    assert node.ref_doc_id == "policy_doc_2025"

print("Chunking comparison complete:")
print(f"- Small chunk nodes count: {len(small_nodes)}")
print(f"- Large chunk nodes count: {len(large_nodes)}")
print(f"- All {len(small_nodes) + len(large_nodes)} nodes preserve parent doc traceability.")
```

### Architecture and execution boundaries

Compares fine-grained sentence chunking with coarse long-context chunking, asserting that all resulting child nodes preserve parent document IDs and ordering relations.
