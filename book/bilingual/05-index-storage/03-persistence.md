# 05.03 StorageContext、更新与灾难恢复 / StorageContext, updates, and disaster recovery

[返回全书目录 / Contents](../00-contents.md)

StorageContext 聚合文档存储、索引存储和向量存储等状态。默认本地存储可以 persist 到目录，再通过 load_index_from_storage 恢复；外部后端可能自行持久化，不受该目录完整覆盖。备份清单必须写明哪些状态在哪个系统，而不是只备份一个文件夹。

StorageContext aggregates document, index, vector, and related storage. Default local storage can be persisted and loaded with load_index_from_storage. External backends may persist independently and are not necessarily captured by that directory. Backup inventories must map every state component to its actual system.

更新需要定义稳定来源 ID、内容版本与节点替换范围。删除文档后还要处理向量、docstore、检索缓存、回答缓存、摘要和派生图数据。具体删除 API 和级联行为依后端而异，应做集成验证。法务删除不能仅靠“下一次全量重建时再处理”。

Updates need stable source IDs, revisions, and defined replacement scopes. Deletions must cover vectors, document stores, retrieval and answer caches, summaries, and derived graphs. API and cascade behavior vary by backend and need integration verification. Legal deletion cannot simply wait for a future rebuild.

恢复演练设置 RPO 与 RTO：允许丢失多少更新，以及多久恢复服务。通过不可变语料快照与配置重建索引可补充数据库备份，但大语料重建时间可能超过 RTO。蓝绿索引切换应保留可回滚版本，并避免将不完整的新版本暴露给查询。

Define recovery point and recovery time objectives: tolerable data loss and restoration duration. Rebuilding from immutable source snapshots complements database backups, but large rebuilds may exceed recovery targets. Blue-green index releases need a rollback target and must not expose incomplete builds.

## 示例与运行边界 / Example and execution scope

本节示例按正文所列前置条件运行；部分是组件片段，不构成完整应用。

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

```python
from llama_index.core import Document, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.embeddings import MockEmbedding
embed = MockEmbedding(embed_dim=8)
index = VectorStoreIndex.from_documents([Document(text="Keep receipts.", id_="p")], embed_model=embed)
index.storage_context.persist(persist_dir="./storage_demo")
context = StorageContext.from_defaults(persist_dir="./storage_demo")
restored = load_index_from_storage(context, embed_model=embed)
assert restored.as_retriever(similarity_top_k=1).retrieve("receipts")
```

## 重点与难点 / Key points and difficulties

重点：完整恢复包含模型配置和所有存储。难点：跨组件一致性，以及删除在派生数据中的传播。

Key: complete recovery includes configuration and all stores. Difficulty: cross-component consistency and deletion propagation.

## 面试考点与参考回答 / Interview question and answer

问：persist 后还需保存什么？答：模型与分块配置、依赖版本、语料快照、外部数据库备份、ACL 版本及发布清单。

Q: What else is needed after persist? A: model and chunking settings, dependencies, source snapshots, external backups, ACL versions, and release manifests.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：恢复成功仅指“索引能加载”，但引用文本已丢失。处置：演练中执行代表性检索、来源定位和权限负例。

Pitfall: declaring recovery successful because loading works while source text is missing. Verify representative queries, citations, and denied-access cases.

## 动手实验与验收 / Exercise and acceptance criteria

运行下例，再模拟删除本地内存对象。验收：恢复后能检索，且清楚区分本地演示与外部数据库恢复。

Run the example and discard in-memory objects. Acceptance: retrieval works after loading, with local persistence clearly distinguished from external database recovery.
