# 12.02 Latency decomposition, caching, and capacity

[返回全书目录 / Contents](../00-contents.md)

Latency includes queueing, retrieval, reranking, context processing, generation, and network time. Parallel latency follows the longest dependency path rather than summing every span. Report percentiles, and distinguish first token, generation completion, and citation validation.

Caches can cover parsing, embeddings, retrieval, and answers. Keys need index and model versions, normalized queries, and authorization scope. Semantic caching is risky for similar-looking questions with different amounts or negations. Validate money, time, identity, and polarity strictly.

Load-test a defined traffic model and find queueing and saturation limits. Include cold starts, misses, long contexts, quotas, and failures rather than only a warm single user. Warm indexes and reusable clients help, but bounded queues and overload protection remain necessary.

## Key points and difficulties

Key: tail latency and critical paths. Difficulty: cache isolation, invalidation, and realistic workload distributions.

## Interview question and answer

Q: Why can caching leak data? A: missing tenant or ACL versions let users reuse restricted answers. Hits still need authorization.

## Production pitfalls and mitigation

Pitfall: repeatedly benchmarking one cached question. Mix unique queries, hot and cold data, and context lengths; report hit rates.

## Exercise and acceptance criteria

Allocate stage budgets and increase load in steps. Acceptance: identify the first bottleneck, p95, and acceptable rejection rate.

## Implementation supplement: Tenant-scoped versioned caching and latency percentiles

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
import math
import time

cache = {}
def cached_retrieve(tenant, principal, acl_revision, index_version, query, retrieve, ttl=60):
    key = (tenant, principal, acl_revision, index_version, query)
    now = time.monotonic()
    entry = cache.get(key)
    if entry and now < entry[0]:
        return list(entry[1]), True
    result = list(retrieve())
    cache[key] = (now + ttl, tuple(result))
    return result, False

def percentile(values, fraction):
    if not values or not 0 < fraction <= 1:
        raise ValueError("invalid percentile input")
    return sorted(values)[math.ceil(len(values) * fraction) - 1]

args = ("a", "u1", "acl-3", "index-7", "hotel?")
assert cached_retrieve(*args, lambda: ["node-1"])[1] is False
assert cached_retrieve(*args, lambda: ["unexpected"])[1] is True
assert cached_retrieve("b", *args[1:], lambda: ["node-2"])[0] == ["node-2"]
assert percentile([10, 20, 30, 40, 100], 0.95) == 100
print({"p95_ms": percentile([10, 20, 30, 40, 100], 0.95)})
```

### Implementation, acceptance and production boundaries

ACL revisions and index versions must come from authoritative server state, not client input. This demonstrates cache keys, not request coalescing, eviction or shared storage. Load tests should separate queueing, retrieval, reranking, first token and total duration. Five-sample p95 is only an arithmetic example.
