# 05.01 VectorStoreIndex and vector retrieval

[返回全书目录 / Contents](../00-contents.md)

Vector retrieval maps queries and nodes into a compatible representation space and ranks candidates by distance or similarity. Cosine divides the dot product by vector norms; normalized dot-product ranking equals cosine ranking. Euclidean distance normally decreases with closeness, but returned scores may be transformed. Confirm backend semantics before setting cutoffs.

VectorStoreIndex connects nodes with vector storage; it is not a particular database. from_documents builds nodes from documents, while direct node construction requires awareness of existing embeddings. In-memory defaults suit experiments but do not survive restart automatically. Large stores often use approximate search with recall, latency, and memory tradeoffs.

Top-k specifies candidate count, not confidence. Nearest-neighbor search returns something even when the answer is absent. Add evidence-sufficiency checks and abstention. Larger k cannot repair model mismatch, bad indexing, or incorrect authorization filters.

## Example and execution scope

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

## Key points and difficulties

Key: similarity is not probability. Difficulty: approximation, filtering, and candidate counts jointly affect recall.

## Interview question and answer

Q: Does vector retrieval guarantee truth? A: no. It measures representation-level relevance; validity, provenance, and evidence still need checking.

## Production pitfalls and mitigation

Pitfall: interpreting 0.8 as 80% correctness. Calibrate decision thresholds on labeled examples and bind them to a model and backend.

## Exercise and acceptance criteria

Compute cosine on two-dimensional vectors and compare raw versus normalized dot products. Acceptance: explain equal cosine for vectors with the same direction but different magnitudes.
