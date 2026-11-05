# 13.03 运维手册、故障演练与变更管理 / Runbooks, incident drills, and change management

[返回全书目录 / Contents](../00-contents.md)

运维手册要从症状进入：空答案、引用错位、跨租户异常、延迟升高、成本突增和数据过期。每种症状对应只读检查、止损动作、恢复步骤与验证。遇到疑似越权先阻断受影响路径并保留审计信息，再定位根因。

Runbooks begin with symptoms: empty answers, bad citations, access anomalies, latency, cost spikes, and stale data. Define inspection, containment, recovery, and verification for each. Suspected unauthorized access requires containing the affected path while preserving audit evidence.

数据新鲜度应作为 SLO，而不只是问答可用率。监测来源最新版本与已发布索引之间的延迟，区分来源停更、连接器失败、构建失败和发布卡住。对于法律删除与撤权，定义更严格的传播期限。

Treat freshness as an SLO alongside availability. Measure lag from source revisions to published indexes and distinguish source inactivity, connector failure, build failure, and publication failure. Define stricter propagation targets for deletion and access revocation.

变更管理覆盖模型、提示、分块、依赖、索引参数和来源模式。每次记录变更理由、开发集结果、风险、回滚目标与负责人。故障复盘围绕系统机制和监测缺口，不以“模型偶尔不稳定”替代具体解释。

Change management covers models, prompts, chunking, dependencies, indexes, and source schemas. Record rationale, evaluation, risks, rollback, and ownership. Incident reviews should identify mechanisms and monitoring gaps rather than simply blaming model variability.

## 重点与难点 / Key points and difficulties

重点：新鲜度、权限传播与恢复有明确目标。难点：跨来源、构建、发布和缓存的故障定位。

Key: define freshness, authorization propagation, and recovery targets. Difficulty: locating failures across ingestion, release, and caches.

## 面试考点与参考回答 / Interview question and answer

问：线上召回突然下降查什么？答：语料和权限变化、模型配置、索引发布、过滤语义、后端参数与缓存版本，按最近变更逐层排查。

Q: What causes sudden retrieval degradation? A: corpus or ACL changes, embeddings, index releases, filter semantics, backend settings, or cache versions; inspect recent changes by stage.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：降级时去掉权限过滤以恢复结果。处置：安全边界不可降级，可返回受控不可用或只用已授权旧版本。

Pitfall: removing filters to restore availability. Never degrade authorization; return controlled failure or an authorized rollback version.

## 动手实验与验收 / Exercise and acceptance criteria

演练向量库不可用、连接器停更和错误索引发布。验收：每次都有检测、止损、恢复和验证记录。

Drill store outage, stale synchronization, and a bad index release. Acceptance: detection, containment, recovery, and verification records.
