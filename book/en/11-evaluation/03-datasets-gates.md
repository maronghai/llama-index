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
