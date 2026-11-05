# 12.03 Token cost and quality-constrained optimization

[返回全书目录 / Contents](../00-contents.md)

Cost includes generation, embedding, parsing, reranking, storage, networking, and evaluation. Rewriting, routing, subquestions, and judging add calls beyond the final answer. Aggregate through the call tree and separate ingestion costs from online marginal costs.

The estimator below contains no actual prices. Supply input and output prices per million tokens and version the rate table. Billing may include caching, batches, tools, or minimum units; reconcile against provider usage rather than relying solely on local tokenization.

First remove duplicate ingestion and unnecessary calls, then reduce candidates and context, then consider model tiers. Smaller models can handle selected routing or extraction tasks if quality gates hold. Cost per successful task captures errors and retries better than cost per request.

## Example and execution scope

Standalone pure-Python algorithm example without external services.

```python
from decimal import Decimal

def token_cost(input_tokens, output_tokens, input_per_million, output_per_million):
    if min(input_tokens, output_tokens) < 0:
        raise ValueError("Token counts cannot be negative")
    million = Decimal("1000000")
    return (Decimal(input_tokens) * Decimal(str(input_per_million))
            + Decimal(output_tokens) * Decimal(str(output_per_million))) / million
# Supply actual versioned rates; no price is assumed here.
assert token_cost(0, 0, "0", "0") == 0
```

## Key points and difficulties

Key: account for the whole call tree. Difficulty: rate versions, billing reconciliation, and quality preservation.

## Interview question and answer

Q: How can cost fall without material quality loss? A: measure stage costs, remove duplicates, trim irrelevant context, select models by task, and validate regressions.

## Production pitfalls and mitigation

Pitfall: trimming answers while ignoring expensive routing loops. Track all calls and total cost per successful task.

## Exercise and acceptance criteria

Build a cost ledger for routing, retrieval, and generation. Acceptance: distinguish estimates, measured usage, and billed amounts.
