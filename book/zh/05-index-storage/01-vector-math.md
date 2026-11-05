# 05.01 VectorStoreIndex 与向量检索原理

[返回全书目录 / Contents](../00-contents.md)

向量检索把查询与节点映射到同一表示空间，然后按距离或相似度选候选。余弦相似度为点积除以范数乘积；归一化后点积与余弦排序一致。欧氏距离通常越小越近，而框架返回分数可能已变换方向。必须先查后端语义再设阈值。

VectorStoreIndex 组织节点与向量存储之间的关系，不等于某一种数据库。from_documents 执行文档到节点的构建，直接传 Nodes 则需要理解嵌入是否已存在。默认内存存储便于实验，重启后不会自动恢复。大规模后端通常使用近似最近邻，在延迟、内存和召回之间取舍。

top-k 只是候选数量，不是可信程度。当语料没有答案时，最近邻仍会返回某些内容。系统需要证据充分性判断和拒答策略。近似检索参数也影响候选质量，增加 k 不能完全修复索引构建错误、模型错配或错误权限过滤。

## 示例与运行边界

纯 Python 独立算法示例；不调用外部服务。

```python
import math
def cosine(a, b):
    denom = math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(y*y for y in b))
    if denom == 0:
        raise ValueError("Zero vector has undefined cosine")
    return sum(x*y for x,y in zip(a,b, strict=True)) / denom
assert abs(cosine([1, 0], [2, 0]) - 1.0) < 1e-12
print(cosine([1, 0], [0, 1]))
```

## 重点与难点

重点：相似度不是概率。难点：近似搜索、过滤与候选数量共同影响召回。

## 面试考点与参考回答

问：向量检索能否保证事实正确？答：不能，它衡量表示空间中的相关性；需要有效版本、来源和答案证据核验。

## 项目中的坑与处置

坑：把分数 0.8 解读成 80% 正确率。处置：使用标注集校准决策阈值，并记录分数所属模型与后端。

## 动手实验与验收

用二维向量手算余弦，再比较归一化前后的点积排名。验收：能解释同方向不同长度向量为何余弦相同。

## 完整代码实现补充：余弦数学相似度度量与 VectorStoreIndex 检索对齐

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

import math
from llama_index.core import Document, VectorStoreIndex

def manual_cosine(v1: list, v2: list) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    return dot / (norm1 * norm2) if norm1 and norm2 else 0.0

embed_model = MockEmbedding(embed_dim=256)
doc1 = Document(text="Deep learning neural network architectures", id_="doc_ai")
doc2 = Document(text="Financial investment and asset management", id_="doc_finance")

index = VectorStoreIndex.from_documents([doc1, doc2], embed_model=embed_model)
retriever = index.as_retriever(similarity_top_k=2)
candidates = retriever.retrieve("neural network models")

assert len(candidates) == 2
print("VectorStoreIndex retrieved nodes:")
for c in candidates:
    print(f"- Node: {c.node.ref_doc_id}, score: {getattr(c, 'score', 'N/A')}")

query_vec = embed_model.get_query_embedding('neural network models')
for hit in candidates:
    node_vec = embed_model.get_text_embedding(hit.node.get_content())
    expected = manual_cosine(query_vec, node_vec)
    assert abs(hit.score - expected) < 1e-6
assert candidates[0].node.ref_doc_id == 'doc_ai'
assert manual_cosine([0,0], [1,0]) == 0
```

### 架构说明与工程边界

使用可复现的词项哈希向量，逐条核对框架检索分数与手算余弦，并测试零向量。该编码器仅用于算法验收，无法代表真实语义检索效果；换模型时必须重建全部向量。
