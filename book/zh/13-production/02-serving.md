# 13.02 服务化、配置与发布策略

[返回全书目录 / Contents](../00-contents.md)

生产服务启动时加载已发布索引，不应每次 HTTP 请求重建索引。启动探针检查配置和必需资源，就绪探针确认能够提供正确版本的服务。健康探针不宜每秒调用昂贵模型，否则监控本身可能消耗配额并触发故障。

将摄取作业与查询服务拆开，分别扩容与授权。发布包绑定应用版本、索引版本、嵌入模型、提示版本和模式版本。支持灰度与回滚，确保应用和索引之间兼容。新模型或维度迁移采用新集合构建，不能对旧集合边查询边无约束重写。

接口应提供请求 ID、明确错误类型、超时与取消语义。回答结构包含正文、引用、索引版本和必要的拒答状态。不要把内部堆栈、凭据或全部候选暴露给客户端。下列伪代码描述边界，不是可直接启动的完整 Web 服务。

## 示例与运行边界

以下为架构伪代码，不可直接运行。

```text
request = authenticate_and_validate(incoming_request)
scope = authorization_scope(request.identity)
release = load_published_release()
evidence = retrieve(request.query, release, scope)
evidence = validate_and_budget(evidence, scope)
answer = generate_with_deadline(request.query, evidence)
return validate_citations_and_serialize(answer, release.version)
```

## 重点与难点

重点：发布对象包含应用与索引。难点：兼容性、灰度比较和快速回滚。

## 面试考点与参考回答

问：为什么摄取与查询分开部署？答：资源模式、权限和失败影响不同；隔离后重建不会拖垮在线请求。

## 项目中的坑与处置

坑：启动时自动重建巨大索引，所有副本同时耗尽配额。处置：独立构建与版本化发布，服务只读取就绪版本。

## 动手实验与验收

设计一次新嵌入模型灰度发布。验收：旧版本可回滚，权限负例通过，观察窗口内有质量与成本指标。

## 代码实现补充：可回滚的版本发布门禁

依赖：Python 3.10+；仅使用 Python 标准库。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

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

### 实现说明、验收与项目边界

每个 Artifact 在独立存储中构建完整索引，运行时将嵌入模型、维度、权限 schema 与索引作为一个整体加载。此例只模拟单进程指针交换，不实现 HTTP 服务或分布式原子发布。生产使用带比较交换的配置存储、就绪探针、预热、灰度和旧版本保留。
