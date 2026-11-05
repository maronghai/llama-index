# 08.01 SummaryIndex and global questions

[返回全书目录 / Contents](../00-contents.md)

Global questions need broad coverage, unlike local fact lookup. SummaryIndex and summary trees can support coverage at higher processing cost than selective retrieval. Summaries compress detail and should not replace original clauses for precise amounts or exceptions.

Use summary paths for overviews and original nodes for details. Record source-node dependencies and summary versions. Updates and deletions invalidate derived summaries. Hierarchical summarization can accumulate omissions, requiring coverage checks and source review.

Evaluate coverage, consistency, and preservation of rare but critical risks, not just fluency. A short exclusion may matter more than repeated background. Frequency alone does not establish importance.

## Key points and difficulties

Key: distinguish broad coverage from precise facts. Difficulty: dependency invalidation and rare critical details.

## Interview question and answer

Q: Can summary indexes replace vector indexes? A: they support different query patterns; combinations need cost control and traceability.

## Production pitfalls and mitigation

Pitfall: summaries expose deleted policy content. Track dependencies and invalidate or rebuild derived data.

## Exercise and acceptance criteria

Summarize a document with rare major risks. Acceptance: preserve those risks and trace every conclusion to a passage.

## Implementation supplement: A full-evidence SummaryIndex baseline

Dependencies: Python 3.10+; install `llama-index-core==0.14.25`.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
from llama_index.core import Document, SummaryIndex
from llama_index.core.llms import MockLLM

index = SummaryIndex.from_documents([
    Document(text="Q1: launched a search prototype.", id_="q1"),
    Document(text="Q2: added access control and regression evaluation.", id_="q2"),
])
hits = index.as_retriever().retrieve("Summarize progress across quarters")
assert {h.node.ref_doc_id for h in hits} == {"q1", "q2"}
engine = index.as_query_engine(response_mode="tree_summarize", llm=MockLLM(max_tokens=16))
response = engine.query("Summarize progress across quarters")
assert len(response.source_nodes) == 2
print({"retrieved": len(hits), "sources": len(response.source_nodes)})
```

### Implementation, acceptance and production boundaries

Default SummaryIndex retrieval returns all nodes. This checks coverage, not summary accuracy. tree_summarize organizes hierarchical synthesis but cannot guarantee completeness or permission propagation. As the corpus grows, compare node counts, calls and input tokens against vector retrieval.

First-run note: core tokenization may download an encoding cache. Provision it and set `TIKTOKEN_CACHE_DIR` for offline use. No model key does not imply a network-free first run.

## Code Implementation Supplement:SummaryIndex Full Implementation for Global Synthesis Queries

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

Offline fixtures validate interfaces, provenance, and control flow, not semantic quality or security. Real-model branches additionally require `llama-index-llms-openai`, `llama-index-embeddings-openai`, and, for reranking, `llama-index-postprocessor-sbert-rerank`; set `RUN_REAL_MODELS=1`, `OPENAI_API_KEY`, `LLM_MODEL`, and `EMBED_MODEL` as required by the block. External-model branches have not been executed in this revision.

```python
from llama_index.core import Document, SummaryIndex
from llama_index.core.llms import MockLLM
from llama_index.core.response_synthesizers import ResponseMode

llm = MockLLM(max_tokens=64)
docs = [
    Document(text="Chapter 1: Vision is high-availability enterprise cloud AI.", id_="ch_1"),
    Document(text="Chapter 2: Security relies on zero trust and tenant isolation.", id_="ch_2"),
    Document(text="Chapter 3: Compliance mandates automated audit logging.", id_="ch_3")
]

# SummaryIndex 不依赖向量计算，保存完整文档节点序列
summary_index = SummaryIndex.from_documents(docs)
retriever = summary_index.as_retriever()
retrieved_nodes = retriever.retrieve("Provide an executive summary")
assert len(retrieved_nodes) == 3

query_engine = summary_index.as_query_engine(
    llm=llm,
    response_mode=ResponseMode.TREE_SUMMARIZE
)
resp = query_engine.query("Summarize all core principles across chapters")
assert resp.source_nodes and len(resp.source_nodes) == 3

print("SummaryIndex verified: scanned all 3 chapters without vector dropouts.")
```

### Architecture and execution boundaries

Operates without vector embeddings by preserving document sequence in SummaryIndex, pairing with tree summarization for full-corpus traversal; the mock tests orchestration only.
