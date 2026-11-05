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
