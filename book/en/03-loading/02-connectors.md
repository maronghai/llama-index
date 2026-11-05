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
