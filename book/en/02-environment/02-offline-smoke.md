# 02.02 An offline pipeline smoke test

[返回全书目录 / Contents](../00-contents.md)

First prove that objects flow through the pipeline, then test semantic quality. MockEmbedding and MockLLM support a service-free smoke test. Mock vectors do not encode meaningful semantics, so their ranking cannot establish retrieval accuracy, and mock output cannot measure faithfulness.

The example indexes two policies with fixed-size mock embeddings, then retrieves and queries. Acceptance concerns object flow, nonempty output, source nodes, and provenance. Only after replacing mocks with real embeddings should you compare synonym retrieval such as hotel versus accommodation.

Distinguish deterministic assertions from generated wording. Model phrasing can change, so test business facts, citations, and abstention rather than matching a fluent paragraph byte for byte. Offline tests should also verify that billing or write operations are not invoked.

## Example and execution scope

Standalone offline smoke example requiring llama-index-core. Mock output does not establish semantic quality.

```python
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM

embed = MockEmbedding(embed_dim=8)
docs = [
    Document(text="Hotel claims require itemized receipts.", id_="hotel"),
    Document(text="Meal claims require manager approval.", id_="meal"),
]
index = VectorStoreIndex.from_documents(docs, embed_model=embed)
hits = index.as_retriever(similarity_top_k=2).retrieve("hotel receipts")
assert hits and all(h.node.ref_doc_id for h in hits)
response = index.as_query_engine(llm=MockLLM(max_tokens=32)).query("hotel receipts")
print(type(response).__name__)
print([h.node.ref_doc_id for h in hits])
```

## Key points and difficulties

Key: mocks validate plumbing only. Difficulty: avoid equating execution success with quality or letting weak tests hide retrieval defects.

## Interview question and answer

Q: How can development proceed without API credentials? A: use mocks for orchestration and fixed evidence for business logic. Evaluate semantics separately with real models.

## Production pitfalls and mitigation

Pitfall: mock vectors yield an apparently high recall score on a tiny corpus. Keep smoke and quality suites separate and never use mocks to rank models.

## Exercise and acceptance criteria

Run the example and print source IDs. Change the embedding dimension and build a fresh index. Acceptance: explain why this is not an embedding-quality experiment.
