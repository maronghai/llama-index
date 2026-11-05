# 04.02 Metadata, filtering, and content views

[返回全书目录 / Contents](../00-contents.md)

Metadata supports citations, authorization, lifecycle management, and model context. A useful schema includes source_id, tenant_id, document_version, effective_from, language, and heading_path. Define time zones and types, preserve monetary units, and avoid mixed numeric and string representations for the same field.

LlamaIndex can control metadata included in embedding and LLM views through exclusion lists. These views do not delete stored fields and are not authorization controls. Hiding tenant_id from prompts does not prevent cross-tenant retrieval. Enforce access server-side and validate evidence before context assembly.

Model-extracted titles, entities, and summaries can improve retrieval but add cost and errors. Deterministic fields such as IDs, business status, and ACLs must come from trusted systems. Store extracted attributes as derived fields with model and transformation versions.

## Example and execution scope

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

```python
from llama_index.core import Document
from llama_index.core.schema import MetadataMode
doc = Document(
    text="A receipt is required.",
    metadata={"tenant_id": "acme", "heading": "Travel", "internal_path": "private"},
    excluded_embed_metadata_keys=["tenant_id", "internal_path"],
    excluded_llm_metadata_keys=["tenant_id", "internal_path"],
)
print(doc.get_content(metadata_mode=MetadataMode.EMBED))
print(doc.metadata["tenant_id"])
```

## Key points and difficulties

Key: metadata has different uses and trust levels. Difficulty: stored fields, embedding input, and generation context are distinct views.

## Interview question and answer

Q: Why exclude paths from embeddings? A: paths may add noise or sensitive information; semantic fields such as headings may help, so evaluate selectively.

## Production pitfalls and mitigation

Pitfall: trusting client-provided tenant_id as authorization. Derive scope from verified identity and let clients only narrow it.

## Exercise and acceptance criteria

Compare EMBED, LLM, and NONE content views. Acceptance: sensitive paths remain out of model input while tenant_id remains available for trusted filtering.

## Code Implementation Supplement:Metadata Content View Masking and Mandatory Permission Filtering Pipeline

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

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.schema import MetadataMode
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters, FilterOperator

embed_model = MockEmbedding(embed_dim=256)

# 1. 包含敏感信息与权限标签的企业文档
doc = Document(
    text="Confidential Strategy: Launch Project Apollo in Q4.",
    metadata={"tenant_id": "finance", "security": "confidential", "internal_path": "/var/finance/p1.pdf"}
)

# 2. 控制内容视图：排除物理路径与敏感评级进入向量与 LLM 提示词
doc.excluded_embed_metadata_keys = ["internal_path", "security"]
doc.excluded_llm_metadata_keys = ["internal_path"]

embed_view = doc.get_content(MetadataMode.EMBED)
llm_view = doc.get_content(MetadataMode.LLM)

assert "internal_path" not in embed_view and "security" not in embed_view
assert "finance" in embed_view
assert "internal_path" not in llm_view and "security" in llm_view

# 3. 强制权限过滤门禁 (Server-side Filter)
index = VectorStoreIndex.from_documents([doc], embed_model=embed_model)
secure_filters = MetadataFilters(
    filters=[
        MetadataFilter(key="tenant_id", value="finance", operator=FilterOperator.EQ),
        MetadataFilter(key="security", value="confidential", operator=FilterOperator.EQ)
    ]
)
retriever = index.as_retriever(filters=secure_filters, similarity_top_k=1)
results = retriever.retrieve("Project Apollo launch")
assert len(results) == 1
assert results[0].node.metadata["tenant_id"] == "finance"

print("Metadata security views and mandatory filtering successfully verified.")
```

### Architecture and execution boundaries

Demonstrates excluded keys masking sensitive fields from embeddings and LLM prompts while MetadataFilters enforce security gates before retrieval execution.
