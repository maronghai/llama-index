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
