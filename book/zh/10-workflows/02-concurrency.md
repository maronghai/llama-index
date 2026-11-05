# 10.02 异步、限流、取消与重试

[返回全书目录 / Contents](../00-contents.md)

异步适合等待网络 I/O，不会自动加速 CPU 密集解析。把同步阻塞调用放入 async 函数仍会阻塞事件循环。根据瓶颈选择异步客户端、受控线程或独立进程，避免无界创建任务。服务限额应按供应商、模型和租户分别管理。

并发限制与速率限制不同：Semaphore 限制同时运行数量，令牌桶等机制限制单位时间请求数。重试只对可恢复错误生效，并受总期限与预算约束。写操作在重试前必须保证幂等；超时可能意味着服务器已经成功但响应丢失。

取消应从入口传播到检索、模型与后台任务。对不可取消的第三方请求，要记录仍在进行的成本，防止用户重试产生更多负载。系统过载时采用有界队列与明确拒绝，比无限排队更容易保证尾延迟。

## 重点与难点

重点：异步不等于限流。难点：超时后的不确定执行状态与写入重试。

## 面试考点与参考回答

问：并发越大越快吗？答：不一定，可能触发限额、内存增长和重试风暴；以吞吐、尾延迟和错误率共同选择。

## 项目中的坑与处置

坑：asyncio.gather 一次创建数十万请求。处置：有界工作池、背压与总预算，不只在内部加一个 Semaphore。

## 动手实验与验收

用可控延迟与故障模拟 API，比较无界和有界并发。验收：队列长度受限，取消无泄漏，重试次数可审计。

## 代码实现补充：带超时与重试上限的异步调用

依赖：Python 3.10+；仅使用 Python 标准库。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

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

### 实现说明、验收与项目边界

把 operation 替换为工作流 step 中的异步模型或检索调用即可复用。这里只重试超时和连接异常；取消信号不被吞掉，退避期间释放并发槽。生产还需总截止时间、带抖动退避、429 的 Retry-After、幂等键与全服务限额；Semaphore 只限制本进程并发，不等于每秒速率限制。
