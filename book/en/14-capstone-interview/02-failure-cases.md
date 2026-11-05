# 14.02 Eight recurring failures and their remedies

[返回全书目录 / Contents](../00-contents.md)

Failure one: similar but useless retrieval. Inspect coverage, embedding compatibility, and query constraints before chunking and candidate recall. Failure two: missing exceptions. Check parsing and truncation, try window recovery, and add conditional questions. These failures need distinct diagnoses.

Failure three: duplicated answers after updates. Check source identity, old-node removal, and channel versions. Failure four: content remains after revocation. Check parent nodes, summaries, history, and caches. Cleanup must follow derived dependencies, not only delete one vector.

Failure five: timeouts under load. Inspect queues, pools, concurrency, and provider quotas; apply backpressure. Failure six: cost spikes. Check subquestion fan-out, agent loops, cache invalidation, and duplicate ingestion. Inspect call counts before prices.

Failure seven: imports or arguments break after upgrades. Separate core, integration, and standalone workflow versions and restore a tested set. Failure eight: good metrics but unhappy users. Inspect leakage, synthetic bias, missing-answer coverage, and business constraints; add anonymized real questions and slice-level evaluation.

## Key points and difficulties

Key: start with evidence and recent changes. Difficulty: similar symptoms can have distinct causes; every fix needs regression coverage.

## Interview question and answer

Q: How do you demonstrate debugging ability? A: explain symptoms, hypotheses, observations, elimination, cause, fix, and regression checks.

## Production pitfalls and mitigation

Pitfall: changing models, chunks, and store settings at once. Contain first, then run attributable experiments.

## Exercise and acceptance criteria

Choose two failures and write diagnostic records with falsification conditions. Acceptance: observable evidence for each hypothesis and explicit elimination.

## Implementation supplement: An executable diagnostic triage for eight failure classes

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
def diagnose(s):
    findings = []
    rules = [
        (s["recall"] < 0.7, "retrieval", "inspect corpus, chunks and embeddings"),
        (s["missing_conditions"] > 0, "omitted exceptions", "inspect parsing and context truncation"),
        (s["duplicate_sources"] > 0, "duplicate ingestion", "inspect stable IDs and deletion"),
        (s["unauthorized_hits"] > 0, "authorization leak", "block affected reads and audit derived artifacts"),
        (s["p95_ms"] > 2000, "latency", "inspect queueing, concurrency and provider limits"),
        (s["calls_per_query"] > 8, "cost amplification", "inspect decomposition and agent budgets"),
        (not s["import_ok"], "upgrade regression", "restore tested package set"),
        (s["online_success"] < s["offline_success"] - 0.15, "distribution shift", "evaluate real anonymized query slices"),
    ]
    for condition, symptom, next_step in rules:
        if condition:
            findings.append({"symptom": symptom, "next_step": next_step})
    return findings

sample = dict(recall=0.5, missing_conditions=1, duplicate_sources=2, unauthorized_hits=1,
              p95_ms=3000, calls_per_query=12, import_ok=False, online_success=0.6, offline_success=0.95)
assert len(diagnose(sample)) == 8
print(diagnose(sample))
```

### Implementation, acceptance and production boundaries

Thresholds are instructional; findings suggest investigations, not proven causes. Contain authorization leaks first and retain audit evidence. Connect traces and evaluations, prioritize alerts, and add falsification and regression checks. Do not automatically change models, chunks and storage together.
