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

## Implementation supplement: An inspectable multi-source routing baseline

Dependencies: Python 3.10+; install `llama-index-core==0.14.25`.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
from llama_index.core import Document, SummaryIndex
from llama_index.core.llms import MockLLM

llm = MockLLM(max_tokens=16)
engines = {
    "travel": SummaryIndex.from_documents([Document(text="Hotel limit is 500.")]).as_query_engine(llm=llm),
    "leave": SummaryIndex.from_documents([Document(text="Annual leave is 12 days.")]).as_query_engine(llm=llm),
}

def route(question):
    q = question.lower()
    matches = [name for name, terms in {"travel": ("hotel", "travel"), "leave": ("leave", "vacation")}.items()
               if any(term in q for term in terms)]
    return matches[0] if len(matches) == 1 else None

assert route("hotel limit?") == "travel"
assert route("hotel and leave rules?") is None
selected = route("hotel limit?")
response = engines[selected].query("hotel limit?")
assert response.source_nodes
print({"route": selected, "sources": len(response.source_nodes)})
```

### Implementation, acceptance and production boundaries

Rule routing is an interpretable baseline for RouterQueryEngine, not its full replacement. Mixed and unknown questions return None for clarification or multi-source handling. Model selectors still need source allowlists, authorization and routing evaluation. Mock responses verify dispatch only.

First-run note: core tokenization may download an encoding cache. Provision it and set `TIKTOKEN_CACHE_DIR` for offline use. No model key does not imply a network-free first run.

## Code Implementation Supplement:RouterQueryEngine Multi-Tool Intent Routing and Dispatching

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
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors.embedding_selectors import EmbeddingSingleSelector

embed_model = MockEmbedding(embed_dim=256)
llm = MockLLM(max_tokens=32)
Settings.embed_model = embed_model
Settings.llm = llm

# 构建两个不同业务领域的专业知识库
idx_finance = VectorStoreIndex.from_documents(
    [Document(text="Finance: Expense claims must be submitted within 30 days.", id_="fin_1")],
    embed_model=embed_model
)
idx_engineering = VectorStoreIndex.from_documents(
    [Document(text="Engineering: Production deployments freeze every Friday.", id_="eng_1")],
    embed_model=embed_model
)

# 封装为查询引擎工具
tool_finance = QueryEngineTool(
    query_engine=idx_finance.as_query_engine(llm=llm),
    metadata=ToolMetadata(name="finance_tool", description="Answers finance, expense, and budget questions")
)
tool_engineering = QueryEngineTool(
    query_engine=idx_engineering.as_query_engine(llm=llm),
    metadata=ToolMetadata(name="engineering_tool", description="Answers software engineering and deployment questions")
)

# 组装基于语义匹配的单选路由引擎
selector = EmbeddingSingleSelector.from_defaults(embed_model=embed_model)
router = RouterQueryEngine(selector=selector, query_engine_tools=[tool_finance, tool_engineering])

response = router.query("When do deployments freeze for engineering?")
assert response.source_nodes is not None
print("Router successfully dispatched query; sources retrieved:", len(response.source_nodes))

assert {s.node.ref_doc_id for s in response.source_nodes} == {'eng_1'}
finance_response = router.query('finance expense budget')
assert {s.node.ref_doc_id for s in finance_response.source_nodes} == {'fin_1'}
print('Both routing directions verified.')
```

### Architecture and execution boundaries

Hashed lexical embeddings validate both routing directions and source isolation without claiming semantic intent recognition. Use a real embedding encoder or LLMSingleSelector in production, authorize tools before routing, and define fallback for unknown or cross-source questions.
