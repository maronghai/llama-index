# 07.02 Router 与多源路由 / Routing across sources

[返回全书目录 / Contents](../00-contents.md)

多源系统可能包含政策文档、工单、产品目录和数据库。Router 根据问题选择合适检索器或引擎。路由描述应说明数据覆盖范围、时间、语言和适合的问题，而不是空泛的“最好的工具”。路由器只负责选择，不会自动协调各来源的访问规则。

Multi-source systems may include policies, tickets, catalogs, and databases. Routers select suitable retrievers or engines. Tool descriptions should state coverage, time range, language, and supported questions. Selection does not automatically coordinate authorization.

确定性字段优先使用规则路由，例如租户、地区、数据类型。语义选择可用于问题类型，但应保留低置信度回退。单源选择更便宜，多源并行覆盖更全但增加成本与冲突。测试路由准确率时区分“选错来源”和“来源正确但没有答案”。

Use deterministic routing for tenant, region, and data type. Semantic selection can classify question intent with a fallback. Single-source routing is cheaper; parallel multi-source retrieval offers coverage at higher cost and conflict risk. Distinguish wrong routing from correct routing to an incomplete source.

工具描述和来源名称本身也可能泄露敏感信息。只给当前用户可见的工具集合，并对每次工具调用重新授权。记录路由理由的结构化摘要即可，不需要收集模型隐藏推理。

Tool names and descriptions may themselves reveal sensitive information. Expose only permitted tools and authorize every call. Log a concise routing rationale rather than attempting to collect hidden model reasoning.

## 重点与难点 / Key points and difficulties

重点：规则与语义路由结合。难点：低置信度回退、多源冲突与权限分层。

Key: combine rule-based and semantic routing. Difficulty: fallback, conflicts, and layered permissions.

## 面试考点与参考回答 / Interview question and answer

问：什么时候不要 Router？答：来源很少且成本可控时，并行检索可能更简单稳定；先证明路由能节省成本且不损失关键召回。

Q: When should routing be avoided? A: with few affordable sources, parallel retrieval may be simpler; prove routing saves cost without unacceptable recall loss.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：工具介绍过度相似，模型随机选路。处置：写清覆盖边界，用容易混淆的问题做对比评测。

Pitfall: nearly identical descriptions cause unstable selection. Specify boundaries and test ambiguous questions.

## 动手实验与验收 / Exercise and acceptance criteria

建立三类来源与 15 个路由问题，含跨源问题。验收：报告混淆矩阵和回退比例，解释每个误路由。

Create three sources and 15 routing questions including cross-source cases. Acceptance: a confusion matrix, fallback rate, and explanations for misroutes.

## 代码实现补充 / Implementation supplement: 可检查的多源路由基线 / An inspectable multi-source routing baseline

依赖 / Dependencies: Python 3.10+; `llama-index-core==0.14.25`。

将完整代码保存为独立 `.py` 文件，在独立进程执行 `python filename.py`。无需密钥，无付费调用；验收为断言通过并输出结果。

Save the full block as a standalone `.py` file and run it in a separate process. No API key or paid call is needed; assertions must pass and results are printed.

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

### 实现说明、验收与项目边界 / Implementation, acceptance and production boundaries

显式规则路由是 RouterQueryEngine 的可解释基线，不是该类的完整替代。混合问题和未知问题返回 None，交给澄清或多源流程；不要静默选第一项。替换为模型 selector 后，仍保留允许源列表、授权与误路由评测。Mock 响应只验证被选引擎被调用。

Rule routing is an interpretable baseline for RouterQueryEngine, not its full replacement. Mixed and unknown questions return None for clarification or multi-source handling. Model selectors still need source allowlists, authorization and routing evaluation. Mock responses verify dispatch only.

首次运行 / First run：tokenizer 可能下载编码缓存。离线运行需预置缓存并设置 `TIKTOKEN_CACHE_DIR`。Tokenization may download an encoding cache; provision it before offline use.

## 完整代码实现补充 / Code Implementation Supplement:RouterQueryEngine 多源工具意图路由与分发落地 / RouterQueryEngine Multi-Tool Intent Routing and Dispatching

Python 3.10+；`llama-index-core==0.14.25`。混合检索另需 `llama-index-retrievers-bm25==0.8.0`，SQL 依赖 SQLAlchemy，事件流依赖 `llama-index-workflows`（core 的依赖）。独立进程运行完整代码块；首次 tokenizer 初始化可能读取或下载缓存，请离线部署时预置 `TIKTOKEN_CACHE_DIR`。

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

离线夹具只验证接口、来源和控制流，不验证语义质量或安全性。启用真实模型的分支需额外安装 `llama-index-llms-openai`、`llama-index-embeddings-openai`，重排分支另需 `llama-index-postprocessor-sbert-rerank`；设置 `RUN_REAL_MODELS=1`、`OPENAI_API_KEY`、`LLM_MODEL`、`EMBED_MODEL`（按示例需要）。这些外部模型分支本次未运行。

Offline fixtures validate interfaces, provenance, and control flow, not semantic quality or security. Real-model branches additionally require `llama-index-llms-openai`, `llama-index-embeddings-openai`, and, for reranking, `llama-index-postprocessor-sbert-rerank`; set `RUN_REAL_MODELS=1`, `OPENAI_API_KEY`, `LLM_MODEL`, and `EMBED_MODEL` as required by the block. External-model branches have not been executed in this revision.

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

from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.llms import MockLLM
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors.embedding_selectors import EmbeddingSingleSelector

embed_model = MockEmbedding(embed_dim=256)
llm = MockLLM(max_tokens=32)
Settings.embed_model = embed_model
Settings.llm = llm

# 构建两个不同业务领域的专业知识库
idx_finance = VectorStoreIndex.from_documents(
    [Document(text="Finance: Expense claims must be submitted within 30 days.", id_="fin_1")],
    embed_model=embed_model
)
idx_engineering = VectorStoreIndex.from_documents(
    [Document(text="Engineering: Production deployments freeze every Friday.", id_="eng_1")],
    embed_model=embed_model
)

# 封装为查询引擎工具
tool_finance = QueryEngineTool(
    query_engine=idx_finance.as_query_engine(llm=llm),
    metadata=ToolMetadata(name="finance_tool", description="Answers finance, expense, and budget questions")
)
tool_engineering = QueryEngineTool(
    query_engine=idx_engineering.as_query_engine(llm=llm),
    metadata=ToolMetadata(name="engineering_tool", description="Answers software engineering and deployment questions")
)

# 组装基于语义匹配的单选路由引擎
selector = EmbeddingSingleSelector.from_defaults(embed_model=embed_model)
router = RouterQueryEngine(selector=selector, query_engine_tools=[tool_finance, tool_engineering])

response = router.query("When do deployments freeze for engineering?")
assert response.source_nodes is not None
print("Router successfully dispatched query; sources retrieved:", len(response.source_nodes))

assert {s.node.ref_doc_id for s in response.source_nodes} == {'eng_1'}
finance_response = router.query('finance expense budget')
assert {s.node.ref_doc_id for s in finance_response.source_nodes} == {'fin_1'}
print('Both routing directions verified.')
```

### 架构说明与工程边界 / Architecture and execution boundaries

使用词项哈希编码器验证两种路由方向及来源隔离，不宣称具备语义意图识别。生产中替换为真实 EmbeddingSingleSelector 编码器或 LLMSingleSelector；工具集合必须先按身份授权，未知或跨源问题需要显式回退。

Hashed lexical embeddings validate both routing directions and source isolation without claiming semantic intent recognition. Use a real embedding encoder or LLMSingleSelector in production, authorize tools before routing, and define fallback for unknown or cross-source questions.
