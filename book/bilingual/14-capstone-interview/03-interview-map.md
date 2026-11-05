# 14.03 重点难点地图与面试表达 / Priority map and interview communication

[返回全书目录 / Contents](../00-contents.md)

学习优先级分三层：必须掌握 Document/Node、显式模型配置、数据解析、切块、向量检索、引用与评估；进阶掌握混合检索、重排、父块、路由和存储更新；按任务选学属性图、多 Agent 和多模态。先把单链路做可靠，再增加可证明有收益的复杂度。

Use three priority tiers. Essentials: Documents and Nodes, explicit configuration, parsing, chunking, vectors, citations, and evaluation. Intermediate: hybrid retrieval, reranking, parent recovery, routing, and updates. Task-dependent: graphs, multiple agents, and multimodality. Establish reliability before adding complexity.

面试问题一：如何优化召回？先确认标签与失败分布，再检查解析、模型、切块、混合候选和重排；每步报告代价。问题二：如何防幻觉？分开处理数据缺失、检索不足与生成越界，增加证据核验与拒答。问题三：如何做增量？稳定 ID、内容哈希、检查点、删除传播和对账。

Interview question one: improve retrieval by first validating labels and failure slices, then parsing, embeddings, chunking, candidate fusion, and reranking, with costs. Question two: reduce hallucination by distinguishing missing data, insufficient retrieval, and unsupported generation. Question three: implement incremental sync with stable IDs, hashes, checkpoints, deletion propagation, and reconciliation.

问题四：如何上线？说明独立构建、版本发布、权限、限流、观测、评估门禁与回滚。问题五：如何选数据库？按过滤、规模、运维、恢复、租户和团队能力，不只看排行榜。问题六：如何证明效果？展示固定基线、开发/测试分离、配对结果、错误案例和真实成本。

Question four: production readiness requires separate builds, versioned releases, authorization, limits, traces, gates, and rollback. Question five: choose stores by filtering, scale, operations, recovery, tenancy, and team capability. Question six: establish impact using a fixed baseline, split datasets, paired outcomes, failures, and real costs.

表达项目时使用“目标—约束—基线—失败—选择—验证—结果”的顺序。没有实测结果就直说目前是设计或实验阶段。技术术语只有在能解释为什么需要它、如何失败和怎样验证时才有价值。

Present projects as goals, constraints, baseline, failures, decisions, validation, and results. Clearly identify designs and unmeasured experiments. Technical terms matter only when you can explain their purpose, failure modes, and verification.

## 重点与难点 / Key points and difficulties

重点：先掌握可复现基本链路，再按失败选择高级架构。难点：把概念知识转成可验证的工程判断。

Key: master a reproducible baseline and add advanced patterns in response to failures. Difficulty: turn concepts into verifiable engineering decisions.

## 面试考点与参考回答 / Interview question and answer

问：LlamaIndex 的价值在哪里？答：提供连接数据、节点、检索、合成、工具与工作流的统一抽象及集成，减少重复编排；仍需开发者负责业务语义与生产边界。

Q: What value does LlamaIndex provide? A: common abstractions and integrations for data, nodes, retrieval, synthesis, tools, and workflows, reducing orchestration work while leaving business and production responsibilities to developers.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：背 API 名称却无法解释取舍。处置：每个概念准备一个失败案例、一个实验和一个不适用场景。

Pitfall: memorizing APIs without tradeoffs. Prepare one failure, experiment, and unsuitable use case for each concept.

## 动手实验与验收 / Exercise and acceptance criteria

用五分钟讲完整项目，再回答“预算减半”“必须离线”“权限实时撤销”三种追问。验收：方案随约束变化，且不虚构成绩。

Present the project in five minutes, then handle half-budget, offline-only, and immediate-revocation constraints. Acceptance: adapt the design without inventing results.
