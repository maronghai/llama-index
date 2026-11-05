# 13.02 Serving, configuration, and rollout strategies

[返回全书目录 / Contents](../00-contents.md)

Load published indexes at startup rather than rebuilding on each request. Startup checks validate configuration and resources; readiness confirms service with the intended version. Avoid expensive model calls in frequent health probes.

Separate ingestion workers from query serving for scaling and permissions. Bind application, index, embedding, prompt, and schema versions into a release. Support canaries and rollback with compatibility checks. Migrate embeddings through new collections rather than unrestricted in-place rewrites.

APIs need request IDs, error types, deadlines, and cancellation semantics. Responses should contain text, citations, index version, and abstention state. Do not expose stacks, credentials, or all candidates. The pseudocode describes boundaries rather than a runnable server.

## Example and execution scope

This is architecture pseudocode, not executable code.

```text
request = authenticate_and_validate(incoming_request)
scope = authorization_scope(request.identity)
release = load_published_release()
evidence = retrieve(request.query, release, scope)
evidence = validate_and_budget(evidence, scope)
answer = generate_with_deadline(request.query, evidence)
return validate_citations_and_serialize(answer, release.version)
```

## Key points and difficulties

Key: release application and index versions together. Difficulty: compatibility, canary comparison, and rollback.

## Interview question and answer

Q: Why separate ingestion from serving? A: resource patterns, permissions, and failure impact differ; rebuilding should not overwhelm live queries.

## Production pitfalls and mitigation

Pitfall: every replica rebuilds a large index on startup. Build separately and serve only published versions.

## Exercise and acceptance criteria

Plan a canary embedding migration. Acceptance: rollback, access-denial checks, and quality/cost metrics during observation.

## Implementation supplement: A rollback-capable release gate

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Artifact:
    version: str
    embedding: str
    dimension: int
    acl_schema: str

active = Artifact("v1", "embed-A", 384, "acl-2")
previous = None

def publish(candidate, metrics):
    global active, previous
    if candidate.dimension <= 0 or not candidate.version:
        raise ValueError("invalid artifact")
    if metrics["unauthorized_hits"] != 0 or metrics["recall"] < 0.9:
        raise ValueError("evaluation gate failed")
    previous, active = active, candidate

candidate = Artifact("v2", "embed-A", 384, "acl-2")
publish(candidate, {"unauthorized_hits": 0, "recall": 0.93})
assert active.version == "v2" and previous.version == "v1"
# Atomic pointer swap is simulated by assignment in this single-process example.
active, previous = previous, active
assert active.version == "v1"
print(active)
```

### Implementation, acceptance and production boundaries

Build each artifact in isolated storage and load its embedding, dimension, ACL schema and index as one unit. Assignment here only simulates a single-process pointer swap, not HTTP serving or distributed atomic release. Use compare-and-swap configuration, readiness probes, warmup, canaries and retained prior artifacts.
