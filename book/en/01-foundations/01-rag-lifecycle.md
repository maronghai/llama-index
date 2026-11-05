# 01.01 The RAG lifecycle and system boundaries

[返回全书目录 / Contents](../00-contents.md)

RAG extends the evidence available to a model beyond its parameters. The offline path loads, parses, chunks, embeds, and publishes data. The online path authenticates callers, retrieves and reranks evidence, assembles context, and generates answers. Evaluation spans both paths. LlamaIndex organizes these components; correctness, authorization, and answer quality remain application responsibilities.

For a travel-policy question, the system must establish the applicable region, employee group, and effective date before selecting evidence. Semantic similarity alone may return last year’s rules or another region’s policy. Separating similarity from applicability is the first production design decision.

Expose observable boundaries: source snapshots, normalized documents, nodes, index releases, retrieval results, and final answers. Record input versions and latency at each boundary. Diagnose failures by asking whether the source contained the answer, parsing preserved it, retrieval found it, and generation used it faithfully.

## Key points and difficulties

Key: separate offline construction from online queries. Difficulty: distinguish source coverage, retrieval quality, and generation faithfulness instead of hiding all failures behind one accuracy number.

## Interview question and answer

Q: RAG or fine-tuning? A: retrieval suits changing knowledge and cited answers; fine-tuning may improve stable behavior or output style. They can be combined. Fine-tuning does not replace live authorization or knowledge updates.

## Production pitfalls and mitigation

Pitfall: shipping chat before governing data makes every correction expensive. Assign stable IDs, versions, provenance, and access scopes from the beginning, and include unanswerable questions in the dataset.

## Exercise and acceptance criteria

Draw both paths of a policy assistant and specify inputs, outputs, and failures at six boundaries. Acceptance: clearly distinguish ingestion loss, retrieval misses, and unsupported generation.

## Implementation supplement: An offline document-to-evidence lifecycle

Dependencies: Python 3.10+; install `llama-index-core==0.14.25`.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM
from llama_index.core.node_parser import SentenceSplitter

docs = [Document(text="Travel lodging limit is 500 CNY per night.",
                 id_="travel-v2", metadata={"revision": "2"})]
nodes = SentenceSplitter(chunk_size=64, chunk_overlap=8).get_nodes_from_documents(docs)
index = VectorStoreIndex(nodes, embed_model=MockEmbedding(embed_dim=8))
hits = index.as_retriever(similarity_top_k=1).retrieve("What is the lodging limit?")
assert hits and hits[0].node.ref_doc_id == "travel-v2"
response = index.as_query_engine(llm=MockLLM(max_tokens=32)).query("Lodging limit?")
assert response.source_nodes
print({"documents": len(docs), "nodes": len(nodes), "sources": len(response.source_nodes)})
```

### Implementation, acceptance and production boundaries

Document IDs, node source references, retrieved evidence and response sources form an auditable chain. Assertions check connectivity only. Neither mock rankings nor mock answers establish quality; replace embeddings and evaluate against labeled evidence.

First-run note: core tokenization may download an encoding cache. Provision it and set `TIKTOKEN_CACHE_DIR` for offline use. No model key does not imply a network-free first run.
