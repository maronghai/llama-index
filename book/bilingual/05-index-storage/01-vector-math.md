# 05.01 VectorStoreIndex 与向量检索原理 / VectorStoreIndex and vector retrieval

[返回全书目录 / Contents](../00-contents.md)

向量检索把查询与节点映射到同一表示空间，然后按距离或相似度选候选。余弦相似度为点积除以范数乘积；归一化后点积与余弦排序一致。欧氏距离通常越小越近，而框架返回分数可能已变换方向。必须先查后端语义再设阈值。

Vector retrieval maps queries and nodes into a compatible representation space and ranks candidates by distance or similarity. Cosine divides the dot product by vector norms; normalized dot-product ranking equals cosine ranking. Euclidean distance normally decreases with closeness, but returned scores may be transformed. Confirm backend semantics before setting cutoffs.

VectorStoreIndex 组织节点与向量存储之间的关系，不等于某一种数据库。from_documents 执行文档到节点的构建，直接传 Nodes 则需要理解嵌入是否已存在。默认内存存储便于实验，重启后不会自动恢复。大规模后端通常使用近似最近邻，在延迟、内存和召回之间取舍。

VectorStoreIndex connects nodes with vector storage; it is not a particular database. from_documents builds nodes from documents, while direct node construction requires awareness of existing embeddings. In-memory defaults suit experiments but do not survive restart automatically. Large stores often use approximate search with recall, latency, and memory tradeoffs.

top-k 只是候选数量，不是可信程度。当语料没有答案时，最近邻仍会返回某些内容。系统需要证据充分性判断和拒答策略。近似检索参数也影响候选质量，增加 k 不能完全修复索引构建错误、模型错配或错误权限过滤。

Top-k specifies candidate count, not confidence. Nearest-neighbor search returns something even when the answer is absent. Add evidence-sufficiency checks and abstention. Larger k cannot repair model mismatch, bad indexing, or incorrect authorization filters.

## 示例与运行边界 / Example and execution scope

纯 Python 独立算法示例；不调用外部服务。

Standalone pure-Python algorithm example without external services.

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

## 重点与难点 / Key points and difficulties

重点：相似度不是概率。难点：近似搜索、过滤与候选数量共同影响召回。

Key: similarity is not probability. Difficulty: approximation, filtering, and candidate counts jointly affect recall.

## 面试考点与参考回答 / Interview question and answer

问：向量检索能否保证事实正确？答：不能，它衡量表示空间中的相关性；需要有效版本、来源和答案证据核验。

Q: Does vector retrieval guarantee truth? A: no. It measures representation-level relevance; validity, provenance, and evidence still need checking.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：把分数 0.8 解读成 80% 正确率。处置：使用标注集校准决策阈值，并记录分数所属模型与后端。

Pitfall: interpreting 0.8 as 80% correctness. Calibrate decision thresholds on labeled examples and bind them to a model and backend.

## 动手实验与验收 / Exercise and acceptance criteria

用二维向量手算余弦，再比较归一化前后的点积排名。验收：能解释同方向不同长度向量为何余弦相同。

Compute cosine on two-dimensional vectors and compare raw versus normalized dot products. Acceptance: explain equal cosine for vectors with the same direction but different magnitudes.
