# 03.02 LlamaHub 连接器与增量同步 / LlamaHub connectors and incremental synchronization

[返回全书目录 / Contents](../00-contents.md)

远程连接器把 API、数据库或协作文档转换成 Document。连接器目录帮助发现集成，但包名、鉴权方式和 load_data 参数需按具体版本确认。不要把教程中的动态加载示例当成长久稳定的生产依赖；生产代码应显式安装、导入并锁定经过测试的集成。

Remote connectors turn APIs, databases, and collaboration content into Documents. Connector catalogs help discovery, but package names, authentication, and loading arguments must be checked for the selected version. Prefer explicit imports and tested dependencies over assuming a tutorial’s dynamic-loader interface is permanently stable.

同步任务需要处理分页、速率限制、重试、游标、修改时间和删除事件。以 updated_at 为游标时，必须考虑同一时间戳多条记录和迟到更新。使用重叠时间窗加稳定 ID 去重，比单纯“严格大于上次时间”更稳健。只有所有页处理成功并持久化后，才能提交新的检查点。

Synchronization must handle pagination, rate limits, retries, cursors, timestamps, and deletions. Timestamp cursors need a tie-breaker and a policy for late updates. Overlapping time windows plus stable-ID deduplication are safer than a strict timestamp cutoff. Advance checkpoints only after every page is durably processed.

读取权限不等于最终用户访问权限。一个服务账号能看到全公司文档，不代表所有用户都应检索这些文档。连接器应采集 ACL、来源版本和删除标记；下游在查询时重新执行授权。凭据最小化、日志脱敏与定期轮换属于同步设计的一部分。

Connector read access is not end-user authorization. A service account may see company-wide content that individual users cannot. Capture ACLs, source revisions, and tombstones, then enforce access during queries. Least privilege, redacted logs, and credential rotation are part of synchronization design.

## 重点与难点 / Key points and difficulties

重点：稳定 ID、检查点和删除传播。难点：至少一次同步下的幂等，以及半途失败后既不丢数据也不重复发布。

Key: stable IDs, checkpoints, and deletion propagation. Difficulty: idempotent processing under at-least-once delivery without losing data or publishing duplicates.

## 面试考点与参考回答 / Interview question and answer

问：全量同步与增量同步如何配合？答：日常用增量减少成本，周期性全量对账发现漏删、权限漂移和游标缺口；对账结果应可审计。

Q: How should full and incremental sync cooperate? A: incremental runs reduce routine cost; periodic reconciliation detects missed deletions, ACL drift, and cursor gaps with an audit trail.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：429 后立刻无限重试，引发雪崩并重复计费。处置：尊重 Retry-After，指数退避加抖动，限制尝试次数，对永久错误进入人工处理队列。

Pitfall: immediate unlimited retries amplify rate-limit failures. Honor Retry-After, use bounded backoff with jitter, and route permanent failures to a review queue.

## 动手实验与验收 / Exercise and acceptance criteria

模拟三页数据，在第二页失败后重跑。验收：检查点不提前推进、稳定 ID 不重复、删除事件能清理旧节点和缓存。

Simulate three pages and fail the second page. Acceptance: no premature checkpoint, no duplicate IDs, and deletions remove obsolete nodes and caches.

## 代码实现补充 / Implementation supplement: 连接器结果的稳定 ID 与增量对账 / Stable connector IDs and incremental reconciliation

依赖 / Dependencies: Python 3.10+; 仅标准库 / standard library only.

将完整代码保存为独立 `.py` 文件，在独立进程执行 `python filename.py`。无需密钥，无付费调用；验收为断言通过并输出结果。

Save the full block as a standalone `.py` file and run it in a separate process. No API key or paid call is needed; assertions must pass and results are printed.

```python
import hashlib
import json

def digest(row):
    # Include metadata: an ACL change also requires publication.
    payload = json.dumps(row, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()

def reconcile(snapshot, rows):
    ids = [r["source_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate source IDs")
    current = {r["source_id"]: digest(r) for r in rows}
    changed = [r for r in rows if snapshot.get(r["source_id"]) != current[r["source_id"]]]
    removed = sorted(set(snapshot) - set(current))
    return changed, removed, current

first = [{"source_id": "wiki:17", "text": "Limit 500", "tenant": "a"}]
changed, removed, snapshot = reconcile({}, first)
assert len(changed) == 1 and not removed
assert reconcile(snapshot, first)[0] == []
changed, removed, next_snapshot = reconcile(snapshot, [])
assert removed == ["wiki:17"]
print({"deleted": removed})
```

### 实现说明、验收与项目边界 / Implementation, acceptance and production boundaries

把 LlamaHub 读取器的输出转换为此契约，再按 source_id 创建 Document。这里只接受完整、成功的快照；分页失败或仅返回一页时不能把缺失记录判为删除。先完成向量、关键词和缓存更新，最后提交 next_snapshot；真实存储需事务或可恢复检查点。

Normalize LlamaHub reader output to this contract, then create Documents using source_id. Only complete successful snapshots permit deletion detection. A partial page is not a snapshot. Publish vectors, keyword records and cache changes before committing next_snapshot, using transactions or recoverable checkpoints.

## 完整代码实现补充 / Code Implementation Supplement:继承 BaseReader 的增量连接器与哈希校验 / Incremental Connector Subclassing BaseReader with Hash Verification

Python 3.10+；`llama-index-core==0.14.25`。混合检索另需 `llama-index-retrievers-bm25==0.8.0`，SQL 依赖 SQLAlchemy，事件流依赖 `llama-index-workflows`（core 的依赖）。独立进程运行完整代码块；首次 tokenizer 初始化可能读取或下载缓存，请离线部署时预置 `TIKTOKEN_CACHE_DIR`。

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

离线夹具只验证接口、来源和控制流，不验证语义质量或安全性。启用真实模型的分支需额外安装 `llama-index-llms-openai`、`llama-index-embeddings-openai`，重排分支另需 `llama-index-postprocessor-sbert-rerank`；设置 `RUN_REAL_MODELS=1`、`OPENAI_API_KEY`、`LLM_MODEL`、`EMBED_MODEL`（按示例需要）。这些外部模型分支本次未运行。

Offline fixtures validate interfaces, provenance, and control flow, not semantic quality or security. Real-model branches additionally require `llama-index-llms-openai`, `llama-index-embeddings-openai`, and, for reranking, `llama-index-postprocessor-sbert-rerank`; set `RUN_REAL_MODELS=1`, `OPENAI_API_KEY`, `LLM_MODEL`, and `EMBED_MODEL` as required by the block. External-model branches have not been executed in this revision.

```python
import hashlib
from typing import List
from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

class CustomDatabaseReader(BaseReader):
    """企业级数据源连接器：继承 BaseReader，标准化生成 Document"""
    def __init__(self, tenant_id: str):
        super().__init__()
        self.tenant_id = tenant_id

    def load_data(self, records: List[dict]) -> List[Document]:
        documents = []
        for r in records:
            body = "Title: " + r.get("title", "") + "\nContent: " + r.get("content", "")
            content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
            doc = Document(
                text=body,
                id_=f"rec_{r['id']}",
                metadata={
                    "tenant_id": self.tenant_id,
                    "version": r.get("version", 1),
                    "content_hash": content_hash,
                    "category": r.get("category", "general")
                }
            )
            documents.append(doc)
        return documents

# 验证自定义加载器与元数据契约
reader = CustomDatabaseReader(tenant_id="tenant_hr")
records = [
    {"id": "leave_01", "title": "Sick Leave", "content": "Paid sick leave is 10 days.", "version": 2},
    {"id": "leave_02", "title": "Maternity Leave", "content": "Maternity leave is 128 days.", "version": 1}
]
docs = reader.load_data(records)

assert len(docs) == 2
assert docs[0].metadata["tenant_id"] == "tenant_hr"
assert docs[0].metadata["version"] == 2
assert "content_hash" in docs[0].metadata
print("Custom reader loaded docs:", len(docs), "sample hash:", docs[0].metadata["content_hash"][:12])

# Reconcile only a complete, successful snapshot. Never infer deletes from a partial page.
def reconcile(old, documents, complete):
    current = {d.id_: d.metadata['content_hash'] for d in documents}
    changed = [d for d in documents if old.get(d.id_) != current[d.id_]]
    removed = sorted(set(old) - set(current)) if complete else []
    return changed, removed, current

old = {d.id_: d.metadata['content_hash'] for d in docs}
assert not reconcile(old, docs, True)[0]
updated = reader.load_data([dict(records[0], content='Paid sick leave is 12 days.')])
changed, deleted, snapshot = reconcile(old, updated, True)
assert len(changed) == 1 and deleted == ['rec_leave_02']
assert reconcile(old, updated, False)[1] == []
print({'upserts': [d.id_ for d in changed], 'deletes': deleted})
```

### 架构说明与工程边界 / Architecture and execution boundaries

Reader 使用传入记录模拟上游分页结果，不连接真实数据库。完成稳定来源 ID、内容哈希、更新与删除对账；生产中把租户纳入主键，并持久化作业状态，只有完整快照成功才处理删除。

Records simulate upstream pages rather than a real database connection. Stable IDs, hashes, updates, and full-snapshot deletion reconciliation are implemented. Production IDs must include the tenant; persist job state and never infer deletes from incomplete pages.
