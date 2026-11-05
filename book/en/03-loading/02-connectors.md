# 03.02 LlamaHub connectors and incremental synchronization

[返回全书目录 / Contents](../00-contents.md)

Remote connectors turn APIs, databases, and collaboration content into Documents. Connector catalogs help discovery, but package names, authentication, and loading arguments must be checked for the selected version. Prefer explicit imports and tested dependencies over assuming a tutorial’s dynamic-loader interface is permanently stable.

Synchronization must handle pagination, rate limits, retries, cursors, timestamps, and deletions. Timestamp cursors need a tie-breaker and a policy for late updates. Overlapping time windows plus stable-ID deduplication are safer than a strict timestamp cutoff. Advance checkpoints only after every page is durably processed.

Connector read access is not end-user authorization. A service account may see company-wide content that individual users cannot. Capture ACLs, source revisions, and tombstones, then enforce access during queries. Least privilege, redacted logs, and credential rotation are part of synchronization design.

## Key points and difficulties

Key: stable IDs, checkpoints, and deletion propagation. Difficulty: idempotent processing under at-least-once delivery without losing data or publishing duplicates.

## Interview question and answer

Q: How should full and incremental sync cooperate? A: incremental runs reduce routine cost; periodic reconciliation detects missed deletions, ACL drift, and cursor gaps with an audit trail.

## Production pitfalls and mitigation

Pitfall: immediate unlimited retries amplify rate-limit failures. Honor Retry-After, use bounded backoff with jitter, and route permanent failures to a review queue.

## Exercise and acceptance criteria

Simulate three pages and fail the second page. Acceptance: no premature checkpoint, no duplicate IDs, and deletions remove obsolete nodes and caches.

## Implementation supplement: Stable connector IDs and incremental reconciliation

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
import hashlib
import json

def digest(row):
    # Include metadata: an ACL change also requires publication.
    payload = json.dumps(row, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()

def reconcile(snapshot, rows):
    ids = [r["source_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate source IDs")
    current = {r["source_id"]: digest(r) for r in rows}
    changed = [r for r in rows if snapshot.get(r["source_id"]) != current[r["source_id"]]]
    removed = sorted(set(snapshot) - set(current))
    return changed, removed, current

first = [{"source_id": "wiki:17", "text": "Limit 500", "tenant": "a"}]
changed, removed, snapshot = reconcile({}, first)
assert len(changed) == 1 and not removed
assert reconcile(snapshot, first)[0] == []
changed, removed, next_snapshot = reconcile(snapshot, [])
assert removed == ["wiki:17"]
print({"deleted": removed})
```

### Implementation, acceptance and production boundaries

Normalize LlamaHub reader output to this contract, then create Documents using source_id. Only complete successful snapshots permit deletion detection. A partial page is not a snapshot. Publish vectors, keyword records and cache changes before committing next_snapshot, using transactions or recoverable checkpoints.

## Code Implementation Supplement:Incremental Connector Subclassing BaseReader with Hash Verification

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

Offline fixtures validate interfaces, provenance, and control flow, not semantic quality or security. Real-model branches additionally require `llama-index-llms-openai`, `llama-index-embeddings-openai`, and, for reranking, `llama-index-postprocessor-sbert-rerank`; set `RUN_REAL_MODELS=1`, `OPENAI_API_KEY`, `LLM_MODEL`, and `EMBED_MODEL` as required by the block. External-model branches have not been executed in this revision.

```python
import hashlib
from typing import List
from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

class CustomDatabaseReader(BaseReader):
    """企业级数据源连接器：继承 BaseReader，标准化生成 Document"""
    def __init__(self, tenant_id: str):
        super().__init__()
        self.tenant_id = tenant_id

    def load_data(self, records: List[dict]) -> List[Document]:
        documents = []
        for r in records:
            body = "Title: " + r.get("title", "") + "\nContent: " + r.get("content", "")
            content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
            doc = Document(
                text=body,
                id_=f"rec_{r['id']}",
                metadata={
                    "tenant_id": self.tenant_id,
                    "version": r.get("version", 1),
                    "content_hash": content_hash,
                    "category": r.get("category", "general")
                }
            )
            documents.append(doc)
        return documents

# 验证自定义加载器与元数据契约
reader = CustomDatabaseReader(tenant_id="tenant_hr")
records = [
    {"id": "leave_01", "title": "Sick Leave", "content": "Paid sick leave is 10 days.", "version": 2},
    {"id": "leave_02", "title": "Maternity Leave", "content": "Maternity leave is 128 days.", "version": 1}
]
docs = reader.load_data(records)

assert len(docs) == 2
assert docs[0].metadata["tenant_id"] == "tenant_hr"
assert docs[0].metadata["version"] == 2
assert "content_hash" in docs[0].metadata
print("Custom reader loaded docs:", len(docs), "sample hash:", docs[0].metadata["content_hash"][:12])

# Reconcile only a complete, successful snapshot. Never infer deletes from a partial page.
def reconcile(old, documents, complete):
    current = {d.id_: d.metadata['content_hash'] for d in documents}
    changed = [d for d in documents if old.get(d.id_) != current[d.id_]]
    removed = sorted(set(old) - set(current)) if complete else []
    return changed, removed, current

old = {d.id_: d.metadata['content_hash'] for d in docs}
assert not reconcile(old, docs, True)[0]
updated = reader.load_data([dict(records[0], content='Paid sick leave is 12 days.')])
changed, deleted, snapshot = reconcile(old, updated, True)
assert len(changed) == 1 and deleted == ['rec_leave_02']
assert reconcile(old, updated, False)[1] == []
print({'upserts': [d.id_ for d in changed], 'deletes': deleted})
```

### Architecture and execution boundaries

Records simulate upstream pages rather than a real database connection. Stable IDs, hashes, updates, and full-snapshot deletion reconciliation are implemented. Production IDs must include the tenant; persist job state and never infer deletes from incomplete pages.
