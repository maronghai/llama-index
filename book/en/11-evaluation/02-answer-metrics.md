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

## Code Implementation Supplement:Faithfulness and Relevancy Evaluation Framework and Regression Quality Gates

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

Offline fixtures validate interfaces, provenance, and control flow, not semantic quality or security. Real-model branches additionally require `llama-index-llms-openai`, `llama-index-embeddings-openai`, and, for reranking, `llama-index-postprocessor-sbert-rerank`; set `RUN_REAL_MODELS=1`, `OPENAI_API_KEY`, `LLM_MODEL`, and `EMBED_MODEL` as required by the block. External-model branches have not been executed in this revision.

```python
import asyncio
import os
from llama_index.core.evaluation import FaithfulnessEvaluator, RelevancyEvaluator
from llama_index.core.llms import MockLLM
from llama_index.core.base.llms.types import CompletionResponse

class JudgeFixture(MockLLM):
    # Controlled responses test evaluator plumbing only, not judgement quality.
    verdict: str = 'YES'
    def __init__(self, verdict='YES'):
        super().__init__()
        self.verdict = verdict
    def complete(self, prompt, formatted=False, **kwargs):
        return CompletionResponse(text=self.verdict)
    async def acomplete(self, prompt, formatted=False, **kwargs):
        return self.complete(prompt, formatted, **kwargs)
async def evaluate(judge, answer):
    args = dict(query='How many days of annual leave?', response=answer,
        contexts=['Full-time employees receive 15 days of annual leave.'])
    faith = await FaithfulnessEvaluator(llm=judge).aevaluate(**args)
    relevant = await RelevancyEvaluator(llm=judge).aevaluate(**args)
    return {'faith': faith, 'relevant': relevant}
def gate(result):
    return all(not r.invalid_result and r.passing is True for r in result.values())
async def main():
    good = await evaluate(JudgeFixture(verdict='YES'), '15 days.')
    bad = await evaluate(JudgeFixture(verdict='NO'), 'Free flights for everyone.')
    assert gate(good) and not gate(bad)
    print({k: {'score': v.score, 'passing': v.passing, 'feedback': v.feedback}
           for k, v in bad.items()})
    if os.getenv('RUN_REAL_MODELS') == '1':
        from llama_index.llms.openai import OpenAI
        judge = OpenAI(model=os.environ['LLM_MODEL'], temperature=0, timeout=30)
        for answer in ['15 days.', 'Free flights for everyone.']:
            result = await evaluate(judge, answer)
            print(answer, 'gate=', gate(result), result)
if __name__ == '__main__':
    asyncio.run(main())
```

### Architecture and execution boundaries

Actually calls both evaluators, records score, passing, and feedback, and tests accepting and rejecting gates. A fixed offline judge validates parsing and control flow only, not answer quality. RUN_REAL_MODELS=1 evaluates positive and negative cases with a real judge; compare against human labels and use an independent model to reduce self-evaluation bias.
