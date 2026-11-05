# 05.02 Chroma integration and collection contracts

[返回全书目录 / Contents](../00-contents.md)

Chroma is useful for local experiments and some deployments, but persistence alone does not deliver high availability, backups, or tenant isolation. Compare stores on filtering, deletion, batches, text storage, concurrency, and recovery as well as vector-search latency.

The integration requires chromadb and llama-index-vector-stores-chroma. Bind each collection to embedding dimensions, model revision, metric, and metadata schema. Different models need separate collections or rebuilding even when dimensions match. The snippet uses MockEmbedding only to demonstrate StorageContext wiring.

Restoring through from_vector_store depends on the backend retaining text and required metadata. Recovery is not identical across stores. During migration, verify deletions, filters, and citation fields rather than only counting vectors.

## Example and execution scope

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

```python
# Requires chromadb and llama-index-vector-stores-chroma.
import chromadb
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
client = chromadb.PersistentClient(path="./chroma_demo")
collection = client.get_or_create_collection("smoke_v1")
store = ChromaVectorStore(chroma_collection=collection)
context = StorageContext.from_defaults(vector_store=store)
index = VectorStoreIndex.from_documents(
    [Document(text="Receipts are required.", id_="policy")],
    storage_context=context, embed_model=MockEmbedding(embed_dim=8),
)
print(len(index.as_retriever(similarity_top_k=1).retrieve("receipts")))
```

## Key points and difficulties

Key: collections are versioned data contracts. Difficulty: adapter semantics can differ from native database behavior.

## Interview question and answer

Q: Why retain model revision as well as dimensions? A: dimensions constrain shape, while model revision defines semantic coordinates; mismatch can silently degrade retrieval.

## Production pitfalls and mitigation

Pitfall: reusing a collection after changing the model. Include index versions in collection naming and validate the manifest before loading.

## Exercise and acceptance criteria

Restore the example collection in a fresh process and record adapter versions. Acceptance: text and provenance survive and embedding identity matches.
