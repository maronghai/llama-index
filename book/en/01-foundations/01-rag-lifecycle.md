# 01.01 The RAG lifecycle and system boundaries

[返回全书目录 / Contents](../00-contents.md)

RAG extends the evidence available to a model beyond its parameters. The offline path loads, parses, chunks, embeds, and publishes data. The online path authenticates callers, retrieves and reranks evidence, assembles context, and generates answers. Evaluation spans both paths. LlamaIndex organizes these components; correctness, authorization, and answer quality remain application responsibilities.

For a travel-policy question, the system must establish the applicable region, employee group, and effective date before selecting evidence. Semantic similarity alone may return last year’s rules or another region’s policy. Separating similarity from applicability is the first production design decision.

Expose observable boundaries: source snapshots, normalized documents, nodes, index releases, retrieval results, and final answers. Record input versions and latency at each boundary. Diagnose failures by asking whether the source contained the answer, parsing preserved it, retrieval found it, and generation used it faithfully.

## Key points and difficulties

Key: separate offline construction from online queries. Difficulty: distinguish source coverage, retrieval quality, and generation faithfulness instead of hiding all failures behind one accuracy number.

## Interview question and answer

Q: RAG or fine-tuning? A: retrieval suits changing knowledge and cited answers; fine-tuning may improve stable behavior or output style. They can be combined. Fine-tuning does not replace live authorization or knowledge updates.

## Production pitfalls and mitigation

Pitfall: shipping chat before governing data makes every correction expensive. Assign stable IDs, versions, provenance, and access scopes from the beginning, and include unanswerable questions in the dataset.

## Exercise and acceptance criteria

Draw both paths of a policy assistant and specify inputs, outputs, and failures at six boundaries. Acceptance: clearly distinguish ingestion loss, retrieval misses, and unsupported generation.
