# 07.02 Routing across sources

[返回全书目录 / Contents](../00-contents.md)

Multi-source systems may include policies, tickets, catalogs, and databases. Routers select suitable retrievers or engines. Tool descriptions should state coverage, time range, language, and supported questions. Selection does not automatically coordinate authorization.

Use deterministic routing for tenant, region, and data type. Semantic selection can classify question intent with a fallback. Single-source routing is cheaper; parallel multi-source retrieval offers coverage at higher cost and conflict risk. Distinguish wrong routing from correct routing to an incomplete source.

Tool names and descriptions may themselves reveal sensitive information. Expose only permitted tools and authorize every call. Log a concise routing rationale rather than attempting to collect hidden model reasoning.

## Key points and difficulties

Key: combine rule-based and semantic routing. Difficulty: fallback, conflicts, and layered permissions.

## Interview question and answer

Q: When should routing be avoided? A: with few affordable sources, parallel retrieval may be simpler; prove routing saves cost without unacceptable recall loss.

## Production pitfalls and mitigation

Pitfall: nearly identical descriptions cause unstable selection. Specify boundaries and test ambiguous questions.

## Exercise and acceptance criteria

Create three sources and 15 routing questions including cross-source cases. Acceptance: a confusion matrix, fallback rate, and explanations for misroutes.
