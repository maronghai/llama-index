# 12.01 Trace、OpenTelemetry 与 Phoenix

[返回全书目录 / Contents](../00-contents.md)

一次请求应关联身份校验、查询改写、检索、重排、生成和工具调用。Trace 组织一次请求，span 记录具体阶段。记录模型与索引版本、候选数、token、耗时和错误类型，能让“答案慢”变成可定位的问题。OpenTelemetry 与 OpenInference 的集成包和接线方式随版本变化，需按实际部署核对。

Phoenix 等追踪与评估工具可辅助查看调用树和实验，但不能默认把全部提示、节点正文与用户消息上传。先定义日志分级、脱敏、采样、访问权限和保留期。线上可仅存文档 ID 与内容哈希，调试时经授权查询原文。

异步任务与多 Agent 交接要传播 trace context。缺少父子关系会让并发调用看成互不相关的请求。观测本身也可能失败或变慢，因此导出器要有界缓冲、超时与降级策略，不应因日志服务不可用而阻断核心查询。

## 重点与难点

重点：版本与证据链进入 Trace。难点：观测与隐私、开销之间的平衡。

## 面试考点与参考回答

问：日志和 Trace 有何区别？答：日志记录离散事件，Trace 关联跨组件请求路径；两者通过 trace_id 对齐更易定位问题。

## 项目中的坑与处置

坑：调试日志长期存储完整私密文档。处置：默认脱敏与最小字段，受控开启短期详细采样。

## 动手实验与验收

对一个请求画调用树，模拟模型超时。验收：定位故障 span，不必查看敏感正文也能判断阶段与版本。

## 代码实现补充：请求关联、分阶段耗时与异常记录

依赖：Python 3.10+；仅使用 Python 标准库。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
import json
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar

request_id = ContextVar("request_id", default="unset")
spans = []
@contextmanager
def span(name):
    started = time.perf_counter()
    record = {"trace_id": request_id.get(), "name": name, "status": "ok"}
    try:
        yield
    except Exception as exc:
        record.update(status="error", error_type=type(exc).__name__)
        raise
    finally:
        record["duration_ms"] = (time.perf_counter() - started) * 1000
        spans.append(record)

token = request_id.set(uuid.uuid4().hex)
try:
    with span("query"):
        with span("retrieve"):
            evidence = ["policy-1"]
        with span("synthesize"):
            answer = "cited answer"
finally:
    request_id.reset(token)
assert len({s["trace_id"] for s in spans}) == 1
assert {s["name"] for s in spans} == {"query", "retrieve", "synthesize"}
print(json.dumps(spans, indent=2))
```

### 实现说明、验收与项目边界

这是不依赖采集平台的追踪契约演示，不会向 Phoenix 发送数据。接入 OpenTelemetry 时替换 span 实现为 tracer.start_as_current_span，并配置 OpenInference 的 LlamaIndex instrumentor 与 OTLP exporter。生产还需 parent span ID、采样、异步传播和脱敏；不要把原文、密钥或完整提示直接写入 trace。
