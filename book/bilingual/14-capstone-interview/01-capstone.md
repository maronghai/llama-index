# 14.01 从需求到可验收的企业知识库 / An enterprise knowledge base from requirements to acceptance

[返回全书目录 / Contents](../00-contents.md)

项目场景是一家多地区企业的制度与客服知识库。用户询问政策、产品编号和工单经验；管理人员发布制度并撤回过期文件。系统必须提供引用、按租户与角色隔离、说明版本、在无答案时拒答。先把这些需求转成测试，而不是先选择向量数据库。

The capstone serves regional policies and support knowledge. Users ask about rules, product IDs, and past tickets; administrators publish and withdraw documents. Requirements include citations, tenant and role isolation, versioning, and abstention. Translate them into tests before choosing a vector database.

第一阶段准备可追溯语料快照和来源清单，以稳定 ID 导入 Document。第二阶段解析与切块，保存页码、标题和权限；建立向量与 BM25 双通道。第三阶段实现服务端授权、候选融合、重排、上下文预算、生成与引用核验。第四阶段加入评估、追踪、删除传播与蓝绿发布。每阶段先获得可验收基线再增加复杂架构。

Stage one creates traceable snapshots and stable Documents. Stage two parses and chunks with pages, headings, and access metadata, then builds dense and BM25 channels. Stage three adds authorization, fusion, reranking, budgeting, generation, and citation checks. Stage four adds evaluation, traces, deletion propagation, and blue-green releases. Establish an acceptable baseline at every stage.

数据契约建议包含 source_id、revision、tenant_id、acl_groups、effective_from、effective_to、deleted 和 parser_version。构建清单绑定快照、模型、分块、代码和依赖版本。查询审计记录身份范围摘要、索引版本和返回证据 ID，不记录明文密钥。

A data contract can include source_id, revision, tenant_id, acl_groups, effective_from, effective_to, deleted, and parser_version. Build manifests bind snapshots, models, chunking, code, and dependencies. Query audits record scoped identity summaries, index versions, and evidence IDs without secrets.

验收表至少覆盖：带条件政策题、精确编号、跨文档比较、无答案、旧版本冲突、恶意文档、跨租户请求、删除后检索和后端故障。阈值由业务风险与实际基线共同确定；本书提供设计，不虚构“达到 99%”的成绩。

Acceptance covers conditional policies, exact IDs, comparisons, missing answers, conflicts, malicious documents, cross-tenant requests, post-deletion retrieval, and outages. Set thresholds using business risk and measured baselines. This book provides a design, not fabricated success rates.

## 重点与难点 / Key points and difficulties

重点：需求—数据契约—实现—评估逐项对应。难点：权限、版本与删除必须贯穿每层。

Key: trace requirements through contracts, implementation, and tests. Difficulty: preserve access, versions, and deletion semantics at every layer.

## 面试考点与参考回答 / Interview question and answer

问：讲一个你负责的 RAG 项目，应说什么？答：业务目标、数据规模与结构、基线、失败样例、方案取舍、配对评测、上线约束和真实收益，明确个人责任。

Q: How should you present a RAG project? A: cover goals, data, baseline, failures, tradeoffs, paired evaluation, deployment constraints, measured impact, and your responsibilities.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：把选型列表当项目方案。处置：每个组件说明解决哪个失败、增加多少成本、怎样验证和回滚。

Pitfall: presenting a technology list as a design. Explain the failure each component addresses, its cost, verification, and rollback.

## 动手实验与验收 / Exercise and acceptance criteria

完成一份项目验收矩阵与最小运行链路，用真实运行结果填表。验收：未运行项写未验证，不能用推测补齐。

Create an acceptance matrix and minimal executable path, then populate it with real results. Acceptance: mark unrun items as unverified.

## 代码实现补充 / Implementation supplement: 带权限、引用与验收的最小知识库 / A minimal knowledge base with authorization and citations

依赖 / Dependencies: Python 3.10+; `llama-index-core==0.14.25`。

将完整代码保存为独立 `.py` 文件，在独立进程执行 `python filename.py`。无需密钥，无付费调用；验收为断言通过并输出结果。

Save the full block as a standalone `.py` file and run it in a separate process. No API key or paid call is needed; assertions must pass and results are printed.

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

### 实现说明、验收与项目边界 / Implementation, acceptance and production boundaries

先在单文件闭环实现 Document/Node 的来源与授权，再拆分摄取和在线服务。这个示例有意只返回原文，Mock 向量不提供语义拒答能力；租户内无关问题仍可能返回一条政策。进入生产前增加真实嵌入、相关性与无答案评测、来源版本、增量删除、持久化、trace 和发布门禁。

Start with provenance and authorization in a single-file loop before separating ingestion and serving. This deliberately returns source text; mock vectors cannot support semantic abstention, so irrelevant in-tenant questions may still retrieve a policy. Add real embeddings, relevance and unanswerable evaluation, revisions, deletion, persistence, tracing and release gates.

首次运行 / First run：tokenizer 可能下载编码缓存。离线运行需预置缓存并设置 `TIKTOKEN_CACHE_DIR`。Tokenization may download an encoding cache; provision it before offline use.
