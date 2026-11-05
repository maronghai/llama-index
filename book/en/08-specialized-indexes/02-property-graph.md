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

## Code Implementation Supplement:SimplePropertyGraphStore Entity and Relation Topology Construction

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

Offline fixtures validate interfaces, provenance, and control flow, not semantic quality or security. Real-model branches additionally require `llama-index-llms-openai`, `llama-index-embeddings-openai`, and, for reranking, `llama-index-postprocessor-sbert-rerank`; set `RUN_REAL_MODELS=1`, `OPENAI_API_KEY`, `LLM_MODEL`, and `EMBED_MODEL` as required by the block. External-model branches have not been executed in this revision.

```python
from llama_index.core.graph_stores.simple_labelled import SimplePropertyGraphStore
from llama_index.core.graph_stores.types import EntityNode, Relation

graph_store = SimplePropertyGraphStore()

# 1. 显式创建实体节点 (EntityNode)
e1 = EntityNode(name="Alice", label="ENGINEER", properties={"team": "Core Platform"})
e2 = EntityNode(name="AuthService", label="MICROSERVICE", properties={"tier": "P0"})
graph_store.upsert_nodes([e1, e2])

# 2. 显式建立带属性的关系边 (Relation)
rel = Relation(
    source_id=e1.id,
    target_id=e2.id,
    label="MAINTAINS",
    properties={"oncall": True, "since": "2023"}
)
graph_store.upsert_relations([rel])

# 3. 验证关系检索与图谱拓扑
triplets = graph_store.get_triplets(entity_names=[e1.id])
assert len(triplets) == 1
assert triplets[0][0].name == "Alice"
assert triplets[0][1].label == "MAINTAINS"
assert triplets[0][2].name == "AuthService"

print("PropertyGraphStore successfully verified:")
print(f"- Triplet: ({triplets[0][0].name}) -[{triplets[0][1].label}]-> ({triplets[0][2].name})")

# Keep canonical identity tenant-scoped. Preserve source provenance on every edge.
rel.properties.update({'source_id': 'runbook-v1', 'tenant_id': 'platform'})
graph_store.upsert_relations([rel])
from llama_index.core import PropertyGraphIndex
from llama_index.core.llms import MockLLM
from llama_index.core.indices.property_graph import CustomPGRetriever
class OwnerRetriever(CustomPGRetriever):
    def init(self, **kwargs):
        pass
    def custom_retrieve(self, query_str):
        triples = self.graph_store.get_triplets(entity_names=['Alice'])
        return '\n'.join(f'{a.name} {r.label} {b.name}; source={r.properties.get("source_id")}'
                         for a, r, b in triples)
index = PropertyGraphIndex(nodes=[], property_graph_store=graph_store,
    llm=MockLLM(max_tokens=16), embed_kg_nodes=False, kg_extractors=[])
retriever = index.as_retriever(sub_retrievers=[OwnerRetriever(graph_store=graph_store)])
hits = retriever.retrieve('Who maintains AuthService?')
assert hits and 'AuthService' in hits[0].node.get_content()
assert 'runbook-v1' in hits[0].node.get_content()
print(hits[0].node.get_content())
```

### Architecture and execution boundaries

Connects entities, provenance-bearing relations, PropertyGraphIndex, and a custom graph retriever. Triples are explicitly supplied, not extracted from open-ended text. Production requires tenant-scoped canonical entities, authorized subgraphs, and validated extraction via SimpleLLMPathExtractor or SchemaLLMPathExtractor.
