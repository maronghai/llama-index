# 04.02 元数据、过滤与内容视图 / Metadata, filtering, and content views

[返回全书目录 / Contents](../00-contents.md)

元数据同时服务来源引用、权限过滤、生命周期管理和模型理解。建议最小模式包含 source_id、tenant_id、document_version、effective_from、language 和 heading_path。时间字段应约定时区和类型，金额字段保留单位；不要让同一个字段在不同记录中一会儿是数字一会儿是字符串。

Metadata supports citations, authorization, lifecycle management, and model context. A useful schema includes source_id, tenant_id, document_version, effective_from, language, and heading_path. Define time zones and types, preserve monetary units, and avoid mixed numeric and string representations for the same field.

LlamaIndex 可以分别控制嵌入和生成时包含哪些元数据。excluded_embed_metadata_keys 和 excluded_llm_metadata_keys 影响内容视图，不会自动删除数据库中的字段，也不是访问控制。隐藏 tenant_id 不会阻止跨租户检索；授权必须在可信服务端过滤，并在上下文组装前再次校验。

LlamaIndex can control metadata included in embedding and LLM views through exclusion lists. These views do not delete stored fields and are not authorization controls. Hiding tenant_id from prompts does not prevent cross-tenant retrieval. Enforce access server-side and validate evidence before context assembly.

模型抽取标题、实体和摘要可提高检索，但会引入成本与错误。确定性字段如文件 ID、业务状态和 ACL 应来自可信源，不能由模型推断。抽取结果保存为派生字段，保留生成模型和提取版本，便于重新处理。

Model-extracted titles, entities, and summaries can improve retrieval but add cost and errors. Deterministic fields such as IDs, business status, and ACLs must come from trusted systems. Store extracted attributes as derived fields with model and transformation versions.

## 示例与运行边界 / Example and execution scope

本节示例按正文所列前置条件运行；部分是组件片段，不构成完整应用。

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

## 重点与难点 / Key points and difficulties

重点：元数据有不同用途与信任等级。难点：存储字段、嵌入内容和模型上下文不是同一份视图。

Key: metadata has different uses and trust levels. Difficulty: stored fields, embedding input, and generation context are distinct views.

## 面试考点与参考回答 / Interview question and answer

问：为什么排除文件路径进入嵌入？答：路径可能引入噪声或敏感信息；但标题等语义字段可能有益，应按评估决定而不是全部删除。

Q: Why exclude paths from embeddings? A: paths may add noise or sensitive information; semantic fields such as headings may help, so evaluate selectively.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：将客户端传入的 tenant_id 直接当授权过滤条件。处置：从已验证身份推导允许范围，客户端只能在该范围内收窄条件。

Pitfall: trusting client-provided tenant_id as authorization. Derive scope from verified identity and let clients only narrow it.

## 动手实验与验收 / Exercise and acceptance criteria

比较 MetadataMode.EMBED、LLM 和 NONE 的正文视图。验收：敏感路径不进入模型，tenant_id 仍存在于存储并用于服务端过滤。

Compare EMBED, LLM, and NONE content views. Acceptance: sensitive paths remain out of model input while tenant_id remains available for trusted filtering.

## 完整代码实现补充 / Code Implementation Supplement:元数据内容视图脱敏与强制权限过滤全链路 / Metadata Content View Masking and Mandatory Permission Filtering Pipeline

Python 3.10+；`llama-index-core==0.14.25`。混合检索另需 `llama-index-retrievers-bm25==0.8.0`，SQL 依赖 SQLAlchemy，事件流依赖 `llama-index-workflows`（core 的依赖）。独立进程运行完整代码块；首次 tokenizer 初始化可能读取或下载缓存，请离线部署时预置 `TIKTOKEN_CACHE_DIR`。

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

离线夹具只验证接口、来源和控制流，不验证语义质量或安全性。启用真实模型的分支需额外安装 `llama-index-llms-openai`、`llama-index-embeddings-openai`，重排分支另需 `llama-index-postprocessor-sbert-rerank`；设置 `RUN_REAL_MODELS=1`、`OPENAI_API_KEY`、`LLM_MODEL`、`EMBED_MODEL`（按示例需要）。这些外部模型分支本次未运行。

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

### 架构说明与工程边界 / Architecture and execution boundaries

演示 excluded_embed_metadata_keys 与 excluded_llm_metadata_keys 控制内容视图，配合 MetadataFilters 在检索执行前完成硬性权限门禁。

Demonstrates excluded keys masking sensitive fields from embeddings and LLM prompts while MetadataFilters enforce security gates before retrieval execution.
