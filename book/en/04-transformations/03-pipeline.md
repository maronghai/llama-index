# 04.03 IngestionPipeline, caching, and idempotency

[返回全书目录 / Contents](../00-contents.md)

IngestionPipeline applies transformations in order, combining chunking, extraction, and embedding. Nodes written to a vector store need suitable embeddings. A pipeline producing only nodes can defer embedding to index construction. Transformation order affects outputs and is part of the build definition.

Official documentation distinguishes node/transformation caching from document management based on doc_id and hashes. Caching avoids repeated computation; stable IDs and a docstore support duplicate detection and update behavior. Cache hits do not establish deletion completeness or transactional consistency with remote vector storage.

A production build separates preparation, transformation, writing, verification, and publication. Persist recoverable job state. Build a new index version and switch readers after validation instead of deleting and rewriting the live collection. Recovery must reconcile cache, document store, and vector store versions.

## Example and execution scope

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

```python
from llama_index.core import Document
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.embeddings import MockEmbedding
pipeline = IngestionPipeline(transformations=[
    SentenceSplitter(chunk_size=128, chunk_overlap=16),
    MockEmbedding(embed_dim=8),
])
nodes = pipeline.run(documents=[Document(text="A receipt is required.", id_="policy")])
assert nodes and len(nodes[0].embedding) == 8
# No vector_store or docstore is attached: this does not demonstrate database upserts.
```

## Key points and difficulties

Key: caching is neither synchronization nor a transaction. Difficulty: retries, edits, deletions, and partial success require distinct handling.

## Interview question and answer

Q: Why back up the database after pipeline.persist? A: local pipeline state does not necessarily include remote vectors; recovery must cover all state components.

## Production pitfalls and mitigation

Pitfall: saving cache without stable source identity still permits duplicate writes. Add source keys, content hashes, job manifests, and idempotent writes.

## Exercise and acceptance criteria

Run an unchanged document twice and an edited document once. Track node and vector counts. Acceptance: explain the actual backend’s deduplication, update, and deletion behavior.
