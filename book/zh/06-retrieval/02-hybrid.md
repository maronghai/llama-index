# 06.02 BM25、向量与 RRF 融合

[返回全书目录 / Contents](../00-contents.md)

BM25 基于词项匹配，适合产品编号、罕见术语与精确名字；稠密向量擅长部分语义改写，但可能混淆相近数字。混合检索让两条通道各召回候选，再去重融合。中文 BM25 的分词、领域词典和编号处理会显著影响效果，默认英文分词不能直接视为合格中文基线。

RRF 使用排名而不是原始分数融合：对每条结果累加 1/(c+rank)，rank 从 1 开始，c 是平滑常数。这样避免直接相加不同分布的 BM25 与向量分数，但仍需选择通道权重、候选数和去重键。权重与 c 应在开发集上调整，不要在最终测试集反复试到满意。

融合前后都应保持授权边界。两条通道使用不同语料版本会返回已删除或旧制度。用稳定节点 ID 对齐候选，并记录每条候选的通道、原始排名和最终分数。若采用不同切块策略，不能只按正文字符串去重，否则来源和例外可能被误合并。

## 示例与运行边界

纯 Python 独立算法示例；不调用外部服务。

```python
from collections import defaultdict
def rrf(rankings, c=60):
    if c < 0:
        raise ValueError("c must be nonnegative")
    scores = defaultdict(float)
    for ranking in rankings:
        unique = list(dict.fromkeys(ranking))
        for rank, node_id in enumerate(unique, start=1):
            scores[node_id] += 1.0 / (c + rank)
    return sorted(scores.items(), key=lambda x: (-x[1], x[0]))
print(rrf([["a", "b", "c"], ["b", "d", "a"]]))
```

## 重点与难点

重点：稀疏与稠密互补，RRF 融合排名。难点：中文分词、稳定 ID 和两路语料一致性。

## 面试考点与参考回答

问：为什么不直接把 BM25 和余弦分数相加？答：分值尺度和分布不同，未经校准的相加缺乏稳定意义；可用排名融合或学习校准。

## 项目中的坑与处置

坑：top-k 各取很少，正确证据未入候选，后续融合救不回来。处置：先评估候选召回，再优化融合与重排。

## 动手实验与验收

用编号、同义词和中英文混合问题比较两路与融合。验收：展示各自独有命中和融合后的错误，而不是只说混合更好。

## 完整代码实现补充：BM25 词项检索与稠密向量的 QueryFusionRetriever 倒数排名融合

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
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever

embed_model = MockEmbedding(embed_dim=256)
llm = MockLLM(max_tokens=32)
Settings.embed_model = embed_model
Settings.llm = llm

docs = [
    Document(text="Apollo 11 landed humans on the Moon in July 1969.", id_="apollo_11"),
    Document(text="Artemis 3 program aims to land astronauts near the lunar South Pole.", id_="artemis_3"),
    Document(text="The International Space Station conducts microgravity experiments.", id_="iss")
]
nodes = SentenceSplitter(chunk_size=128, chunk_overlap=16).get_nodes_from_documents(docs)

# 1. 稠密向量检索器 (Dense Vector) 与稀疏关键词检索器 (Sparse BM25)
vector_index = VectorStoreIndex(nodes, embed_model=embed_model)
vector_retriever = vector_index.as_retriever(similarity_top_k=2)
bm25_retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=2)

# 2. QueryFusionRetriever 聚合两路候选，使用 RRF (Reciprocal Rank Fusion)
fusion_retriever = QueryFusionRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    similarity_top_k=2,
    mode="reciprocal_rerank",
    num_queries=1,
    use_async=False,
    llm=llm
)
results = fusion_retriever.retrieve("Apollo Moon landing 1969")

assert len(results) > 0
print("Hybrid Fusion search verified successfully:")
print(f"- Total merged candidates: {len(results)}")
print(f"- Top ranked document: {results[0].node.ref_doc_id}")

assert bm25_retriever.retrieve('Apollo Moon landing 1969')[0].node.ref_doc_id == 'apollo_11'
assert results[0].node.ref_doc_id == 'apollo_11'
assert len({h.node.node_id for h in results}) == len(results)
```

### 架构说明与工程边界

整合官方 BM25Retriever 与 VectorStoreIndex，使用 QueryFusionRetriever 开启倒数排名融合 (RRF)，显式配置 Mock 模型以杜绝网络依赖。
