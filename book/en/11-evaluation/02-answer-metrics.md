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

## Implementation supplement: Separate fact correctness from citation support

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
def evaluate(predicted_claims, expected_claims, evidence_facts):
    # Claims are manually normalized facts, not raw generated sentences.
    correct = set(predicted_claims) & set(expected_claims)
    supported = [claim for claim, refs in predicted_claims.items()
                 if refs and all(claim in evidence_facts.get(ref, set()) for ref in refs)]
    return {
        "fact_precision": len(correct) / max(1, len(predicted_claims)),
        "fact_recall": len(correct) / max(1, len(expected_claims)),
        "citation_support": len(supported) / max(1, len(predicted_claims)),
    }

gold = {"hotel_limit=500", "receipts=required"}
evidence = {"p1": {"hotel_limit=500"}, "p2": {"receipts=required"}}
good = evaluate({"hotel_limit=500": ["p1"], "receipts=required": ["p2"]}, gold, evidence)
bad = evaluate({"hotel_limit=800": ["p1"]}, gold, evidence)
assert good == {"fact_precision": 1.0, "fact_recall": 1.0, "citation_support": 1.0}
assert bad["citation_support"] == 0
print({"good": good, "bad": bad})
```

### Implementation, acceptance and production boundaries

Manually annotate atomic facts and evidence for deterministic scoring and judge calibration. Citation support uses a strict rule: every listed reference must support the claim. This is neither natural-language entailment nor a replacement for FaithfulnessEvaluator. Record judge prompts, models, audits and abstention policy.
