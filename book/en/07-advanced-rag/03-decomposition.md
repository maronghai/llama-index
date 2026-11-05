# 07.03 Question decomposition and multi-document comparison

[返回全书目录 / Contents](../00-contents.md)

A multi-company revenue comparison contains entities, years, and calculations. Decomposition retrieves individual facts before synthesis. Sub-question patterns support this workflow, but plans can omit requirements or add assumptions and therefore need validation.

Retain units, periods, provenance, and missingness for each result. Fiscal and calendar years or consolidated and standalone figures are not directly comparable. Align structured facts before deterministic growth calculations; zero denominators and missing values require explicit unavailable results.

Parallel independent questions can reduce critical-path latency while increasing concurrency and cost. Bound task duration, step duration, question count, and partial-failure behavior. Clearly distinguish complete conclusions from observations based on incomplete evidence.

## Key points and difficulties

Key: separate planning, extraction, computation, and synthesis. Difficulty: aligning units and reporting periods.

## Interview question and answer

Q: How do you prevent decomposition drift? A: convert requirements into a checklist, validate sub-question coverage, and verify final coverage.

## Production pitfalls and mitigation

Pitfall: failed subqueries become zeros in calculations. Preserve missingness and reject incomplete computation.

## Exercise and acceptance criteria

Compare reports with different periods. Acceptance: reject incompatible comparisons, obtain aligned facts, then calculate with citations.

## Implementation supplement: Budgeted sub-question planning and aggregation

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Task:
    source: str
    question: str

facts = {"a": {"hotel": 500}, "b": {"hotel": 650}}

def execute_plan(tasks, authorized, max_calls=3):
    if len(tasks) > max_calls:
        raise ValueError("plan exceeds call budget")
    results = []
    for task in tasks:
        if task.source not in authorized:
            raise PermissionError(task.source)
        value = facts.get(task.source, {}).get(task.question)
        results.append({"source": task.source, "value": value, "ok": value is not None})
    return results

plan = [Task("a", "hotel"), Task("b", "hotel")]
rows = execute_plan(plan, {"a", "b"})
assert all(r["ok"] for r in rows)
difference = rows[1]["value"] - rows[0]["value"]
assert difference == 150
print({"evidence": rows, "difference": difference})
```

### Implementation, acceptance and production boundaries

A manual plan separates decomposition quality from execution reliability. With SubQuestionQueryEngine, validate generated plans against source authorization, call and time budgets. Missing values are failures, not zero; align units, currencies and effective dates before comparison.
