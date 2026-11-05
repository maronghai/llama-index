# 06.01 Response synthesis, citations, and abstention

[返回全书目录 / Contents](../00-contents.md)

Retrievers supply candidates, node postprocessors filter or rerank them, and response synthesizers generate within a context budget. Refine may revise an answer across chunks; compact packs context first; tree_summarize combines summaries hierarchically. Actual calls also depend on context length and model limits.

Prompts should define the task, evidence boundaries, conflict handling, and abstention. “Use only context” helps but is not a guarantee. Associate important claims with supporting passages. source_nodes shows what material was supplied, not that every generated sentence is entailed by it. Citation access must also be authorized.

Abstain or request missing constraints when evidence is insufficient. Resolve conflicts using authority and effective dates; if unresolved, disclose the conflict and cite both sides. Do not override explicit internal rules with model background knowledge. Validate critical amounts, dates, and identifiers deterministically where possible.

## Key points and difficulties

Key: a source list is not claim-level support. Difficulty: conflicts, exceptions, and truncation need more than a prompt.

## Interview question and answer

Q: Can RAG hallucinate? A: yes, from wrong retrieval, insufficient or truncated context, or unsupported generation. Use layered checks and abstention.

## Production pitfalls and mitigation

Pitfall: citing a whole PDF leaves claims unverifiable. Retain passage/page mappings and check that granular citations support the answer.

## Exercise and acceptance criteria

Create answerable, unanswerable, and version-conflict questions. Acceptance: grounded answer, abstention, and disclosed conflict respectively.

## Implementation supplement: Conservative answers with evidence IDs

Dependencies: Python 3.10+; install `llama-index-core==0.14.25`.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
from llama_index.core.schema import TextNode, NodeWithScore

def answer(question, hits, allowed_ids):
    trusted = [h for h in hits if h.node.node_id in allowed_ids]
    if not trusted:
        return {"answer": "Insufficient evidence", "citations": []}
    # Extractive baseline: do not invent a claim not in evidence.
    return {"answer": trusted[0].node.text,
            "citations": [trusted[0].node.node_id]}

node = TextNode(id_="policy-2-p3", text="Hotel allowance is CNY 500 per night.")
hits = [NodeWithScore(node=node, score=0.9)]
result = answer("Hotel allowance?", hits, {"policy-2-p3"})
assert result["citations"] == ["policy-2-p3"]
assert answer("Hotel allowance?", hits, set())["citations"] == []
print(result)
```

### Implementation, acceptance and production boundaries

This post-retrieval extractive baseline exposes a service signature; question is not used for relevance checking. Retrieval and relevance gates must run first. A generative synthesizer may replace extraction, but citation IDs must come from authorized evidence and support each claim. Nonempty evidence is not sufficient evidence.

First-run note: core tokenization may download an encoding cache. Provision it and set `TIKTOKEN_CACHE_DIR` for offline use. No model key does not imply a network-free first run.
