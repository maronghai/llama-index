# 08.01 SummaryIndex and global questions

[返回全书目录 / Contents](../00-contents.md)

Global questions need broad coverage, unlike local fact lookup. SummaryIndex and summary trees can support coverage at higher processing cost than selective retrieval. Summaries compress detail and should not replace original clauses for precise amounts or exceptions.

Use summary paths for overviews and original nodes for details. Record source-node dependencies and summary versions. Updates and deletions invalidate derived summaries. Hierarchical summarization can accumulate omissions, requiring coverage checks and source review.

Evaluate coverage, consistency, and preservation of rare but critical risks, not just fluency. A short exclusion may matter more than repeated background. Frequency alone does not establish importance.

## Key points and difficulties

Key: distinguish broad coverage from precise facts. Difficulty: dependency invalidation and rare critical details.

## Interview question and answer

Q: Can summary indexes replace vector indexes? A: they support different query patterns; combinations need cost control and traceability.

## Production pitfalls and mitigation

Pitfall: summaries expose deleted policy content. Track dependencies and invalidate or rebuild derived data.

## Exercise and acceptance criteria

Summarize a document with rare major risks. Acceptance: preserve those risks and trace every conclusion to a passage.
