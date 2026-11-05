# 08.02 Property graphs, entity resolution, and graph retrieval

[返回全书目录 / Contents](../00-contents.md)

Graphs suit explicit relationships and multi-hop questions, such as suppliers indirectly dependent on the same part. Evaluate PropertyGraphIndex and compatible graph stores for modern implementations. Historical KnowledgeGraphIndex tutorials are not automatically current recommendations. Check extractors and integrations for the selected release.

Extracting triples is only a start. Define entity types, directions, allowed properties, provenance, and effective dates. Resolve ambiguous names using context and business keys. Extracted edges are not verified facts, and errors can amplify across multiple hops.

Vectors can locate entities and passages, graphs can constrain traversal, and original text can ground the answer. Bound hops, visited nodes, and relationship types. Enforce tenant and access scope on graph edges, not just final text.

## Key points and difficulties

Key: graphs need schema and evidence. Difficulty: entity resolution, temporal relations, and error propagation.

## Interview question and answer

Q: Is graph RAG always better? A: no. Relationship-heavy tasks may benefit, but extraction and maintenance add complexity that needs measured justification.

## Production pitfalls and mitigation

Pitfall: merging names creates false cross-company relationships. Use namespaces and trusted keys; review uncertain matches.

## Exercise and acceptance criteria

Build a small graph with duplicate company names and a two-hop question. Acceptance: separate entities and evidence for every answer path.

## Implementation supplement: An evidence-bearing property graph and bounded traversal

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
from collections import deque

edges = [
    {"src": "org:acme", "rel": "OWNS", "dst": "product:x", "tenant": "a", "evidence": "doc-1"},
    {"src": "product:x", "rel": "USES", "dst": "tech:y", "tenant": "a", "evidence": "doc-2"},
    {"src": "product:x", "rel": "USES", "dst": "secret:z", "tenant": "b", "evidence": "doc-3"},
]

def traverse(start, tenant, max_hops=2):
    queue = deque([(start, 0)])
    visited = {start}
    result = []
    while queue:
        node, depth = queue.popleft()
        if depth >= max_hops:
            continue
        for edge in edges:
            if edge["src"] == node and edge["tenant"] == tenant:
                result.append(edge)
                if edge["dst"] not in visited:
                    visited.add(edge["dst"])
                    queue.append((edge["dst"], depth + 1))
    return result

result = traverse("org:acme", "a")
assert len(result) == 2 and all(e["evidence"] for e in result)
assert all(e["dst"] != "secret:z" for e in result)
print(result)
```

### Implementation, acceptance and production boundaries

This reference traversal is not a PropertyGraphIndex integration test. Entities use namespaced stable IDs and edges carry evidence and tenant ownership. Validate extracted triples, entity resolution and relation types before writing graph storage. Production traversal also needs edge, time and high-degree limits.
