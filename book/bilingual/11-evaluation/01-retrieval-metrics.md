# 11.01 检索指标与证据标注 / Retrieval metrics and evidence labeling

[返回全书目录 / Contents](../00-contents.md)

检索评估需要问题、相关证据 ID 和相关性定义。对于多跳问题，单个相关节点不代表证据充分。标签可区分支持、部分支持、冲突和无关，并记录是否需要多个节点共同构成答案。标注人员应能查看原文，而不是只看模型生成的参考答案。

Retrieval evaluation needs questions, relevant evidence IDs, and a relevance definition. A single relevant node may be insufficient for multi-hop questions. Label supporting, partially supporting, conflicting, and irrelevant evidence, including jointly necessary sets. Annotators need original sources, not only generated answers.

Recall@k 是前 k 个结果中命中的相关项占全部标注相关项的比例；MRR 关注第一个相关结果的倒数排名；nDCG 可处理分级相关性并惩罚靠后结果。Hit rate 只表示至少命中一项，不能替代多证据覆盖。若相关证据标注不完整，Recall 的分母本身就有偏差。

Recall@k measures retrieved relevant items against all labeled relevant items. MRR uses the reciprocal rank of the first relevant result. nDCG supports graded relevance and rank discounting. Hit rate only asks whether anything relevant appeared and does not measure complete evidence coverage. Incomplete labels bias recall itself.

切块变化会改变节点 ID 与证据粒度。为了跨切块策略比较，可保留来源段落或字符区间标签，再映射到新节点。评测时去重，避免多个重叠块因重复命中被误认为更高覆盖。

Chunking changes node IDs and evidence granularity. Use source passages or spans to map labels across strategies. Deduplicate results so overlapping chunks do not falsely inflate coverage.

## 示例与运行边界 / Example and execution scope

纯 Python 独立算法示例；不调用外部服务。

Standalone pure-Python algorithm example without external services.

```python
def retrieval_metrics(ranking, relevant, k):
    if k <= 0 or not relevant:
        raise ValueError("Positive k and nonempty labels required")
    ranking = list(dict.fromkeys(ranking))
    top = ranking[:k]
    recall = len(set(top) & set(relevant)) / len(set(relevant))
    rr = next((1.0 / rank for rank, item in enumerate(top, 1)
               if item in relevant), 0.0)
    return {"recall_at_k": recall, "reciprocal_rank_at_k": rr}
assert retrieval_metrics(["a", "b", "c"], {"b", "d"}, 3)["recall_at_k"] == 0.5
print(retrieval_metrics(["a", "b", "c"], {"b", "d"}, 3))
```

## 重点与难点 / Key points and difficulties

重点：指标必须对应业务证据充分性。难点：切块变化与不完整标签导致不可比。

Key: metrics must reflect sufficient evidence. Difficulty: changing chunks and incomplete labels undermine comparisons.

## 面试考点与参考回答 / Interview question and answer

问：MRR 高但答案仍差为什么？答：第一个证据排得靠前不表示所有必要证据齐全，也不表示生成忠实。

Q: Why can high MRR coexist with poor answers? A: an early relevant hit does not guarantee complete evidence or faithful generation.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：把重叠块都算独立正确答案，Recall 被人为抬高。处置：按证据单元或来源区间去重并报告多证据覆盖。

Pitfall: counting overlapping chunks as independent evidence inflates recall. Deduplicate by evidence unit or source span.

## 动手实验与验收 / Exercise and acceptance criteria

手算三条查询的 Recall@3 与 MRR，再和下例对照。验收：无相关标签的问题单独分类，不混入普通召回平均。

Hand-calculate Recall@3 and MRR for three queries and compare with the snippet. Acceptance: separately classify queries with no relevant evidence.
