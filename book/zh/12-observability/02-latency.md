# 12.02 延迟分解、缓存与容量规划

[返回全书目录 / Contents](../00-contents.md)

总延迟包括排队、检索、重排、上下文处理、模型生成和网络。并行任务的关键路径是最长依赖路径，不是所有阶段耗时相加。分别报告 p50、p95 和 p99，平均值可能掩盖少数极慢请求。首 token、生成完成和引用校验完成也应分开定义。

缓存可位于解析、嵌入、检索和回答层。缓存键应包含索引版本、模型版本、规范化问题及必要授权范围。语义缓存用相似问题复用答案存在风险：“上限 500 吗”和“上限 5000 吗”可能接近却意义不同。金额、否定、时间和身份应参与严格校验。

容量规划通过固定流量模型压测，观察排队和资源饱和点。不要只测单用户热缓存。包含冷启动、缓存未命中、大上下文、限额和下游失败。预热索引与复用客户端能改善延迟，但不能取代有界队列与过载保护。

## 重点与难点

重点：尾延迟和关键路径。难点：缓存隔离、失效与真实负载分布。

## 面试考点与参考回答

问：为什么缓存后出现越权？答：键中缺少租户或权限版本，其他用户复用了受限答案；缓存命中仍需授权校验。

## 项目中的坑与处置

坑：压测全部使用同一问题，结果只代表缓存吞吐。处置：混合独特查询、冷热数据与长短上下文，并报告命中率。

## 动手实验与验收

给每阶段分配延迟预算并进行压力阶梯实验。验收：报告最先饱和组件、p95 和可接受拒绝率。

## 代码实现补充：租户隔离的索引版本缓存与延迟分位数

依赖：Python 3.10+；仅使用 Python 标准库。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

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

### 实现说明、验收与项目边界

ACL 修订号和索引版本必须来自服务端权威状态，不能信任客户端传值。此例没有并发合并、容量淘汰与跨进程共享，只用于解释正确缓存键。真实容量测试需分别测排队、检索、重排、首 token 与总耗时；五个样本的 p95 只是计算示例。
