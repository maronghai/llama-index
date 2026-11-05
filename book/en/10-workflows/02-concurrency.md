# 10.02 Async execution, rate limiting, cancellation, and retries

[返回全书目录 / Contents](../00-contents.md)

Async execution helps with network waits, not automatically with CPU-heavy parsing. Blocking calls still block an async function. Use async clients, bounded threads, or processes according to the bottleneck, and avoid unbounded tasks. Apply limits by provider, model, and tenant.

Concurrency limits bound simultaneous work; rate limits bound requests over time. Retry only recoverable failures within overall deadlines and budgets. Writes must be idempotent because a timeout can occur after the server committed the action.

Propagate cancellation through retrieval, models, and background tasks. Track costs for third-party work that cannot be canceled. Under overload, bounded queues and explicit rejection protect tail latency better than unlimited waiting.

## Key points and difficulties

Key: async is not rate limiting. Difficulty: ambiguous execution after timeouts and retried writes.

## Interview question and answer

Q: Does more concurrency always help? A: no; rate limits, memory, and retry storms can dominate. Tune throughput with tail latency and errors.

## Production pitfalls and mitigation

Pitfall: creating hundreds of thousands of tasks at once. Use bounded workers and backpressure, not only an internal semaphore.

## Exercise and acceptance criteria

Simulate latency and failures. Acceptance: bounded queues, clean cancellation, and auditable retry counts.
