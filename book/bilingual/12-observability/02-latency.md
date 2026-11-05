# 12.02 延迟分解、缓存与容量规划 / Latency decomposition, caching, and capacity

[返回全书目录 / Contents](../00-contents.md)

总延迟包括排队、检索、重排、上下文处理、模型生成和网络。并行任务的关键路径是最长依赖路径，不是所有阶段耗时相加。分别报告 p50、p95 和 p99，平均值可能掩盖少数极慢请求。首 token、生成完成和引用校验完成也应分开定义。

Latency includes queueing, retrieval, reranking, context processing, generation, and network time. Parallel latency follows the longest dependency path rather than summing every span. Report percentiles, and distinguish first token, generation completion, and citation validation.

缓存可位于解析、嵌入、检索和回答层。缓存键应包含索引版本、模型版本、规范化问题及必要授权范围。语义缓存用相似问题复用答案存在风险：“上限 500 吗”和“上限 5000 吗”可能接近却意义不同。金额、否定、时间和身份应参与严格校验。

Caches can cover parsing, embeddings, retrieval, and answers. Keys need index and model versions, normalized queries, and authorization scope. Semantic caching is risky for similar-looking questions with different amounts or negations. Validate money, time, identity, and polarity strictly.

容量规划通过固定流量模型压测，观察排队和资源饱和点。不要只测单用户热缓存。包含冷启动、缓存未命中、大上下文、限额和下游失败。预热索引与复用客户端能改善延迟，但不能取代有界队列与过载保护。

Load-test a defined traffic model and find queueing and saturation limits. Include cold starts, misses, long contexts, quotas, and failures rather than only a warm single user. Warm indexes and reusable clients help, but bounded queues and overload protection remain necessary.

## 重点与难点 / Key points and difficulties

重点：尾延迟和关键路径。难点：缓存隔离、失效与真实负载分布。

Key: tail latency and critical paths. Difficulty: cache isolation, invalidation, and realistic workload distributions.

## 面试考点与参考回答 / Interview question and answer

问：为什么缓存后出现越权？答：键中缺少租户或权限版本，其他用户复用了受限答案；缓存命中仍需授权校验。

Q: Why can caching leak data? A: missing tenant or ACL versions let users reuse restricted answers. Hits still need authorization.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：压测全部使用同一问题，结果只代表缓存吞吐。处置：混合独特查询、冷热数据与长短上下文，并报告命中率。

Pitfall: repeatedly benchmarking one cached question. Mix unique queries, hot and cold data, and context lengths; report hit rates.

## 动手实验与验收 / Exercise and acceptance criteria

给每阶段分配延迟预算并进行压力阶梯实验。验收：报告最先饱和组件、p95 和可接受拒绝率。

Allocate stage budgets and increase load in steps. Acceptance: identify the first bottleneck, p95, and acceptable rejection rate.

## 代码实现补充 / Implementation supplement: 租户隔离的索引版本缓存与延迟分位数 / Tenant-scoped versioned caching and latency percentiles

依赖 / Dependencies: Python 3.10+; 仅标准库 / standard library only.

将完整代码保存为独立 `.py` 文件，在独立进程执行 `python filename.py`。无需密钥，无付费调用；验收为断言通过并输出结果。

Save the full block as a standalone `.py` file and run it in a separate process. No API key or paid call is needed; assertions must pass and results are printed.

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

### 实现说明、验收与项目边界 / Implementation, acceptance and production boundaries

ACL 修订号和索引版本必须来自服务端权威状态，不能信任客户端传值。此例没有并发合并、容量淘汰与跨进程共享，只用于解释正确缓存键。真实容量测试需分别测排队、检索、重排、首 token 与总耗时；五个样本的 p95 只是计算示例。

ACL revisions and index versions must come from authoritative server state, not client input. This demonstrates cache keys, not request coalescing, eviction or shared storage. Load tests should separate queueing, retrieval, reranking, first token and total duration. Five-sample p95 is only an arithmetic example.
