# 06.02 BM25、向量与 RRF 融合 / BM25, dense retrieval, and RRF

[返回全书目录 / Contents](../00-contents.md)

BM25 基于词项匹配，适合产品编号、罕见术语与精确名字；稠密向量擅长部分语义改写，但可能混淆相近数字。混合检索让两条通道各召回候选，再去重融合。中文 BM25 的分词、领域词典和编号处理会显著影响效果，默认英文分词不能直接视为合格中文基线。

BM25 matches terms and is useful for identifiers, rare terminology, and exact names. Dense embeddings handle semantic paraphrases but may confuse nearby numbers. Hybrid retrieval combines candidates from both channels. Chinese BM25 requires suitable tokenization and domain handling; an English default is not a valid Chinese baseline.

RRF 使用排名而不是原始分数融合：对每条结果累加 1/(c+rank)，rank 从 1 开始，c 是平滑常数。这样避免直接相加不同分布的 BM25 与向量分数，但仍需选择通道权重、候选数和去重键。权重与 c 应在开发集上调整，不要在最终测试集反复试到满意。

Reciprocal rank fusion sums 1/(c+rank), with ranks starting at one. Ranking avoids directly adding incompatible BM25 and vector scores, but channel weights, candidate counts, and deduplication keys still matter. Tune on development data rather than repeatedly optimizing against the final test set.

融合前后都应保持授权边界。两条通道使用不同语料版本会返回已删除或旧制度。用稳定节点 ID 对齐候选，并记录每条候选的通道、原始排名和最终分数。若采用不同切块策略，不能只按正文字符串去重，否则来源和例外可能被误合并。

Maintain authorization through both channels. Different corpus versions can reintroduce deleted or stale content. Align candidates using stable node IDs and retain channel, original rank, and fused score. String-only deduplication can incorrectly merge evidence with different provenance or exceptions.

## 示例与运行边界 / Example and execution scope

纯 Python 独立算法示例；不调用外部服务。

Standalone pure-Python algorithm example without external services.

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

## 重点与难点 / Key points and difficulties

重点：稀疏与稠密互补，RRF 融合排名。难点：中文分词、稳定 ID 和两路语料一致性。

Key: sparse and dense methods complement each other; RRF combines ranks. Difficulty: Chinese tokenization, stable identity, and synchronized corpora.

## 面试考点与参考回答 / Interview question and answer

问：为什么不直接把 BM25 和余弦分数相加？答：分值尺度和分布不同，未经校准的相加缺乏稳定意义；可用排名融合或学习校准。

Q: Why not add BM25 and cosine scores directly? A: their scales differ. Use rank fusion or learned calibration.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：top-k 各取很少，正确证据未入候选，后续融合救不回来。处置：先评估候选召回，再优化融合与重排。

Pitfall: tiny candidate pools exclude the right evidence before fusion. Measure candidate recall before tuning fusion and reranking.

## 动手实验与验收 / Exercise and acceptance criteria

用编号、同义词和中英文混合问题比较两路与融合。验收：展示各自独有命中和融合后的错误，而不是只说混合更好。

Compare channels and fusion on identifiers, synonyms, and mixed-language questions. Acceptance: show unique wins and fusion failures, not just an aggregate claim.
