# 11.03 Synthetic data, leakage, and regression gates

[返回全书目录 / Contents](../00-contents.md)

Synthetic questions broaden coverage but often mirror source wording and underestimate ambiguity or false premises. Track synthetic, anonymized real, and adversarial questions separately. Include missing answers, conflicts, languages, access denials, table calculations, and long-context boundaries.

Split by source, time, or entity to avoid near-duplicate leakage. Tune on development data and reserve the test set for confirmation. Turn real failures into regression cases while retaining ordinary traffic coverage.

Release gates should cover quality, authorization, performance, cost, and recovery. Set non-regression rules for high-risk slices. Compare paired outcomes and inspect wins and regressions. Small samples do not support strong claims from tiny percentage changes.

## Key points and difficulties

Key: include negative and failure cases. Difficulty: leakage, distribution shifts, and small-sample uncertainty.

## Interview question and answer

Q: How do you establish an improvement? A: freeze baseline and data, change one main factor, compare paired results, and report slices, cost, and regressions.

## Production pitfalls and mitigation

Pitfall: repeated tuning against the test set inflates performance. Keep a sealed holdout and version tuning decisions.

## Exercise and acceptance criteria

Design a 50-question evaluation and gate table, labeling targets as proposed rather than measured. Acceptance: every gate has an owner and failure response.

## Implementation supplement: Source-grouped splitting and regression gates

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
import hashlib

rows = [{"source_id": "doc-" + str(i), "question": "q" + str(i)} for i in range(30)]
def bucket(source_id):
    return int(hashlib.sha256(source_id.encode()).hexdigest()[:8], 16) % 10
train = [r for r in rows if bucket(r["source_id"]) < 7]
test = [r for r in rows if bucket(r["source_id"]) >= 7]
assert train and test
assert not ({r["source_id"] for r in train} & {r["source_id"] for r in test})

def release_gate(metrics):
    return (metrics["recall_at_5"] >= 0.9 and metrics["unauthorized_hits"] == 0
            and metrics["p95_ms"] <= 1800)

assert release_gate({"recall_at_5": 0.93, "unauthorized_hits": 0, "p95_ms": 1500})
assert not release_gate({"recall_at_5": 0.99, "unauthorized_hits": 1, "p95_ms": 100})
print({"train": len(train), "test": len(test), "gate": "passed example assertions"})
```

### Implementation, acceptance and production boundaries

Questions from the same source stay in one partition. Near-duplicate sources still need clustering, and temporal holdouts should cover unanswerable, conflicting and permission-sensitive cases. Gate metrics here are synthetic inputs, not measured system results; report slice sizes and uncertainty.
