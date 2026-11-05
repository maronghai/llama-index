# 11.01 Retrieval metrics and evidence labeling

[返回全书目录 / Contents](../00-contents.md)

Retrieval evaluation needs questions, relevant evidence IDs, and a relevance definition. A single relevant node may be insufficient for multi-hop questions. Label supporting, partially supporting, conflicting, and irrelevant evidence, including jointly necessary sets. Annotators need original sources, not only generated answers.

Recall@k measures retrieved relevant items against all labeled relevant items. MRR uses the reciprocal rank of the first relevant result. nDCG supports graded relevance and rank discounting. Hit rate only asks whether anything relevant appeared and does not measure complete evidence coverage. Incomplete labels bias recall itself.

Chunking changes node IDs and evidence granularity. Use source passages or spans to map labels across strategies. Deduplicate results so overlapping chunks do not falsely inflate coverage.

## Example and execution scope

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

## Key points and difficulties

Key: metrics must reflect sufficient evidence. Difficulty: changing chunks and incomplete labels undermine comparisons.

## Interview question and answer

Q: Why can high MRR coexist with poor answers? A: an early relevant hit does not guarantee complete evidence or faithful generation.

## Production pitfalls and mitigation

Pitfall: counting overlapping chunks as independent evidence inflates recall. Deduplicate by evidence unit or source span.

## Exercise and acceptance criteria

Hand-calculate Recall@3 and MRR for three queries and compare with the snippet. Acceptance: separately classify queries with no relevant evidence.
