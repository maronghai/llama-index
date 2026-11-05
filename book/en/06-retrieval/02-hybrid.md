# 06.02 BM25, dense retrieval, and RRF

[返回全书目录 / Contents](../00-contents.md)

BM25 matches terms and is useful for identifiers, rare terminology, and exact names. Dense embeddings handle semantic paraphrases but may confuse nearby numbers. Hybrid retrieval combines candidates from both channels. Chinese BM25 requires suitable tokenization and domain handling; an English default is not a valid Chinese baseline.

Reciprocal rank fusion sums 1/(c+rank), with ranks starting at one. Ranking avoids directly adding incompatible BM25 and vector scores, but channel weights, candidate counts, and deduplication keys still matter. Tune on development data rather than repeatedly optimizing against the final test set.

Maintain authorization through both channels. Different corpus versions can reintroduce deleted or stale content. Align candidates using stable node IDs and retain channel, original rank, and fused score. String-only deduplication can incorrectly merge evidence with different provenance or exceptions.

## Example and execution scope

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

## Key points and difficulties

Key: sparse and dense methods complement each other; RRF combines ranks. Difficulty: Chinese tokenization, stable identity, and synchronized corpora.

## Interview question and answer

Q: Why not add BM25 and cosine scores directly? A: their scales differ. Use rank fusion or learned calibration.

## Production pitfalls and mitigation

Pitfall: tiny candidate pools exclude the right evidence before fusion. Measure candidate recall before tuning fusion and reranking.

## Exercise and acceptance criteria

Compare channels and fusion on identifiers, synonyms, and mixed-language questions. Acceptance: show unique wins and fusion failures, not just an aggregate claim.
