# 14.03 Priority map and interview communication

[返回全书目录 / Contents](../00-contents.md)

Use three priority tiers. Essentials: Documents and Nodes, explicit configuration, parsing, chunking, vectors, citations, and evaluation. Intermediate: hybrid retrieval, reranking, parent recovery, routing, and updates. Task-dependent: graphs, multiple agents, and multimodality. Establish reliability before adding complexity.

Interview question one: improve retrieval by first validating labels and failure slices, then parsing, embeddings, chunking, candidate fusion, and reranking, with costs. Question two: reduce hallucination by distinguishing missing data, insufficient retrieval, and unsupported generation. Question three: implement incremental sync with stable IDs, hashes, checkpoints, deletion propagation, and reconciliation.

Question four: production readiness requires separate builds, versioned releases, authorization, limits, traces, gates, and rollback. Question five: choose stores by filtering, scale, operations, recovery, tenancy, and team capability. Question six: establish impact using a fixed baseline, split datasets, paired outcomes, failures, and real costs.

Present projects as goals, constraints, baseline, failures, decisions, validation, and results. Clearly identify designs and unmeasured experiments. Technical terms matter only when you can explain their purpose, failure modes, and verification.

## Key points and difficulties

Key: master a reproducible baseline and add advanced patterns in response to failures. Difficulty: turn concepts into verifiable engineering decisions.

## Interview question and answer

Q: What value does LlamaIndex provide? A: common abstractions and integrations for data, nodes, retrieval, synthesis, tools, and workflows, reducing orchestration work while leaving business and production responsibilities to developers.

## Production pitfalls and mitigation

Pitfall: memorizing APIs without tradeoffs. Prepare one failure, experiment, and unsuitable use case for each concept.

## Exercise and acceptance criteria

Present the project in five minutes, then handle half-budget, offline-only, and immediate-revocation constraints. Acceptance: adapt the design without inventing results.
