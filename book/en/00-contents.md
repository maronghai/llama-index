# LlamaIndex: From Data Ingestion to Production RAG

[导读 / Reading guide](00-guide.md) · [术语表 / Glossary](00-glossary.md)

## 01 Architecture and core abstractions

- [01.01 The RAG lifecycle and system boundaries](01-foundations/01-rag-lifecycle.md)
- [01.02 Documents, nodes, and provenance](01-foundations/02-documents-nodes.md)
- [01.03 Retrievers, query engines, and chat engines](01-foundations/03-engines.md)

## 02 Environment, versions, and a reproducible first experiment

- [02.01 Modular packages and Settings](02-environment/01-packages-settings.md)
- [02.02 An offline pipeline smoke test](02-environment/02-offline-smoke.md)
- [02.03 Real models and a measurable baseline](02-environment/03-real-models.md)

## 03 Local loading, remote connectors, and complex documents

- [03.01 Using SimpleDirectoryReader](03-loading/01-directory-reader.md)
- [03.02 LlamaHub connectors and incremental synchronization](03-loading/02-connectors.md)
- [03.03 PDFs, tables, images, and parsing quality](03-loading/03-parsing.md)

## 04 Chunking, metadata, and ingestion pipelines

- [04.01 Sentence, semantic, and hierarchical chunking](04-transformations/01-chunking.md)
- [04.02 Metadata, filtering, and content views](04-transformations/02-metadata.md)
- [04.03 IngestionPipeline, caching, and idempotency](04-transformations/03-pipeline.md)

## 05 Vector indexes, Chroma, and storage lifecycle

- [05.01 VectorStoreIndex and vector retrieval](05-index-storage/01-vector-math.md)
- [05.02 Chroma integration and collection contracts](05-index-storage/02-chroma.md)
- [05.03 StorageContext, updates, and disaster recovery](05-index-storage/03-persistence.md)

## 06 Query engines, reranking, and hybrid retrieval

- [06.01 Response synthesis, citations, and abstention](06-retrieval/01-synthesis.md)
- [06.02 BM25, dense retrieval, and RRF](06-retrieval/02-hybrid.md)
- [06.03 Reranking, thresholds, and streaming](06-retrieval/03-rerank-stream.md)

## 07 Advanced retrieval and multi-source questions

- [07.01 Parent recovery and sentence windows](07-advanced-rag/01-parent-window.md)
- [07.02 Routing across sources](07-advanced-rag/02-routing.md)
- [07.03 Question decomposition and multi-document comparison](07-advanced-rag/03-decomposition.md)

## 08 Summaries, property graphs, and structured data

- [08.01 SummaryIndex and global questions](08-specialized-indexes/01-summary.md)
- [08.02 Property graphs, entity resolution, and graph retrieval](08-specialized-indexes/02-property-graph.md)
- [08.03 Text-to-SQL and deterministic computation](08-specialized-indexes/03-sql.md)

## 09 Tools, agents, and conversational memory

- [09.01 FunctionTool and QueryEngineTool](09-agents/01-tools.md)
- [09.02 FunctionAgent, ReAct, and budgets](09-agents/02-agent-patterns.md)
- [09.03 Conversation memory, compression, and isolation](09-agents/03-memory.md)

## 10 Event workflows, async execution, and human review

- [10.01 Event-driven workflows and state](10-workflows/01-events.md)
- [10.02 Async execution, rate limiting, cancellation, and retries](10-workflows/02-concurrency.md)
- [10.03 Human review and multi-agent coordination](10-workflows/03-human-review.md)

## 11 Datasets, metrics, and quality gates

- [11.01 Retrieval metrics and evidence labeling](11-evaluation/01-retrieval-metrics.md)
- [11.02 Faithfulness, relevance, and correctness](11-evaluation/02-answer-metrics.md)
- [11.03 Synthetic data, leakage, and regression gates](11-evaluation/03-datasets-gates.md)

## 12 Observability, performance, and cost

- [12.01 Traces, OpenTelemetry, and Phoenix](12-observability/01-tracing.md)
- [12.02 Latency decomposition, caching, and capacity](12-observability/02-latency.md)
- [12.03 Token cost and quality-constrained optimization](12-observability/03-cost.md)

## 13 Security, tenancy, and production releases

- [13.01 Prompt injection, authorization, and output security](13-production/01-security.md)
- [13.02 Serving, configuration, and rollout strategies](13-production/02-serving.md)
- [13.03 Runbooks, incident drills, and change management](13-production/03-operations.md)

## 14 Enterprise capstone and interview review

- [14.01 An enterprise knowledge base from requirements to acceptance](14-capstone-interview/01-capstone.md)
- [14.02 Eight recurring failures and their remedies](14-capstone-interview/02-failure-cases.md)
- [14.03 Priority map and interview communication](14-capstone-interview/03-interview-map.md)


## Advanced implementation revision and validation

Validation in this revision: 15 of the 17 new complete examples passed in isolated processes. The property-graph and answer-evaluation examples were subsequently corrected for the custom retriever init method and judge constructor; these edits have not been revalidated. Before those final corrections, 59 Chinese-edition Python blocks passed syntax parsing and the 17 new examples matched across all editions. Other legacy examples and real external-model branches were not executed.
