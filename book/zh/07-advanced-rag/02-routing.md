# 07.02 Router 与多源路由

[返回全书目录 / Contents](../00-contents.md)

多源系统可能包含政策文档、工单、产品目录和数据库。Router 根据问题选择合适检索器或引擎。路由描述应说明数据覆盖范围、时间、语言和适合的问题，而不是空泛的“最好的工具”。路由器只负责选择，不会自动协调各来源的访问规则。

确定性字段优先使用规则路由，例如租户、地区、数据类型。语义选择可用于问题类型，但应保留低置信度回退。单源选择更便宜，多源并行覆盖更全但增加成本与冲突。测试路由准确率时区分“选错来源”和“来源正确但没有答案”。

工具描述和来源名称本身也可能泄露敏感信息。只给当前用户可见的工具集合，并对每次工具调用重新授权。记录路由理由的结构化摘要即可，不需要收集模型隐藏推理。

## 重点与难点

重点：规则与语义路由结合。难点：低置信度回退、多源冲突与权限分层。

## 面试考点与参考回答

问：什么时候不要 Router？答：来源很少且成本可控时，并行检索可能更简单稳定；先证明路由能节省成本且不损失关键召回。

## 项目中的坑与处置

坑：工具介绍过度相似，模型随机选路。处置：写清覆盖边界，用容易混淆的问题做对比评测。

## 动手实验与验收

建立三类来源与 15 个路由问题，含跨源问题。验收：报告混淆矩阵和回退比例，解释每个误路由。

## 代码实现补充：可检查的多源路由基线

依赖：Python 3.10+；安装 `llama-index-core==0.14.25`。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
from llama_index.core import Document, SummaryIndex
from llama_index.core.llms import MockLLM

llm = MockLLM(max_tokens=16)
engines = {
    "travel": SummaryIndex.from_documents([Document(text="Hotel limit is 500.")]).as_query_engine(llm=llm),
    "leave": SummaryIndex.from_documents([Document(text="Annual leave is 12 days.")]).as_query_engine(llm=llm),
}

def route(question):
    q = question.lower()
    matches = [name for name, terms in {"travel": ("hotel", "travel"), "leave": ("leave", "vacation")}.items()
               if any(term in q for term in terms)]
    return matches[0] if len(matches) == 1 else None

assert route("hotel limit?") == "travel"
assert route("hotel and leave rules?") is None
selected = route("hotel limit?")
response = engines[selected].query("hotel limit?")
assert response.source_nodes
print({"route": selected, "sources": len(response.source_nodes)})
```

### 实现说明、验收与项目边界

显式规则路由是 RouterQueryEngine 的可解释基线，不是该类的完整替代。混合问题和未知问题返回 None，交给澄清或多源流程；不要静默选第一项。替换为模型 selector 后，仍保留允许源列表、授权与误路由评测。Mock 响应只验证被选引擎被调用。

首次运行提示：核心包 tokenizer 可能下载编码缓存；离线环境请预置缓存并设置 `TIKTOKEN_CACHE_DIR`。无需模型密钥不代表首次运行不联网。
