# 导读与版本说明 / Reading guide and version scope

[目录 / Contents](00-contents.md)

本书面向具备 Python 基础的软件工程师。目标是能解释原理、建立基线、诊断失败并设计生产边界，而不只是跑通一个聊天演示。全书 14 章、42 节，三种版本编号一一对应。

This book targets software engineers with basic Python knowledge. Its goal is principled implementation, baselines, failure diagnosis, and production boundaries. The 14 chapters and 42 sections correspond across all three editions.

阅读路线：初学者先读 01—06，再读 11 和 14；项目落地补读 10、12、13；进阶检索读 07—08；Agent 方向读 09—10。每节末尾包含重点难点、面试参考、踩坑与验收实验。

Reading paths: beginners start with 01–06, then 11 and 14; production readers add 10, 12, and 13; advanced retrieval readers focus on 07–08; agent readers use 09–10. Every section includes priorities, interviews, pitfalls, and acceptance exercises.

资料基础：用户的 docs/00-LlamaIndex.md 提供六大主题，docs/1.1-Framework_Architecture_and_Core_Concepts.md 提供基础稿；html 中四份 MHTML 作为学习线索。正文为重新组织的原创讲解，不逐字复制网页存档。

Source basis: the user curriculum defines six major topics, the architecture draft supplies initial concepts, and four MHTML archives provide learning context. The manuscript reorganizes and explains the material rather than copying the archives.

原大纲映射：Data Ingestion 对应 01—04；Indexing 对应 05、08；Retrieval 对应 06；Advanced Retrieval 对应 07；Agents 对应 09—10；Evaluation 对应 11—12。新增 02 环境、13 生产与 14 综合项目。

Curriculum mapping: ingestion maps to 01–04, indexing to 05 and 08, retrieval to 06, advanced retrieval to 07, agents to 09–10, and evaluation to 11–12. Added emphasis includes environments, production, and the capstone.

版本边界：编写日期为 2026-11-05。核心向量索引与摄取管道已查阅官方页面；Agent 与独立 Workflows 入口经官方搜索结果确认。未对全部集成逐项做最新版本核验，不宣称某个精确依赖组合已被测试。

Version scope: authored on 2026-11-05. Official vector-index and ingestion pages were consulted; agent and standalone workflow entry points were checked through official search results. Not every integration has been verified against a latest release, and no exact dependency combination is claimed as tested.

代码分层：纯 Python 算法可独立执行；离线 Mock 示例依赖核心包且只测链路；真实嵌入、Chroma、Agent 和 Workflow 示例需要各自集成与模型。含 index 等外部变量的片段不是独立脚本；标为 text 的流程为伪代码。环境安装和外部服务调用未作为编写过程自动执行。

Code tiers: pure-Python algorithms run independently; Mock examples require core and test plumbing only; embeddings, Chroma, agents, and workflows need their integrations. Snippets referencing existing variables such as index are not standalone scripts. Text blocks are pseudocode. Environment setup and external service calls were not automatically performed while writing.

学习方法：每节先解释一个失败，再运行对应实验，最后用自己的数据复测。所有实验阈值需依据业务风险确定。书中没有虚构检索成绩、延迟、价格或上线收益；实验建议不是实测结论。

Study method: explain a failure, run an experiment, and repeat on your data. Choose thresholds from business risk. The book invents no benchmark scores, latency measurements, prices, or production impact; experiment proposals are not measured results.

## 官方资料入口 / Official documentation

- [Using VectorStoreIndex](https://developers.llamaindex.ai/python/framework/module_guides/indexing/vector_store_index/)
- [Ingestion Pipeline](https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/)
- [Building an agent](https://developers.llamaindex.ai/python/framework/understanding/agent/)
- [FunctionAgent / AgentWorkflow Basic Introduction](https://developers.llamaindex.ai/python/examples/agent/agent_workflow_basic/)
- [Multi-agent patterns in LlamaIndex](https://developers.llamaindex.ai/python/framework/understanding/agent/multi_agent/)
- [Workflow API](https://developers.llamaindex.ai/python/workflows-api-reference/workflow/)
- [Workflows Introduction](https://developers.llamaindex.ai/python/llamaagents/workflows/)
- [Events API](https://developers.llamaindex.ai/python/workflows-api-reference/events/)

## 本次代码补充与验证范围

本次为原先没有 Python 实现的 25 节各补充一个完整代码块，三版同步，现每版 42 节均有 Python 代码。新增 25 个示例在 Python 3.12.14 下执行成功，其中核心框架示例使用 llama-index-core 0.14.25。三版共 126 个 Python 代码块通过语法解析并核对代码一致性；原有 17 个示例本次未重新执行，真实模型、数据库、Phoenix 等外部集成未完成端到端验证。

核心框架可能在第一次调用 tokenizer 时下载编码缓存。离线部署需预先准备缓存，并通过 TIKTOKEN_CACHE_DIR 指定缓存位置；无需 API Key 不等于首次运行完全不联网。本次首次执行部分索引示例超时，缓存就绪后运行成功。Mock 示例只验证链路，标准库生产算法示例只展示设计边界，不代表完整生产服务。


## Code supplement and validation scope

One complete code block was added to each of the 25 sections that lacked Python implementations, synchronized across all editions. All 42 sections per edition now contain Python. The 25 new examples executed successfully with Python 3.12.14; core examples used llama-index-core 0.14.25. All 126 Python blocks across the three editions parsed successfully and matching sections contained identical code. The 17 original examples were not re-executed in this update. Real models, databases and Phoenix integrations were not end-to-end tested.

Core tokenization may download an encoding cache on first use. Provision that cache and set TIKTOKEN_CACHE_DIR for offline deployment. No API key does not mean a network-free first run. Several initial index runs timed out and succeeded once the cache was available. Mock examples establish connectivity only; standard-library production examples illustrate boundaries rather than complete production services.
