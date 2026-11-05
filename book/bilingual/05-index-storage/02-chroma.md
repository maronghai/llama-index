# 05.02 Chroma 集成与集合契约 / Chroma integration and collection contracts

[返回全书目录 / Contents](../00-contents.md)

Chroma 适合本地实验与部分部署场景，但“用了持久化客户端”不等于满足高可用、备份和多租户隔离需求。评估后端应覆盖过滤表达式、删除、批量写入、文本保存、并发模型和运维恢复，不只比较向量查询速度。

Chroma is useful for local experiments and some deployments, but persistence alone does not deliver high availability, backups, or tenant isolation. Compare stores on filtering, deletion, batches, text storage, concurrency, and recovery as well as vector-search latency.

集成需要 chromadb 与 llama-index-vector-stores-chroma。集合应绑定嵌入维度、模型版本、距离度量和元数据模式。维度相同的不同模型也必须分集合或重建。下例使用 MockEmbedding 只说明 StorageContext 接线；实际质量实验应替换为真实且前后一致的模型。

The integration requires chromadb and llama-index-vector-stores-chroma. Bind each collection to embedding dimensions, model revision, metric, and metadata schema. Different models need separate collections or rebuilding even when dimensions match. The snippet uses MockEmbedding only to demonstrate StorageContext wiring.

重新打开已有集合时，是否能直接 from_vector_store 恢复取决于后端是否保存文本与所需元数据。不要假设所有向量库都能用同一恢复步骤。迁移时验证旧文档删除、过滤和引用字段，而不只是比较向量总数。

Restoring through from_vector_store depends on the backend retaining text and required metadata. Recovery is not identical across stores. During migration, verify deletions, filters, and citation fields rather than only counting vectors.

## 示例与运行边界 / Example and execution scope

本节示例按正文所列前置条件运行；部分是组件片段，不构成完整应用。

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

```python
# Requires chromadb and llama-index-vector-stores-chroma.
import chromadb
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
client = chromadb.PersistentClient(path="./chroma_demo")
collection = client.get_or_create_collection("smoke_v1")
store = ChromaVectorStore(chroma_collection=collection)
context = StorageContext.from_defaults(vector_store=store)
index = VectorStoreIndex.from_documents(
    [Document(text="Receipts are required.", id_="policy")],
    storage_context=context, embed_model=MockEmbedding(embed_dim=8),
)
print(len(index.as_retriever(similarity_top_k=1).retrieve("receipts")))
```

## 重点与难点 / Key points and difficulties

重点：集合是带版本的数据契约。难点：框架适配层可能与数据库原生接口在过滤和持久化语义上不同。

Key: collections are versioned data contracts. Difficulty: adapter semantics can differ from native database behavior.

## 面试考点与参考回答 / Interview question and answer

问：为什么要保存模型版本而不仅维度？答：维度只约束形状，模型版本决定语义空间；错配可无报错地降低召回。

Q: Why retain model revision as well as dimensions? A: dimensions constrain shape, while model revision defines semantic coordinates; mismatch can silently degrade retrieval.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：get_or_create_collection 复用了旧集合却换了模型。处置：命名中加入索引版本，并在加载前验证构建清单。

Pitfall: reusing a collection after changing the model. Include index versions in collection naming and validate the manifest before loading.

## 动手实验与验收 / Exercise and acceptance criteria

执行持久化示例后在新进程恢复集合并检索，记录适配器版本。验收：正文与来源字段均恢复，且模型身份匹配。

Restore the example collection in a fresh process and record adapter versions. Acceptance: text and provenance survive and embedding identity matches.
