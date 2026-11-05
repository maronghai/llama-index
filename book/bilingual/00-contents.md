# LlamaIndex：从数据接入到生产级 RAG / From Data Ingestion to Production RAG

[导读 / Reading guide](00-guide.md) · [术语表 / Glossary](00-glossary.md)

## 01 基础架构与核心抽象 / Architecture and core abstractions

- [01.01 RAG 的生命周期与系统边界 / The RAG lifecycle and system boundaries](01-foundations/01-rag-lifecycle.md)
- [01.02 Document、Node 与证据溯源 / Documents, nodes, and provenance](01-foundations/02-documents-nodes.md)
- [01.03 Retriever、QueryEngine 与 ChatEngine / Retrievers, query engines, and chat engines](01-foundations/03-engines.md)

## 02 环境、版本与第一个可复现实验 / Environment, versions, and a reproducible first experiment

- [02.01 模块化安装与 Settings / Modular packages and Settings](02-environment/01-packages-settings.md)
- [02.02 离线链路冒烟测试 / An offline pipeline smoke test](02-environment/02-offline-smoke.md)
- [02.03 接入真实模型与建立基线 / Real models and a measurable baseline](02-environment/03-real-models.md)

## 03 本地读取、远程连接与复杂文档 / Local loading, remote connectors, and complex documents

- [03.01 使用 SimpleDirectoryReader / Using SimpleDirectoryReader](03-loading/01-directory-reader.md)
- [03.02 LlamaHub 连接器与增量同步 / LlamaHub connectors and incremental synchronization](03-loading/02-connectors.md)
- [03.03 PDF、表格、图像与解析质量 / PDFs, tables, images, and parsing quality](03-loading/03-parsing.md)

## 04 切块、元数据与摄取管道 / Chunking, metadata, and ingestion pipelines

- [04.01 句子、语义与层级切块 / Sentence, semantic, and hierarchical chunking](04-transformations/01-chunking.md)
- [04.02 元数据、过滤与内容视图 / Metadata, filtering, and content views](04-transformations/02-metadata.md)
- [04.03 IngestionPipeline、缓存与幂等 / IngestionPipeline, caching, and idempotency](04-transformations/03-pipeline.md)

## 05 向量索引、Chroma 与存储生命周期 / Vector indexes, Chroma, and storage lifecycle

- [05.01 VectorStoreIndex 与向量检索原理 / VectorStoreIndex and vector retrieval](05-index-storage/01-vector-math.md)
- [05.02 Chroma 集成与集合契约 / Chroma integration and collection contracts](05-index-storage/02-chroma.md)
- [05.03 StorageContext、更新与灾难恢复 / StorageContext, updates, and disaster recovery](05-index-storage/03-persistence.md)

## 06 查询引擎、重排与混合检索 / Query engines, reranking, and hybrid retrieval

- [06.01 响应合成、引用与拒答 / Response synthesis, citations, and abstention](06-retrieval/01-synthesis.md)
- [06.02 BM25、向量与 RRF 融合 / BM25, dense retrieval, and RRF](06-retrieval/02-hybrid.md)
- [06.03 重排、阈值与流式响应 / Reranking, thresholds, and streaming](06-retrieval/03-rerank-stream.md)

## 07 高级检索架构与多源问答 / Advanced retrieval and multi-source questions

- [07.01 父文档恢复与句子窗口 / Parent recovery and sentence windows](07-advanced-rag/01-parent-window.md)
- [07.02 Router 与多源路由 / Routing across sources](07-advanced-rag/02-routing.md)
- [07.03 子问题分解与多文档比较 / Question decomposition and multi-document comparison](07-advanced-rag/03-decomposition.md)

## 08 摘要、属性图与结构化数据 / Summaries, property graphs, and structured data

- [08.01 SummaryIndex 与全局问题 / SummaryIndex and global questions](08-specialized-indexes/01-summary.md)
- [08.02 属性图、实体消歧与图检索 / Property graphs, entity resolution, and graph retrieval](08-specialized-indexes/02-property-graph.md)
- [08.03 Text-to-SQL 与确定性计算 / Text-to-SQL and deterministic computation](08-specialized-indexes/03-sql.md)

## 09 工具、Agent 与对话记忆 / Tools, agents, and conversational memory

- [09.01 FunctionTool 与 QueryEngineTool / FunctionTool and QueryEngineTool](09-agents/01-tools.md)
- [09.02 FunctionAgent、ReAct 与预算 / FunctionAgent, ReAct, and budgets](09-agents/02-agent-patterns.md)
- [09.03 会话记忆、压缩与隔离 / Conversation memory, compression, and isolation](09-agents/03-memory.md)

## 10 事件工作流、异步与人工介入 / Event workflows, async execution, and human review

- [10.01 事件驱动工作流与状态 / Event-driven workflows and state](10-workflows/01-events.md)
- [10.02 异步、限流、取消与重试 / Async execution, rate limiting, cancellation, and retries](10-workflows/02-concurrency.md)
- [10.03 人工介入与多 Agent 协作 / Human review and multi-agent coordination](10-workflows/03-human-review.md)

## 11 评估集、指标与质量门禁 / Datasets, metrics, and quality gates

- [11.01 检索指标与证据标注 / Retrieval metrics and evidence labeling](11-evaluation/01-retrieval-metrics.md)
- [11.02 忠实性、相关性与正确性 / Faithfulness, relevance, and correctness](11-evaluation/02-answer-metrics.md)
- [11.03 合成数据、数据泄漏与回归门禁 / Synthetic data, leakage, and regression gates](11-evaluation/03-datasets-gates.md)

## 12 可观测性、性能与成本 / Observability, performance, and cost

- [12.01 Trace、OpenTelemetry 与 Phoenix / Traces, OpenTelemetry, and Phoenix](12-observability/01-tracing.md)
- [12.02 延迟分解、缓存与容量规划 / Latency decomposition, caching, and capacity](12-observability/02-latency.md)
- [12.03 Token 成本与质量约束优化 / Token cost and quality-constrained optimization](12-observability/03-cost.md)

## 13 安全、多租户与生产发布 / Security, tenancy, and production releases

- [13.01 提示注入、数据权限与输出安全 / Prompt injection, authorization, and output security](13-production/01-security.md)
- [13.02 服务化、配置与发布策略 / Serving, configuration, and rollout strategies](13-production/02-serving.md)
- [13.03 运维手册、故障演练与变更管理 / Runbooks, incident drills, and change management](13-production/03-operations.md)

## 14 企业知识库项目与面试总复习 / Enterprise capstone and interview review

- [14.01 从需求到可验收的企业知识库 / An enterprise knowledge base from requirements to acceptance](14-capstone-interview/01-capstone.md)
- [14.02 八类典型故障与修复思路 / Eight recurring failures and their remedies](14-capstone-interview/02-failure-cases.md)
- [14.03 重点难点地图与面试表达 / Priority map and interview communication](14-capstone-interview/03-interview-map.md)


## 本轮进阶实现增补与验证

本轮验证：17 个新增完整示例中 15 个独立运行通过；属性图和答案评估的接口问题已修正，修改后没有再验证。外部模型分支未执行。

Validation: 15 of 17 new complete examples passed in isolated processes. Interface issues in the property-graph and answer-evaluation examples were corrected without rerunning. External-model branches were not executed.
