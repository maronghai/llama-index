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
