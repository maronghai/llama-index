# 08.02 属性图、实体消歧与图检索 / Property graphs, entity resolution, and graph retrieval

[返回全书目录 / Contents](../00-contents.md)

图索引适合关系明确、需要多跳解释的问题，例如“哪些供应商间接依赖同一零件”。现代方案应考察 PropertyGraphIndex 与相应图存储集成；历史 KnowledgeGraphIndex 教程不能直接当作当前推荐接口。具体抽取器、图存储和向量组合需按所选版本核对。

Graphs suit explicit relationships and multi-hop questions, such as suppliers indirectly dependent on the same part. Evaluate PropertyGraphIndex and compatible graph stores for modern implementations. Historical KnowledgeGraphIndex tutorials are not automatically current recommendations. Check extractors and integrations for the selected release.

抽取三元组或属性关系只是起点。需要定义实体类型、关系方向、允许属性、来源证据和生效时间。“Apple”是公司还是水果要通过上下文与业务主键消歧。模型抽取的关系不是已验证事实；错误边经过多跳传播可能放大误导。

Extracting triples is only a start. Define entity types, directions, allowed properties, provenance, and effective dates. Resolve ambiguous names using context and business keys. Extracted edges are not verified facts, and errors can amplify across multiple hops.

图与向量可互补：向量定位相关实体与段落，图约束关系遍历，再返回原文支撑答案。限制跳数、节点数和路径类型，避免无界遍历。图中每条边也要执行租户和权限检查，不能只过滤最终文本。

Vectors can locate entities and passages, graphs can constrain traversal, and original text can ground the answer. Bound hops, visited nodes, and relationship types. Enforce tenant and access scope on graph edges, not just final text.

## 重点与难点 / Key points and difficulties

重点：图结构需要模式与证据。难点：实体消歧、时态关系和错误传播。

Key: graphs need schema and evidence. Difficulty: entity resolution, temporal relations, and error propagation.

## 面试考点与参考回答 / Interview question and answer

问：Graph RAG 总比向量 RAG 好吗？答：不。关系密集任务可能受益，但抽取、维护和查询更复杂，应比较质量收益与成本。

Q: Is graph RAG always better? A: no. Relationship-heavy tasks may benefit, but extraction and maintenance add complexity that needs measured justification.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：同名实体合并导致跨公司关系。处置：使用来源命名空间与可信主键，低置信匹配进入审核。

Pitfall: merging names creates false cross-company relationships. Use namespaces and trusted keys; review uncertain matches.

## 动手实验与验收 / Exercise and acceptance criteria

建立含同名公司的小图，设计两跳问题。验收：不会错误合并实体，每条答案路径可定位原始证据。

Build a small graph with duplicate company names and a two-hop question. Acceptance: separate entities and evidence for every answer path.

## 代码实现补充 / Implementation supplement: 有证据的属性图与受限遍历 / An evidence-bearing property graph and bounded traversal

依赖 / Dependencies: Python 3.10+; 仅标准库 / standard library only.

将完整代码保存为独立 `.py` 文件，在独立进程执行 `python filename.py`。无需密钥，无付费调用；验收为断言通过并输出结果。

Save the full block as a standalone `.py` file and run it in a separate process. No API key or paid call is needed; assertions must pass and results are printed.

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

### 实现说明、验收与项目边界 / Implementation, acceptance and production boundaries

这是属性图检索的参考算法，不是 PropertyGraphIndex 集成测试。实体使用命名空间稳定 ID，关系携带证据与租户。真实抽取器输出三元组后必须校验实体消歧、关系类型与证据，再写入 PropertyGraphIndex 的图存储；生产遍历还要限制边数、时间与高出度节点。

This reference traversal is not a PropertyGraphIndex integration test. Entities use namespaced stable IDs and edges carry evidence and tenant ownership. Validate extracted triples, entity resolution and relation types before writing graph storage. Production traversal also needs edge, time and high-degree limits.

## 完整代码实现补充 / Code Implementation Supplement:SimplePropertyGraphStore 实体与属性关系图完整构建与拓扑遍历 / SimplePropertyGraphStore Entity and Relation Topology Construction

Python 3.10+；`llama-index-core==0.14.25`。混合检索另需 `llama-index-retrievers-bm25==0.8.0`，SQL 依赖 SQLAlchemy，事件流依赖 `llama-index-workflows`（core 的依赖）。独立进程运行完整代码块；首次 tokenizer 初始化可能读取或下载缓存，请离线部署时预置 `TIKTOKEN_CACHE_DIR`。

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

离线夹具只验证接口、来源和控制流，不验证语义质量或安全性。启用真实模型的分支需额外安装 `llama-index-llms-openai`、`llama-index-embeddings-openai`，重排分支另需 `llama-index-postprocessor-sbert-rerank`；设置 `RUN_REAL_MODELS=1`、`OPENAI_API_KEY`、`LLM_MODEL`、`EMBED_MODEL`（按示例需要）。这些外部模型分支本次未运行。

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

### 架构说明与工程边界 / Architecture and execution boundaries

完成实体、边、来源属性、PropertyGraphIndex 与自定义图检索器连接；本例显式写入三元组，未实现开放域实体抽取。生产需要先做租户级实体消歧，在进入图遍历前限制可访问子图，并采用 SimpleLLMPathExtractor 或 SchemaLLMPathExtractor 抽取与校验。

Connects entities, provenance-bearing relations, PropertyGraphIndex, and a custom graph retriever. Triples are explicitly supplied, not extracted from open-ended text. Production requires tenant-scoped canonical entities, authorized subgraphs, and validated extraction via SimpleLLMPathExtractor or SchemaLLMPathExtractor.
