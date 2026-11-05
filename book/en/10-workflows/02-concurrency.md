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

## Implementation supplement: Async calls with timeouts and bounded retries

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
import asyncio

async def call_one(item, semaphore, operation, attempts=3):
    for attempt in range(attempts):
        try:
            async with semaphore:
                return await asyncio.wait_for(operation(item), timeout=1)
        except (TimeoutError, ConnectionError):
            if attempt + 1 == attempts:
                raise
            await asyncio.sleep(0.01 * (2 ** attempt))

async def main():
    calls = {}
    async def unstable(item):
        calls[item] = calls.get(item, 0) + 1
        if item == 2 and calls[item] == 1:
            raise ConnectionError("temporary failure")
        await asyncio.sleep(0)
        return item * 10
    semaphore = asyncio.Semaphore(2)
    tasks = [asyncio.create_task(call_one(i, semaphore, unstable)) for i in range(4)]
    try:
        results = await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    assert results == [0, 10, 20, 30] and calls[2] == 2
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
```

### Implementation, acceptance and production boundaries

Use an async model or retrieval call as operation inside a workflow step. Only timeouts and connection failures are retried; cancellation propagates and backoff releases the slot. Add overall deadlines, jitter, Retry-After handling, idempotency and service-wide quotas. A semaphore limits local concurrency, not requests per second.
