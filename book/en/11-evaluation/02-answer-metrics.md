# 11.02 Faithfulness, relevance, and correctness

[返回全书目录 / Contents](../00-contents.md)

Faithfulness asks whether evidence supports the answer. Correctness asks whether the answer satisfies facts or a reference. Relevance asks whether it addresses the question. An answer can faithfully repeat stale policy or be correct from model memory without retrieval support. Report dimensions separately.

LLM judges scale evaluation but depend on prompts, model biases, order, and domain knowledge. Freeze the protocol, blind system identities, manually review representative samples, and version the judge. Evaluators such as FaithfulnessEvaluator are tools, not objective truth guarantees.

Track justified abstention, false refusal, and incorrect answers separately. Accuracy alone can reward refusing everything; answer rate alone can reward invention. Select operating points using risk weights and coverage, especially for consequential facts.

## Key points and difficulties

Key: separate faithfulness, correctness, and relevance. Difficulty: judge bias and abstention tradeoffs.

## Interview question and answer

Q: Is a different answer from the reference necessarily wrong? A: no; check claims, conditions, units, and support rather than wording alone.

## Production pitfalls and mitigation

Pitfall: the same model writes references and judges itself. Use independent labels, varied checks, and disagreement review.

## Exercise and acceptance criteria

Create faithful-but-stale, correct-but-unsupported, and relevant-but-incomplete answers. Acceptance: distinguish their scores and rationales.
