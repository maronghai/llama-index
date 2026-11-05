# 14.01 从需求到可验收的企业知识库

[返回全书目录 / Contents](../00-contents.md)

项目场景是一家多地区企业的制度与客服知识库。用户询问政策、产品编号和工单经验；管理人员发布制度并撤回过期文件。系统必须提供引用、按租户与角色隔离、说明版本、在无答案时拒答。先把这些需求转成测试，而不是先选择向量数据库。

第一阶段准备可追溯语料快照和来源清单，以稳定 ID 导入 Document。第二阶段解析与切块，保存页码、标题和权限；建立向量与 BM25 双通道。第三阶段实现服务端授权、候选融合、重排、上下文预算、生成与引用核验。第四阶段加入评估、追踪、删除传播与蓝绿发布。每阶段先获得可验收基线再增加复杂架构。

数据契约建议包含 source_id、revision、tenant_id、acl_groups、effective_from、effective_to、deleted 和 parser_version。构建清单绑定快照、模型、分块、代码和依赖版本。查询审计记录身份范围摘要、索引版本和返回证据 ID，不记录明文密钥。

验收表至少覆盖：带条件政策题、精确编号、跨文档比较、无答案、旧版本冲突、恶意文档、跨租户请求、删除后检索和后端故障。阈值由业务风险与实际基线共同确定；本书提供设计，不虚构“达到 99%”的成绩。

## 重点与难点

重点：需求—数据契约—实现—评估逐项对应。难点：权限、版本与删除必须贯穿每层。

## 面试考点与参考回答

问：讲一个你负责的 RAG 项目，应说什么？答：业务目标、数据规模与结构、基线、失败样例、方案取舍、配对评测、上线约束和真实收益，明确个人责任。

## 项目中的坑与处置

坑：把选型列表当项目方案。处置：每个组件说明解决哪个失败、增加多少成本、怎样验证和回滚。

## 动手实验与验收

完成一份项目验收矩阵与最小运行链路，用真实运行结果填表。验收：未运行项写未验证，不能用推测补齐。

## 代码实现补充：带权限、引用与验收的最小知识库

依赖：Python 3.10+；安装 `llama-index-core==0.14.25`。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

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

### 实现说明、验收与项目边界

先在单文件闭环实现 Document/Node 的来源与授权，再拆分摄取和在线服务。这个示例有意只返回原文，Mock 向量不提供语义拒答能力；租户内无关问题仍可能返回一条政策。进入生产前增加真实嵌入、相关性与无答案评测、来源版本、增量删除、持久化、trace 和发布门禁。

首次运行提示：核心包 tokenizer 可能下载编码缓存；离线环境请预置缓存并设置 `TIKTOKEN_CACHE_DIR`。无需模型密钥不代表首次运行不联网。
