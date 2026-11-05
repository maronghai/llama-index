# 07.03 子问题分解与多文档比较

[返回全书目录 / Contents](../00-contents.md)

“比较两家公司三年的收入变化并解释差异”包含多个实体、时间点和计算步骤。子问题分解把任务拆为可检索的事实，再汇总。LlamaIndex 的子问题查询模式适合这种场景，但规划本身也会出错，必须检查子问题是否覆盖原问题且没有新增假设。

为每个子结果保留单位、期间、来源和缺失状态。财年与自然年、合并口径与单体口径不能直接比较。先用结构化记录对齐口径，再用确定性函数计算增长率；分母为零或数据缺失时明确输出不可计算，而不是让模型补值。

并行运行独立子问题可减少关键路径时间，但会放大 API 并发与预算。设置总任务期限、单步期限、最大子问题数和部分失败语义。汇总回答应区分完整结论与仅基于部分数据的观察。

## 重点与难点

重点：规划、事实提取、计算、汇总分层。难点：跨来源单位和期间对齐。

## 面试考点与参考回答

问：如何避免分解后答非所问？答：把原需求转成检查项，验证子问题覆盖率，并在最终汇总时逐项核对。

## 项目中的坑与处置

坑：子问题失败被当成零值参与平均。处置：用显式缺失状态，不允许缺失值进入计算。

## 动手实验与验收

比较两份不同期间的报告。验收：先拒绝错误口径比较，补齐可比数据后再计算并逐项引用。

## 代码实现补充：有预算的子问题计划与合并

依赖：Python 3.10+；仅使用 Python 标准库。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Task:
    source: str
    question: str

facts = {"a": {"hotel": 500}, "b": {"hotel": 650}}

def execute_plan(tasks, authorized, max_calls=3):
    if len(tasks) > max_calls:
        raise ValueError("plan exceeds call budget")
    results = []
    for task in tasks:
        if task.source not in authorized:
            raise PermissionError(task.source)
        value = facts.get(task.source, {}).get(task.question)
        results.append({"source": task.source, "value": value, "ok": value is not None})
    return results

plan = [Task("a", "hotel"), Task("b", "hotel")]
rows = execute_plan(plan, {"a", "b"})
assert all(r["ok"] for r in rows)
difference = rows[1]["value"] - rows[0]["value"]
assert difference == 150
print({"evidence": rows, "difference": difference})
```

### 实现说明、验收与项目边界

此处手写计划隔离“分解是否合理”和“执行是否可靠”。接入 SubQuestionQueryEngine 时让模型产生同类结构，再执行源授权、调用数和时间预算校验。缺失值必须标记失败，不能补成 0；金额、单位和生效日期一致后才可比较。

## 完整代码实现补充：子问题查询引擎 SubQuestionQueryEngine 分解与执行闭环

Python 3.10+；`llama-index-core==0.14.25`。混合检索另需 `llama-index-retrievers-bm25==0.8.0`，SQL 依赖 SQLAlchemy，事件流依赖 `llama-index-workflows`（core 的依赖）。独立进程运行完整代码块；首次 tokenizer 初始化可能读取或下载缓存，请离线部署时预置 `TIKTOKEN_CACHE_DIR`。

离线夹具只验证接口、来源和控制流，不验证语义质量或安全性。启用真实模型的分支需额外安装 `llama-index-llms-openai`、`llama-index-embeddings-openai`，重排分支另需 `llama-index-postprocessor-sbert-rerank`；设置 `RUN_REAL_MODELS=1`、`OPENAI_API_KEY`、`LLM_MODEL`、`EMBED_MODEL`（按示例需要）。这些外部模型分支本次未运行。

```python
import hashlib
import math
import re
from llama_index.core.embeddings import MockEmbedding as _MockEmbedding

class MockEmbedding(_MockEmbedding):
    # Test-only hashed lexical vectors; NOT a semantic embedding model.
    def _vector(self, text):
        values = [0.0] * 256
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            slot = int(hashlib.sha256(word.encode()).hexdigest()[:8], 16) % 256
            values[slot] += 1.0
        norm = math.sqrt(sum(v*v for v in values)) or 1.0
        return [v / norm for v in values]
    def _get_text_embedding(self, text):
        return self._vector(text)
    def _get_query_embedding(self, query):
        return self._vector(query)
    async def _aget_query_embedding(self, query):
        return self._vector(query)

from typing import Sequence, List
from llama_index.core import Document, VectorStoreIndex, Settings, QueryBundle
from llama_index.core.llms import MockLLM
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.question_gen.types import BaseQuestionGenerator, SubQuestion

embed_model = MockEmbedding(embed_dim=256)
llm = MockLLM(max_tokens=64)
Settings.embed_model = embed_model
Settings.llm = llm

docs_2024 = [Document(text="Year 2024 Revenue was 100M USD.", id_="doc_2024")]
docs_2025 = [Document(text="Year 2025 Revenue was 130M USD.", id_="doc_2025")]

idx_2024 = VectorStoreIndex.from_documents(docs_2024, embed_model=embed_model)
idx_2025 = VectorStoreIndex.from_documents(docs_2025, embed_model=embed_model)

tools = [
    QueryEngineTool(query_engine=idx_2024.as_query_engine(llm=llm), metadata=ToolMetadata(name="fin_2024", description="2024 Financials")),
    QueryEngineTool(query_engine=idx_2025.as_query_engine(llm=llm), metadata=ToolMetadata(name="fin_2025", description="2025 Financials"))
]

# 确定性子问题生成器：将复合对比转化为两个原子查询
class DeterministicQuestionGenerator(BaseQuestionGenerator):
    def _get_prompts(self):
        return {}
    def _update_prompts(self, prompts):
        pass
    def generate(self, tools: Sequence[ToolMetadata], query: QueryBundle) -> List[SubQuestion]:
        return [
            SubQuestion(sub_question="What was the revenue in 2024?", tool_name="fin_2024"),
            SubQuestion(sub_question="What was the revenue in 2025?", tool_name="fin_2025")
        ]
    async def agenerate(self, tools: Sequence[ToolMetadata], query: QueryBundle) -> List[SubQuestion]:
        return self.generate(tools, query)

sub_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=tools,
    question_gen=DeterministicQuestionGenerator(),
    llm=llm,
    use_async=False
)

response = sub_engine.query("Compare revenue between 2024 and 2025")
assert response.source_nodes is not None
print("SubQuestionQueryEngine verified; gathered source count:", len(response.source_nodes))

source_ids = {s.node.ref_doc_id for s in response.source_nodes if s.node.ref_doc_id}
assert {'doc_2024', 'doc_2025'} <= source_ids
# Compute with verified structured values rather than asking the LLM to do arithmetic.
revenue = {'2024': 100, '2025': 130}
growth = (revenue['2025'] / revenue['2024'] - 1) * 100
assert round(growth, 2) == 30.0
print({'verified_growth_percent': round(growth, 2)})
```

### 架构说明与工程边界

确定性生成器只适用于本例的两年比较，不会泛化分解任意问题。真实系统可用 LLMQuestionGenerator.from_defaults(llm=真实模型) 替换，并验证工具名、子问题数量和授权范围；两个年度来源均进入结果后，对结构化数值单独计算增长率。
