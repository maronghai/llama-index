# 13.03 Runbooks, incident drills, and change management

[返回全书目录 / Contents](../00-contents.md)

Runbooks begin with symptoms: empty answers, bad citations, access anomalies, latency, cost spikes, and stale data. Define inspection, containment, recovery, and verification for each. Suspected unauthorized access requires containing the affected path while preserving audit evidence.

Treat freshness as an SLO alongside availability. Measure lag from source revisions to published indexes and distinguish source inactivity, connector failure, build failure, and publication failure. Define stricter propagation targets for deletion and access revocation.

Change management covers models, prompts, chunking, dependencies, indexes, and source schemas. Record rationale, evaluation, risks, rollback, and ownership. Incident reviews should identify mechanisms and monitoring gaps rather than simply blaming model variability.

## Key points and difficulties

Key: define freshness, authorization propagation, and recovery targets. Difficulty: locating failures across ingestion, release, and caches.

## Interview question and answer

Q: What causes sudden retrieval degradation? A: corpus or ACL changes, embeddings, index releases, filter semantics, backend settings, or cache versions; inspect recent changes by stage.

## Production pitfalls and mitigation

Pitfall: removing filters to restore availability. Never degrade authorization; return controlled failure or an authorized rollback version.

## Exercise and acceptance criteria

Drill store outage, stale synchronization, and a bad index release. Acceptance: detection, containment, recovery, and verification records.

## Implementation supplement: Deletion propagation and reconciliation drills

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
state = {
    "vectors": {"doc-1": ["n1", "n2"], "doc-2": ["n3"]},
    "keywords": {"doc-1": ["n1", "n2"], "doc-2": ["n3"]},
    "summaries": {"doc-1": "summary-1"},
    "cache": {"doc-1": "cached-answer"},
}
tombstones = set()

def delete_source(source_id):
    # Readers must reject tombstoned sources immediately.
    tombstones.add(source_id)
    for store in state.values():
        store.pop(source_id, None)

def remaining(source_id):
    return [name for name, store in state.items() if source_id in store]

delete_source("doc-1")
assert remaining("doc-1") == []
assert "doc-2" in state["vectors"]
delete_source("doc-1")
assert "doc-1" in tombstones
print({"residual_stores": remaining("doc-1"), "idempotent": True})
```

### Implementation, acceptance and production boundaries

Block reads with a tombstone, clean derived artifacts, then reconcile. Dictionaries simulate stores. Production needs reverse dependencies, durable job state, retries, dead letters and audit evidence. Include backups and session memory and replay tombstones after restoration. This drill is not proof of deletion in a deployed system.
