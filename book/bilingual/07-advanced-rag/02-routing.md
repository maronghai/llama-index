# 07.02 Router 与多源路由 / Routing across sources

[返回全书目录 / Contents](../00-contents.md)

多源系统可能包含政策文档、工单、产品目录和数据库。Router 根据问题选择合适检索器或引擎。路由描述应说明数据覆盖范围、时间、语言和适合的问题，而不是空泛的“最好的工具”。路由器只负责选择，不会自动协调各来源的访问规则。

Multi-source systems may include policies, tickets, catalogs, and databases. Routers select suitable retrievers or engines. Tool descriptions should state coverage, time range, language, and supported questions. Selection does not automatically coordinate authorization.

确定性字段优先使用规则路由，例如租户、地区、数据类型。语义选择可用于问题类型，但应保留低置信度回退。单源选择更便宜，多源并行覆盖更全但增加成本与冲突。测试路由准确率时区分“选错来源”和“来源正确但没有答案”。

Use deterministic routing for tenant, region, and data type. Semantic selection can classify question intent with a fallback. Single-source routing is cheaper; parallel multi-source retrieval offers coverage at higher cost and conflict risk. Distinguish wrong routing from correct routing to an incomplete source.

工具描述和来源名称本身也可能泄露敏感信息。只给当前用户可见的工具集合，并对每次工具调用重新授权。记录路由理由的结构化摘要即可，不需要收集模型隐藏推理。

Tool names and descriptions may themselves reveal sensitive information. Expose only permitted tools and authorize every call. Log a concise routing rationale rather than attempting to collect hidden model reasoning.

## 重点与难点 / Key points and difficulties

重点：规则与语义路由结合。难点：低置信度回退、多源冲突与权限分层。

Key: combine rule-based and semantic routing. Difficulty: fallback, conflicts, and layered permissions.

## 面试考点与参考回答 / Interview question and answer

问：什么时候不要 Router？答：来源很少且成本可控时，并行检索可能更简单稳定；先证明路由能节省成本且不损失关键召回。

Q: When should routing be avoided? A: with few affordable sources, parallel retrieval may be simpler; prove routing saves cost without unacceptable recall loss.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：工具介绍过度相似，模型随机选路。处置：写清覆盖边界，用容易混淆的问题做对比评测。

Pitfall: nearly identical descriptions cause unstable selection. Specify boundaries and test ambiguous questions.

## 动手实验与验收 / Exercise and acceptance criteria

建立三类来源与 15 个路由问题，含跨源问题。验收：报告混淆矩阵和回退比例，解释每个误路由。

Create three sources and 15 routing questions including cross-source cases. Acceptance: a confusion matrix, fallback rate, and explanations for misroutes.
