# 10.02 异步、限流、取消与重试 / Async execution, rate limiting, cancellation, and retries

[返回全书目录 / Contents](../00-contents.md)

异步适合等待网络 I/O，不会自动加速 CPU 密集解析。把同步阻塞调用放入 async 函数仍会阻塞事件循环。根据瓶颈选择异步客户端、受控线程或独立进程，避免无界创建任务。服务限额应按供应商、模型和租户分别管理。

Async execution helps with network waits, not automatically with CPU-heavy parsing. Blocking calls still block an async function. Use async clients, bounded threads, or processes according to the bottleneck, and avoid unbounded tasks. Apply limits by provider, model, and tenant.

并发限制与速率限制不同：Semaphore 限制同时运行数量，令牌桶等机制限制单位时间请求数。重试只对可恢复错误生效，并受总期限与预算约束。写操作在重试前必须保证幂等；超时可能意味着服务器已经成功但响应丢失。

Concurrency limits bound simultaneous work; rate limits bound requests over time. Retry only recoverable failures within overall deadlines and budgets. Writes must be idempotent because a timeout can occur after the server committed the action.

取消应从入口传播到检索、模型与后台任务。对不可取消的第三方请求，要记录仍在进行的成本，防止用户重试产生更多负载。系统过载时采用有界队列与明确拒绝，比无限排队更容易保证尾延迟。

Propagate cancellation through retrieval, models, and background tasks. Track costs for third-party work that cannot be canceled. Under overload, bounded queues and explicit rejection protect tail latency better than unlimited waiting.

## 重点与难点 / Key points and difficulties

重点：异步不等于限流。难点：超时后的不确定执行状态与写入重试。

Key: async is not rate limiting. Difficulty: ambiguous execution after timeouts and retried writes.

## 面试考点与参考回答 / Interview question and answer

问：并发越大越快吗？答：不一定，可能触发限额、内存增长和重试风暴；以吞吐、尾延迟和错误率共同选择。

Q: Does more concurrency always help? A: no; rate limits, memory, and retry storms can dominate. Tune throughput with tail latency and errors.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：asyncio.gather 一次创建数十万请求。处置：有界工作池、背压与总预算，不只在内部加一个 Semaphore。

Pitfall: creating hundreds of thousands of tasks at once. Use bounded workers and backpressure, not only an internal semaphore.

## 动手实验与验收 / Exercise and acceptance criteria

用可控延迟与故障模拟 API，比较无界和有界并发。验收：队列长度受限，取消无泄漏，重试次数可审计。

Simulate latency and failures. Acceptance: bounded queues, clean cancellation, and auditable retry counts.

## 代码实现补充 / Implementation supplement: 带超时与重试上限的异步调用 / Async calls with timeouts and bounded retries

依赖 / Dependencies: Python 3.10+; 仅标准库 / standard library only.

将完整代码保存为独立 `.py` 文件，在独立进程执行 `python filename.py`。无需密钥，无付费调用；验收为断言通过并输出结果。

Save the full block as a standalone `.py` file and run it in a separate process. No API key or paid call is needed; assertions must pass and results are printed.

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

### 实现说明、验收与项目边界 / Implementation, acceptance and production boundaries

把 operation 替换为工作流 step 中的异步模型或检索调用即可复用。这里只重试超时和连接异常；取消信号不被吞掉，退避期间释放并发槽。生产还需总截止时间、带抖动退避、429 的 Retry-After、幂等键与全服务限额；Semaphore 只限制本进程并发，不等于每秒速率限制。

Use an async model or retrieval call as operation inside a workflow step. Only timeouts and connection failures are retried; cancellation propagates and backoff releases the slot. Add overall deadlines, jitter, Retry-After handling, idempotency and service-wide quotas. A semaphore limits local concurrency, not requests per second.
