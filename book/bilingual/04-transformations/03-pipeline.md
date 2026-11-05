# 04.03 IngestionPipeline、缓存与幂等 / IngestionPipeline, caching, and idempotency

[返回全书目录 / Contents](../00-contents.md)

IngestionPipeline 按顺序执行 transformations，可组合切块、元数据提取和嵌入。若连接向量库，应确保写入的节点已有适用的向量。离线转换输出节点时可不做嵌入，后续再交给索引。顺序改变会改变产物，不能把转换列表当成无序配置。

IngestionPipeline applies transformations in order, combining chunking, extraction, and embedding. Nodes written to a vector store need suitable embeddings. A pipeline producing only nodes can defer embedding to index construction. Transformation order affects outputs and is part of the build definition.

官方文档说明缓存基于节点与转换组合，文档管理则通过 doc_id 与内容哈希跟踪变化；两者解决不同问题。缓存减少重复计算，稳定 ID 与 docstore 支持重复检测或更新语义。缓存命中不意味着源系统没有删除记录，也不意味着远程向量库和本地状态已事务一致。

Official documentation distinguishes node/transformation caching from document management based on doc_id and hashes. Caching avoids repeated computation; stable IDs and a docstore support duplicate detection and update behavior. Cache hits do not establish deletion completeness or transactional consistency with remote vector storage.

生产摄取将一次构建分为准备、转换、写入、验证和发布。任何一步失败都保留可恢复的作业状态。使用临时索引版本构建，通过验收后切换读指针，比在当前在线集合中边删边写更容易回滚。恢复时同时核对缓存、文档存储和向量存储版本。

A production build separates preparation, transformation, writing, verification, and publication. Persist recoverable job state. Build a new index version and switch readers after validation instead of deleting and rewriting the live collection. Recovery must reconcile cache, document store, and vector store versions.

## 示例与运行边界 / Example and execution scope

本节示例按正文所列前置条件运行；部分是组件片段，不构成完整应用。

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

```python
from llama_index.core import Document
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.embeddings import MockEmbedding
pipeline = IngestionPipeline(transformations=[
    SentenceSplitter(chunk_size=128, chunk_overlap=16),
    MockEmbedding(embed_dim=8),
])
nodes = pipeline.run(documents=[Document(text="A receipt is required.", id_="policy")])
assert nodes and len(nodes[0].embedding) == 8
# No vector_store or docstore is attached: this does not demonstrate database upserts.
```

## 重点与难点 / Key points and difficulties

重点：缓存不等于增量同步，不等于事务。难点：同一文档重跑、修改、删除与部分成功需要不同状态处理。

Key: caching is neither synchronization nor a transaction. Difficulty: retries, edits, deletions, and partial success require distinct handling.

## 面试考点与参考回答 / Interview question and answer

问：为什么 pipeline.persist 后还需要数据库备份？答：本地管道状态不必然包含远程向量数据，恢复必须覆盖所有状态组件。

Q: Why back up the database after pipeline.persist? A: local pipeline state does not necessarily include remote vectors; recovery must cover all state components.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：仅保存缓存，没有保存稳定来源 ID；重跑仍重复写。处置：引入来源主键、内容哈希、作业清单和幂等写入策略。

Pitfall: saving cache without stable source identity still permits duplicate writes. Add source keys, content hashes, job manifests, and idempotent writes.

## 动手实验与验收 / Exercise and acceptance criteria

对同一文档连续运行两次，再修改正文运行第三次，记录节点和向量数量。验收：能够解释实际后端的去重、更新和删除行为。

Run an unchanged document twice and an edited document once. Track node and vector counts. Acceptance: explain the actual backend’s deduplication, update, and deletion behavior.
