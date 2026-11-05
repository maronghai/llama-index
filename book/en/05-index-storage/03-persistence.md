# 05.03 StorageContext, updates, and disaster recovery

[返回全书目录 / Contents](../00-contents.md)

StorageContext aggregates document, index, vector, and related storage. Default local storage can be persisted and loaded with load_index_from_storage. External backends may persist independently and are not necessarily captured by that directory. Backup inventories must map every state component to its actual system.

Updates need stable source IDs, revisions, and defined replacement scopes. Deletions must cover vectors, document stores, retrieval and answer caches, summaries, and derived graphs. API and cascade behavior vary by backend and need integration verification. Legal deletion cannot simply wait for a future rebuild.

Define recovery point and recovery time objectives: tolerable data loss and restoration duration. Rebuilding from immutable source snapshots complements database backups, but large rebuilds may exceed recovery targets. Blue-green index releases need a rollback target and must not expose incomplete builds.

## Example and execution scope

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

```python
from llama_index.core import Document, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.embeddings import MockEmbedding
embed = MockEmbedding(embed_dim=8)
index = VectorStoreIndex.from_documents([Document(text="Keep receipts.", id_="p")], embed_model=embed)
index.storage_context.persist(persist_dir="./storage_demo")
context = StorageContext.from_defaults(persist_dir="./storage_demo")
restored = load_index_from_storage(context, embed_model=embed)
assert restored.as_retriever(similarity_top_k=1).retrieve("receipts")
```

## Key points and difficulties

Key: complete recovery includes configuration and all stores. Difficulty: cross-component consistency and deletion propagation.

## Interview question and answer

Q: What else is needed after persist? A: model and chunking settings, dependencies, source snapshots, external backups, ACL versions, and release manifests.

## Production pitfalls and mitigation

Pitfall: declaring recovery successful because loading works while source text is missing. Verify representative queries, citations, and denied-access cases.

## Exercise and acceptance criteria

Run the example and discard in-memory objects. Acceptance: retrieval works after loading, with local persistence clearly distinguished from external database recovery.
