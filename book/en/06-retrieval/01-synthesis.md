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
