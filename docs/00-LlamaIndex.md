# LlamaIndex

Build production-ready context-augmented LLM applications and retrieval pipelines

## About

Teaches developers how to build robust, production-grade applications that connect private data to large language models. You will master data ingestion, indexing strategies, advanced retrieval techniques, and multi-agent workflows using the LlamaIndex Python framework. The curriculum equips software engineers and AI developers with practical skills to deploy efficient retrieval-augmented generation systems.

## Covers

- Data connectors and document parsing strategies
- Node parsing, chunking, and metadata extraction
- Vector stores and custom indexing architectures
- Advanced query engines, reranking, and hybrid search
- Autonomous data agents and tool orchestration
- Evaluation metrics and production observability

### Data Ingestion and Parsing

Load, clean, and structure unstructured enterprise data from diverse sources into standardized documents.

- Framework Architecture and Core Concepts
- SimpleDirectoryReader for Local Files
- Remote Data Connectors with LlamaHub
- Metadata Management for Document Objects
- Sentence Splitters and Node Parsers
- Semantic Chunking for Complex Text

### Indexing and Vector Storage

Construct searchable indices and persist high-dimensional embeddings across dedicated vector databases.

- Vector Store Index Fundamentals
- Local Vector Store Configuration with Chroma
- Summary Indexes for Global Document Context
- Knowledge Graph Indexes for Relational Data
- Embedding Model Customization and Configuration
- Persistent Storage Management via StorageContext

### Retrieval and Query Optimization

Design resilient query pipelines that find precise context using advanced search and reranking techniques.

- Query Engine Architecture and Response Synthesizers
- Customizing Similarity Search Cutoffs
- Keyword and Hybrid Search with BM25
- Cross-Encoder Reranking with Node Postprocessors
- Auto-Retrieval Using Metadata Filters
- Streaming Responses for Low-Latency Interfaces

### Advanced Retrieval Architectures

Implement sophisticated RAG patterns to resolve ambiguous queries and retrieve dense hierarchical information.

- Router Query Engines for Multi-Source Selection
- Sub-Question Query Engines for Complex Inquiries
- Hierarchical Node Parsing with Parent Document Retrieval
- Sentence Window Retrieval Workflows
- Multi-Document Agents with Query Engine Tools

### Autonomous Data Agents

Create reasoning agents capable of tool execution, structured planning, and multi-step data analysis.

- Function Calling Agents with LLMs
- ReAct Agent Pattern Implementation
- Tool Creation from Existing Query Engines
- Context-Aware Memory and Chat Engines
- Human-in-the-Loop Agent Workflows

### Evaluation and Observability

Quantify pipeline accuracy, diagnose hallucination, and monitor application health in production environments.

- Faithfulness and Relevancy Evaluation Metrics
- Ground-Truth Generation via Synthetic Datasets
- OpenInference and OpenTelemetry Setup
- Tracing Pipeline Latency with Arize Phoenix
- Cost Tracking and Token Usage Optimization
