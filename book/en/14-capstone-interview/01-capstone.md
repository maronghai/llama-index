# 14.01 An enterprise knowledge base from requirements to acceptance

[返回全书目录 / Contents](../00-contents.md)

The capstone serves regional policies and support knowledge. Users ask about rules, product IDs, and past tickets; administrators publish and withdraw documents. Requirements include citations, tenant and role isolation, versioning, and abstention. Translate them into tests before choosing a vector database.

Stage one creates traceable snapshots and stable Documents. Stage two parses and chunks with pages, headings, and access metadata, then builds dense and BM25 channels. Stage three adds authorization, fusion, reranking, budgeting, generation, and citation checks. Stage four adds evaluation, traces, deletion propagation, and blue-green releases. Establish an acceptable baseline at every stage.

A data contract can include source_id, revision, tenant_id, acl_groups, effective_from, effective_to, deleted, and parser_version. Build manifests bind snapshots, models, chunking, code, and dependencies. Query audits record scoped identity summaries, index versions, and evidence IDs without secrets.

Acceptance covers conditional policies, exact IDs, comparisons, missing answers, conflicts, malicious documents, cross-tenant requests, post-deletion retrieval, and outages. Set thresholds using business risk and measured baselines. This book provides a design, not fabricated success rates.

## Key points and difficulties

Key: trace requirements through contracts, implementation, and tests. Difficulty: preserve access, versions, and deletion semantics at every layer.

## Interview question and answer

Q: How should you present a RAG project? A: cover goals, data, baseline, failures, tradeoffs, paired evaluation, deployment constraints, measured impact, and your responsibilities.

## Production pitfalls and mitigation

Pitfall: presenting a technology list as a design. Explain the failure each component addresses, its cost, verification, and rollback.

## Exercise and acceptance criteria

Create an acceptance matrix and minimal executable path, then populate it with real results. Acceptance: mark unrun items as unverified.
