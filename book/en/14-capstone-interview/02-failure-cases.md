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
