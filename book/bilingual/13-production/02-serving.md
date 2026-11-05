# 13.02 服务化、配置与发布策略 / Serving, configuration, and rollout strategies

[返回全书目录 / Contents](../00-contents.md)

生产服务启动时加载已发布索引，不应每次 HTTP 请求重建索引。启动探针检查配置和必需资源，就绪探针确认能够提供正确版本的服务。健康探针不宜每秒调用昂贵模型，否则监控本身可能消耗配额并触发故障。

Load published indexes at startup rather than rebuilding on each request. Startup checks validate configuration and resources; readiness confirms service with the intended version. Avoid expensive model calls in frequent health probes.

将摄取作业与查询服务拆开，分别扩容与授权。发布包绑定应用版本、索引版本、嵌入模型、提示版本和模式版本。支持灰度与回滚，确保应用和索引之间兼容。新模型或维度迁移采用新集合构建，不能对旧集合边查询边无约束重写。

Separate ingestion workers from query serving for scaling and permissions. Bind application, index, embedding, prompt, and schema versions into a release. Support canaries and rollback with compatibility checks. Migrate embeddings through new collections rather than unrestricted in-place rewrites.

接口应提供请求 ID、明确错误类型、超时与取消语义。回答结构包含正文、引用、索引版本和必要的拒答状态。不要把内部堆栈、凭据或全部候选暴露给客户端。下列伪代码描述边界，不是可直接启动的完整 Web 服务。

APIs need request IDs, error types, deadlines, and cancellation semantics. Responses should contain text, citations, index version, and abstention state. Do not expose stacks, credentials, or all candidates. The pseudocode describes boundaries rather than a runnable server.

## 示例与运行边界 / Example and execution scope

以下为架构伪代码，不可直接运行。

This is architecture pseudocode, not executable code.

```text
request = authenticate_and_validate(incoming_request)
scope = authorization_scope(request.identity)
release = load_published_release()
evidence = retrieve(request.query, release, scope)
evidence = validate_and_budget(evidence, scope)
answer = generate_with_deadline(request.query, evidence)
return validate_citations_and_serialize(answer, release.version)
```

## 重点与难点 / Key points and difficulties

重点：发布对象包含应用与索引。难点：兼容性、灰度比较和快速回滚。

Key: release application and index versions together. Difficulty: compatibility, canary comparison, and rollback.

## 面试考点与参考回答 / Interview question and answer

问：为什么摄取与查询分开部署？答：资源模式、权限和失败影响不同；隔离后重建不会拖垮在线请求。

Q: Why separate ingestion from serving? A: resource patterns, permissions, and failure impact differ; rebuilding should not overwhelm live queries.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：启动时自动重建巨大索引，所有副本同时耗尽配额。处置：独立构建与版本化发布，服务只读取就绪版本。

Pitfall: every replica rebuilds a large index on startup. Build separately and serve only published versions.

## 动手实验与验收 / Exercise and acceptance criteria

设计一次新嵌入模型灰度发布。验收：旧版本可回滚，权限负例通过，观察窗口内有质量与成本指标。

Plan a canary embedding migration. Acceptance: rollback, access-denial checks, and quality/cost metrics during observation.
