# LlamaIndex：从数据接入到生产级 RAG
> *LlamaIndex: From Data Ingestion to Production RAG*

本项目是一套面向实战与生产落地的 **LlamaIndex 权威技术著作**与**工业级参考实现代码库**。包含系统完整的 14 章 42 节三语书稿，以及一个可独立运行、具备多租户隔离与持久化异步队列的企业级 RAG 项目工程。

---

## 目录导航 (Table of Contents)

1. [项目全景与特色](#项目全景与特色)
2. [全书架构与核心章节 (Book Structure)](#全书架构与核心章节-book-structure)
3. [三语书稿阅读指南 (`book/`)](#三语书稿阅读指南-book)
4. [生产级项目介绍 (`book-demo/`)](#生产级项目介绍-book-demo)
5. [五分钟快速上手 (Quickstart)](#五分钟快速上手-quickstart)
6. [重点、难点与面试突击路线](#重点难点与面试突击路线)
7. [生产演进与架构边界](#生产演进与架构边界)

---

## 项目全景与特色

- 📖 **三语对应体系**：提供完整的**中文版 (`book/zh/`)**、**英文版 (`book/en/`)** 与 **中英逐段对照版 (`book/bilingual/`)**，共计 136 个 Markdown 文件，覆盖理论、代码、面试与实战。
- 🎯 **统一工程栏目**：全书 42 个小节，每节严格遵循结构化写作，包含：
  - **核心原理与架构设计**
  - **重点与难点深度拆解**
  - **高频面试考点与标准解答思路**
  - **实际生产项目踩坑指南与规避手段**
  - **可执行验证的 Python 代码实现与实验验收要求**
- 🛠️ **完整可运行工程 (`book-demo/`)**：拒绝空谈 Mock，串联真实 LlamaIndex 检索组件、FastAPI 服务、多租户鉴权、SQLite WAL 持久化、文档版本乐观锁、持久化摄取任务队列、批量向量计算及自动化评测套件。

---

## 全书架构与核心章节 (Book Structure)

全书共 **14 章、42 节**，逻辑层层递进：

| 章节 | 核心主题 | 关键涵盖技术点 |
|---|---|---|
| **01 基础架构与核心抽象** | RAG 范式演进与边界 | RAG 生命周期、Document 与 Node 溯源、Retriever / QueryEngine / ChatEngine |
| **02 环境与首个实验** | 模块化与配置收敛 | `llama-index-core` 显式 Settings、离线冒烟测试、真实模型基线 |
| **03 加载、连接与复杂文档** | 数据源打通与解析 | `SimpleDirectoryReader`、LlamaHub 连接器、增量同步对账、PDF/表格多模态解析 |
| **04 切块、元数据与管道** | 数据加工与变换 | 语义/层级/窗口切块、元数据提取与过滤、`IngestionPipeline` 缓存与幂等 |
| **05 向量索引与存储** | 检索核心与持久化 | 余弦距离与向量数学、Chroma 生产集合契约、`StorageContext` 灾备与迁移 |
| **06 查询重排与混合检索** | 精度增强与输出治理 | Compact / Tree 响应合成、BM25 + 向量 + RRF 倒数排名融合、交叉编码重排与流式输出 |
| **07 高级检索与多源问答** | 解决召回断裂与复杂意图 | 句子窗口与父子文档、`RouterQueryEngine` 多源路由、`SubQuestionQueryEngine` 子问题分解 |
| **08 专用索引与结构化** | 超越简单向量检索 | `SummaryIndex` 全局摘要检索、Property Graph 属性图与知识图谱、Text-to-SQL 只读安全计算 |
| **09 Agent、工具与记忆** | 自主决策与上下文管理 | `FunctionTool` 与 QueryEngine 封装、FunctionAgent / ReAct 循环、多轮会话窗口与租户记忆隔离 |
| **10 工作流与人机协同** | 工业级事件驱动引擎 | `llama-index-core.workflow` 事件状态机、异步限流并发、人类在环 (Human-in-the-Loop) 审核 |
| **11 评估体系与门禁** | RAG 质量量化监控 | 检索指标 (Hit Rate / MRR / NDCG)、答案指标 (忠实度 / 相关性)、CI/CD 自动化回归门禁 |
| **12 可观测性与成本** | 生产运行健康保障 | OpenTelemetry 与 Phoenix 链路追踪、P95/P99 延迟归因剖析、Token 成本计算与分级优化 |
| **13 生产部署与合规** | 基础设施加固 | Prompt 注入防御、数据行级隔离、无状态服务容器化发布、SRE 故障预案演练 |
| **14 综合实战与面试** | 生产落地大集结 | 端到端企业知识库落地实操、八大经典生产故障复盘、全书面试核心表达地图 |

---

## 三语书稿阅读指南 (`book/`)

所有书稿位于 `book/` 目录下，并已打包提供完整下载：

- **[全书总导读 (`book/00-start.md`)](book/00-start.md)**
- 🇨🇳 **[中文版全书目录 (`book/zh/00-contents.md`)](book/zh/00-contents.md)**
- 🇬🇧 **[English Edition Table of Contents (`book/en/00-contents.md`)](book/en/00-contents.md)**
- 🔀 **[中英逐段对照版目录 (`book/bilingual/00-contents.md`)](book/bilingual/00-contents.md)**
- 📦 **[三语全书打包下载 (`book/LlamaIndex_三语全书.zip`)](book/LlamaIndex_三语全书.zip)**

---

## 生产级项目介绍 (`book-demo/`)

`book-demo/` 是配套书中实战章节构建的**轻量级、自包含多租户企业知识库服务**。

### 核心技术特性

1. **服务端租户强制绑定 (Strict Multi-Tenancy)**：
   - 客户端只能提交 API Key，由服务器配置解析唯一的 `tenant` 与角色 (`reader`, `writer`, `admin`)。
   - 彻底杜绝在请求体伪造租户导致的越权串标。
2. **混合检索与排序融合 (Hybrid Retrieval & RRF)**：
   - 结合 LlamaIndex `VectorStoreIndex` 密集向量检索与精准词法 BM25 检索。
   - 采用标准 Reciprocal Rank Fusion (RRF) 融合算法计算最终候选集。
3. **严格一致性保障与证据复查 (Consistency & Tombstones)**：
   - 每次检索生成完毕、向客户端输出之前，二次复查命中的文档版本；若在途被删除或更新，直接返回 `409 Conflict`，杜绝脏证据扩散。
   - `document_versions` 记录最大历史版本墓碑（Tombstone），文档删除后重建版本单调递增，彻底避免旧缓存命中。
4. **持久化异步摄取队列 (Durable Ingestion Jobs)**：
   - 基于 SQLite 事务实现租约（Lease）认领与心跳续期机制，防止节点崩溃任务丢失。
   - 支持幂等控制 (`idempotency_key`)、任务优雅取消、指数退避重试与背压限制。
5. **模型接入与真实诊断 (Real Model Connectivity)**：
   - 默认远程模式 (`KB_MODE=remote`)，支持批量向量嵌入 (`batch_size`)、校验非零/有限维度与返回顺序。
   - 支持生成端与嵌入端独立地址与密钥配置。
   - 提供 `doctor` 命令用于直接探测远端端点连通性与引用契约。
6. **自动化评测与目录导入**：
   - `ingest-directory`：将本地 Markdown / Text 递归命名空间化入库，自动计算哈希增量跳过。
   - `evaluate`：直接针对运行中的 HTTP 实例跑测试集，产出 Recall@k、MRR 与命中包含报告。

详细架构设计、数据库表结构与运维演练，请查阅 **[`book-demo/DEPLOYMENT.md`](book-demo/DEPLOYMENT.md)**。

---

## 五分钟快速上手 (Quickstart)

### 1. 运行离线端到端验收演示 (Demo)

离线模式使用确定性哈希向量与特征提取，无需配置外部大模型 API Key，验证多租户隔离、权限检查与未知问题拒答：

```powershell
cd book-demo

# 1. 安装锁定依赖
python install.py

# 2. 运行自动化演示
python run.py demo
```

输出将呈现通过证据检索、租户隔离与未知拒绝检查的结果。

### 2. 运行工程测试套件 (Test Suite)

执行全量单元与集成测试（涵盖并发冲突、租约失效、容量越界、故障注入）：

```powershell
python -m pytest tests -v -p no:cacheprovider
```

### 3. 配置并启动正式服务 (Serve & Worker)

在独立终端分别启动 API 服务与异步摄取工作进程：

```powershell
# 生成高强度随机客户端密钥并映射身份
$Key = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:KB_KEYS_JSON = @{ $Key = @{ tenant = 'alpha'; role = 'admin' } } | ConvertTo-Json -Compress

# 配置真实模型网关（示例）
$env:KB_MODE = 'remote'
$env:KB_MODEL_BASE = 'https://your-model-gateway.com/v1'
$env:KB_MODEL_KEY = 'sk-your-model-key'
$env:KB_EMBEDDING_MODEL = 'text-embedding-3-small'
$env:KB_CHAT_MODEL = 'gpt-4o-mini'
$env:KB_EMBEDDING_DIM = '1536'
$env:KB_DB = 'data/knowledge.db'

# 终端 1：启动 API 网关
python run.py serve

# 终端 2：启动后台摄取 Worker
python run.py worker
```

### 4. 连通性自检与目录摄取

```powershell
# 连通性自检
python run.py doctor

# 批量摄取本地文档目录
$env:KB_SERVICE_URL = 'http://127.0.0.1:8000'
$env:KB_CLIENT_KEY = $Key
python run.py ingest-directory --input 'D:\CompanyDocs'
```

---

## 重点、难点与面试突击路线

在准备 RAG 与大模型架构师面试时，推荐重点复习书稿以下章节：

1. **RAG 评估与指标设计 (第 11 章)**：
   - *面试必问*：如何评估 RAG？没有标注集怎么做？
   - *掌握重点*：Hit Rate、MRR、NDCG、Context Precision/Recall、Faithfulness、Answer Relevance，以及合成测试集的污染规避。
2. **多租户数据安全与越权防御 (第 13 章 / 14 章)**：
   - *面试必问*：RAG 如何做到数据行级权限与物理隔离？
   - *掌握重点*：为什么在 Vector 检索后过滤是危险的（可能漏回未授权数据到 Prompt）、服务端身份绑定的必要性。
3. **混合检索与 RRF 排序融合 (第 06 章)**：
   - *面试必问*：Dense 检索与 Sparse (BM25) 检索各有何优劣？如何归一化分数融合？
   - *掌握重点*：为什么不能直接把 Cosine 距离与 BM25 分数线性相加？RRF 算法公式及参数 $k=60$ 的平滑机理。
4. **模型幻觉控制与拒答机制 (第 06 章 / book-demo)**：
   - *面试必问*：模型生成了看似合理但不正确的答案怎么办？
   - *掌握重点*：基于证据引用的二次校验，显式 `<REFUSE>` 提示约束与无证据保底拒答。

---

## 生产演进与架构边界

`book-demo` 针对单机中受控规模（单租户几千切块内）的企业内部知识库进行了高确定性优化。若要支撑千万级向量与全球高并发，在真实落地时建议按照本书演化指南推进：

- **分布式向量下推**：将本地 SQLite 内存索引迁移至专有分布式向量数据库（如 Milvus / Qdrant / PgVector），将租户过滤谓词直接下推到存储引擎。
- **消息中枢解耦**：将基于 SQLite 事务的单机任务表升级为 Kafka / RabbitMQ，搭配 Redis 分布式锁与 Outbox 模式。
- **模型弹性网关**：在服务入口前增加专用大模型网关，承担熔断降级、令牌桶速率限制与语义缓存（Semantic Cache）。

---

## 授权与版权

本仓库采用 **代码 MIT、书稿保留版权** 的分范围授权，详见 [根目录许可声明](LICENSE)。

| 内容 | 授权方式 |
|---|---|
| 本项目原创软件代码、脚本、测试与书中代码示例 | MIT，允许商用、修改及分发，须保留版权及许可声明 |
| 软件运行、安装与部署说明 | MIT，不包括书稿叙述性内容 |
| 中文、英文及中英对照书稿的正文、译文、图表等非代码内容 | 保留版权；法律允许范围以外的复制、转载、出版、改编及分发需取得权利人书面许可 |
| 第三方依赖、引用资料、商标及其他第三方内容 | 遵循各自原有许可与权利 |

- [配套代码 MIT License](book-demo/LICENSE)
- [书稿版权声明及代码示例许可](book/LICENSE)

版权归本项目各贡献者及其他相应权利人所有。MIT 不提供任何明示或默示担保，也不等于承诺项目已通过生产上线验收。本项目不代表 LlamaIndex 官方，也不主张拥有第三方依赖或引用材料的版权。
