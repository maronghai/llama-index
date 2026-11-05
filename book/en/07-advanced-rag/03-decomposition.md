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
