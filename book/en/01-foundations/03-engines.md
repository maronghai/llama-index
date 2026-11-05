# 01.03 Retrievers, query engines, and chat engines

[返回全书目录 / Contents](../00-contents.md)

A retriever returns candidate evidence. A query engine combines retrieval with response synthesis. A chat engine additionally manages conversational context. These are separate responsibilities. A query call usually does not implicitly retain chat history, although underlying components can still share caches or custom state.

Use as_retriever().retrieve() to isolate evidence selection, then as_query_engine().query() to inspect synthesis. Response source_nodes commonly contain NodeWithScore objects. Scores may be absent, and their meaning depends on the backend; do not assume every score is cosine similarity or transfer cutoffs between stores.

Follow-up questions such as “what about it?” need contextual interpretation. Rewriting must preserve the original intent, authorization scope, and time constraints. History may contain stale answers. Record the original query, rewritten retrieval query, and final citations to locate failures.

## Example and execution scope

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

```python
# Requires an initialized index; this is a component-level snippet.
retriever = index.as_retriever(similarity_top_k=5)
hits = retriever.retrieve("What receipts are required?")
for hit in hits:
    score = "n/a" if hit.score is None else f"{hit.score:.4f}"
    print(score, hit.node.get_content())
response = index.as_query_engine(similarity_top_k=5).query("What receipts are required?")
print(str(response))
```

## Key points and difficulties

Key: test retrieval and generation separately. Difficulty: conversational rewriting must not broaden access or treat prior answers as authoritative evidence.

## Interview question and answer

Q: Should a wrong answer trigger a model upgrade? A: first inspect source nodes. Missing evidence points to data or retrieval; present evidence points to prompts, truncation, conflicts, or generation.

## Production pitfalls and mitigation

Pitfall: formatting a missing score as a float crashes diagnostics. Handle None and log the score definition with the embedding and retrieval configuration.

## Exercise and acceptance criteria

Save retrieved nodes and the final answer for one question. Label evidence sufficiency. Acceptance: propose separate retrieval and generation improvements.
