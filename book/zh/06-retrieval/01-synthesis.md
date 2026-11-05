# 06.01 响应合成、引用与拒答

[返回全书目录 / Contents](../00-contents.md)

检索器提供候选节点，节点后处理负责过滤、去重或重排，响应合成器按上下文预算生成答案。refine 可能逐块修订答案并产生多次调用，compact 倾向先打包上下文，tree_summarize 通过树形合并摘要。具体调用数量还受块长度和模型窗口影响，不能仅凭模式名估算费用。

提示应定义任务、证据边界、冲突规则和无答案行为。“只根据上下文”有帮助，但不是保证。应把答案拆成可验证主张，每个重要主张引用支持它的段落。source_nodes 说明提供过哪些材料，不等于每句话都被这些材料支持。引用可访问性也应受权限控制。

证据不足时可以拒答或请求补充条件。存在多个版本冲突时，优先根据权威来源与生效时间解决；无法解决则说明冲突并引用双方。不要用生成模型的常识覆盖内部制度中的明确约束。对高风险金额、日期和编号，可增加确定性校验。

## 重点与难点

重点：来源列表不等于逐主张支持。难点：长上下文中的冲突、例外和截断，不能仅靠一个提示解决。

## 面试考点与参考回答

问：RAG 仍会幻觉吗？答：会。可能检索错误、上下文不足、证据被截断，或生成超出证据；需要分层检测和拒答。

## 项目中的坑与处置

坑：只引用整份 PDF，用户无法定位支持句。处置：保存段落与页码映射，按主张给出细粒度引用，并核对引用是否真正支持答案。

## 动手实验与验收

构造一条可回答、一条无答案和一条版本冲突的问题。验收：分别给出有据回答、拒答和冲突说明，不能都生成确定性结论。

## 代码实现补充：带证据 ID 的保守回答

依赖：Python 3.10+；安装 `llama-index-core==0.14.25`。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
from llama_index.core.schema import TextNode, NodeWithScore

def answer(question, hits, allowed_ids):
    trusted = [h for h in hits if h.node.node_id in allowed_ids]
    if not trusted:
        return {"answer": "Insufficient evidence", "citations": []}
    # Extractive baseline: do not invent a claim not in evidence.
    return {"answer": trusted[0].node.text,
            "citations": [trusted[0].node.node_id]}

node = TextNode(id_="policy-2-p3", text="Hotel allowance is CNY 500 per night.")
hits = [NodeWithScore(node=node, score=0.9)]
result = answer("Hotel allowance?", hits, {"policy-2-p3"})
assert result["citations"] == ["policy-2-p3"]
assert answer("Hotel allowance?", hits, set())["citations"] == []
print(result)
```

### 实现说明、验收与项目边界

这是检索后抽取式基线，question 参数仅用于展示服务接口，尚未用于相关性判断；必须先由检索与相关性门禁筛选候选。生产可将正文交给响应合成器，但引用 ID 必须从授权证据集合选择，并检查每个事实是否被引用支持。非空证据不等于足以回答。

首次运行提示：核心包 tokenizer 可能下载编码缓存；离线环境请预置缓存并设置 `TIKTOKEN_CACHE_DIR`。无需模型密钥不代表首次运行不联网。

## 完整代码实现补充：响应合成器模式 (Compact 与 Tree Summarize) 完整对比与验证

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

from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.llms import MockLLM
from llama_index.core.response_synthesizers import get_response_synthesizer, ResponseMode

embed_model = MockEmbedding(embed_dim=256)
llm = MockLLM(max_tokens=64)
Settings.embed_model = embed_model
Settings.llm = llm

docs = [
    Document(text="Maintenance window is every Sunday at 02:00 AM UTC.", id_="doc_maint"),
    Document(text="Database backup retention is strictly 30 days.", id_="doc_backup")
]
index = VectorStoreIndex.from_documents(docs, embed_model=embed_model)

# 1. Compact 模式: 紧凑填充上下文到 Prompt 模板
synth_compact = get_response_synthesizer(llm=llm, response_mode=ResponseMode.COMPACT)
engine_compact = index.as_query_engine(llm=llm, response_synthesizer=synth_compact)
res_compact = engine_compact.query("When is maintenance?")
assert res_compact.source_nodes and len(res_compact.source_nodes) >= 1

# 2. Tree Summarize 模式: 层次归纳与长文档跨块提炼
synth_tree = get_response_synthesizer(llm=llm, response_mode=ResponseMode.TREE_SUMMARIZE)
engine_tree = index.as_query_engine(llm=llm, response_synthesizer=synth_tree)
res_tree = engine_tree.query("Summarize maintenance and backup rules.")
assert res_tree.source_nodes and len(res_tree.source_nodes) >= 1

print("Synthesis pipelines verified:")
print(f"- Compact source count: {len(res_compact.source_nodes)}")
print(f"- Tree Summarize source count: {len(res_tree.source_nodes)}")
```

### 架构说明与工程边界

显式注入不同的 ResponseMode，验证紧凑填充与树状总结两种生产模式的管道构建与上下文引用溯源。
