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

## Implementation supplement: A minimal knowledge base with authorization and citations

Dependencies: Python 3.10+; install `llama-index-core==0.14.25`.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
from llama_index.core import VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.schema import TextNode

nodes = [
    TextNode(id_="a-policy", text="Hotel allowance is CNY 500 per night.", metadata={"tenant": "a"}),
    TextNode(id_="b-policy", text="Hotel allowance is CNY 900 per night.", metadata={"tenant": "b"}),
]
# Separate indexes make tenant isolation explicit for this tiny example.
indexes = {tenant: VectorStoreIndex([n for n in nodes if n.metadata["tenant"] == tenant],
                                  embed_model=MockEmbedding(embed_dim=8))
           for tenant in {"a", "b"}}

def ask(authenticated_tenant, question):
    index = indexes.get(authenticated_tenant)
    if index is None:
        return {"answer": "Insufficient evidence", "citations": []}
    hits = index.as_retriever(similarity_top_k=1).retrieve(question)
    hits = [h for h in hits if h.node.metadata["tenant"] == authenticated_tenant]
    if not hits:
        return {"answer": "Insufficient evidence", "citations": []}
    return {"answer": hits[0].node.text, "citations": [hits[0].node.node_id]}

result = ask("a", "hotel allowance?")
assert result["citations"] == ["a-policy"] and "900" not in result["answer"]
assert ask("unknown", "hotel allowance?")["citations"] == []
print(result)
```

### Implementation, acceptance and production boundaries

Start with provenance and authorization in a single-file loop before separating ingestion and serving. This deliberately returns source text; mock vectors cannot support semantic abstention, so irrelevant in-tenant questions may still retrieve a policy. Add real embeddings, relevance and unanswerable evaluation, revisions, deletion, persistence, tracing and release gates.

First-run note: core tokenization may download an encoding cache. Provision it and set `TIKTOKEN_CACHE_DIR` for offline use. No model key does not imply a network-free first run.

## Code Implementation Supplement:End-to-End Multi-Tenant Enterprise Knowledge Base Architecture

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

Offline fixtures validate interfaces, provenance, and control flow, not semantic quality or security. Real-model branches additionally require `llama-index-llms-openai`, `llama-index-embeddings-openai`, and, for reranking, `llama-index-postprocessor-sbert-rerank`; set `RUN_REAL_MODELS=1`, `OPENAI_API_KEY`, `LLM_MODEL`, and `EMBED_MODEL` as required by the block. External-model branches have not been executed in this revision.

```python
import hashlib
import math
import re
from llama_index.core.embeddings import MockEmbedding as _MockEmbedding

class MockEmbedding(_MockEmbedding):
    # Test-only hashed lexical vectors; NOT a semantic embedding model.
    def _vector(self, text):
        values = [0.0] * 256
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            slot = int(hashlib.sha256(word.encode()).hexdigest()[:8], 16) % 256
            values[slot] += 1.0
        norm = math.sqrt(sum(v*v for v in values)) or 1.0
        return [v / norm for v in values]
    def _get_text_embedding(self, text):
        return self._vector(text)
    def _get_query_embedding(self, query):
        return self._vector(query)
    async def _aget_query_embedding(self, query):
        return self._vector(query)

from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.llms import MockLLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters, FilterOperator

embed_model = MockEmbedding(embed_dim=256)
llm = MockLLM(max_tokens=64)
Settings.embed_model = embed_model
Settings.llm = llm

# 1. 注入多租户企业异构知识库文档
raw_docs = [
    Document(
        text="Finance Dept: International business flights require VP pre-approval.",
        id_="fin_policy_01",
        metadata={"tenant_id": "finance", "classification": "internal"}
    ),
    Document(
        text="HR Dept: Standard employee probation period is exactly 3 months.",
        id_="hr_policy_01",
        metadata={"tenant_id": "hr", "classification": "public"}
    )
]

# 2. 规范化分块切分与向量索引构建
nodes = SentenceSplitter(chunk_size=64, chunk_overlap=8).get_nodes_from_documents(raw_docs)
index = VectorStoreIndex(nodes, embed_model=embed_model)

# 3. 生产级鉴权安全沙箱检索函数
def secure_enterprise_search(caller_tenant: str, query_text: str) -> dict:
    mandatory_filters = MetadataFilters(
        filters=[MetadataFilter(key="tenant_id", value=caller_tenant, operator=FilterOperator.EQ)]
    )
    retriever = index.as_retriever(filters=mandatory_filters, similarity_top_k=2)
    hits = retriever.retrieve(query_text)
    
    # 强制来源证据审计记录
    audit_trail = [
        {"node_id": h.node.node_id, "doc_id": h.node.ref_doc_id, "tenant": h.node.metadata.get("tenant_id")}
        for h in hits
    ]
    return {"query": query_text, "hits_count": len(hits), "audit": audit_trail}

# 验证防越权安全门禁：Finance 租户发起检索，绝不可命中 HR 文档
fin_result = secure_enterprise_search("finance", "What is the policy?")
assert fin_result["hits_count"] > 0
assert all(item["tenant"] == "finance" for item in fin_result["audit"])

print("Enterprise capstone knowledge base successfully verified:")
print(f"- Caller: finance | Retrieved hits: {fin_result['hits_count']}")
print(f"- Audit verification: all hits strictly belong to 'finance' tenant.")

assert secure_enterprise_search('unknown_tenant', 'policy')['hits_count'] == 0
hr_result = secure_enterprise_search('hr', 'probation')
assert hr_result['hits_count'] and all(x['tenant'] == 'hr' for x in hr_result['audit'])
# Only a trusted authentication layer may supply caller_tenant.
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.tools import FunctionTool

def answer_for_verified_identity(tenant, question):
    filters = MetadataFilters(filters=[MetadataFilter(key='tenant_id', value=tenant)])
    evidence = index.as_retriever(filters=filters, similarity_top_k=2).retrieve(question)
    assert all(h.node.metadata['tenant_id'] == tenant for h in evidence)
    if not evidence:
        return {'status': 'no_evidence', 'sources': []}
    response = get_response_synthesizer(llm=llm).synthesize(query=question, nodes=evidence)
    return {'status': 'ok', 'answer': str(response),
            'sources': [s.node.ref_doc_id for s in response.source_nodes]}
result = answer_for_verified_identity('finance', 'business flights')
assert result['sources'] == ['fin_policy_01']
assert answer_for_verified_identity('missing', 'probation')['status'] == 'no_evidence'
# Bind identity in the service closure; never expose tenant as an LLM tool argument.
def finance_tool(question: str) -> dict:
    return answer_for_verified_identity('finance', question)
tool = FunctionTool.from_defaults(fn=finance_tool)
print(result)
```

### Architecture and execution boundaries

An executable multi-tenant RAG vertical slice, not a complete production system. Tests both isolation directions, unknown tenants, authorization rechecks, synthesis, and citations; tool identity is server-bound. Deployment still needs authentication, persistence, queues, rate limits, deletion, and redacted audits. MockLLM output cannot validate answer accuracy.
