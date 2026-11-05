# Reading guide and version scope

[目录 / Contents](00-contents.md)

This book targets software engineers with basic Python knowledge. Its goal is principled implementation, baselines, failure diagnosis, and production boundaries. The 14 chapters and 42 sections correspond across all three editions.

Reading paths: beginners start with 01–06, then 11 and 14; production readers add 10, 12, and 13; advanced retrieval readers focus on 07–08; agent readers use 09–10. Every section includes priorities, interviews, pitfalls, and acceptance exercises.

Source basis: the user curriculum defines six major topics, the architecture draft supplies initial concepts, and four MHTML archives provide learning context. The manuscript reorganizes and explains the material rather than copying the archives.

Curriculum mapping: ingestion maps to 01–04, indexing to 05 and 08, retrieval to 06, advanced retrieval to 07, agents to 09–10, and evaluation to 11–12. Added emphasis includes environments, production, and the capstone.

Version scope: authored on 2026-11-05. Official vector-index and ingestion pages were consulted; agent and standalone workflow entry points were checked through official search results. Not every integration has been verified against a latest release, and no exact dependency combination is claimed as tested.

Code tiers: pure-Python algorithms run independently; Mock examples require core and test plumbing only; embeddings, Chroma, agents, and workflows need their integrations. Snippets referencing existing variables such as index are not standalone scripts. Text blocks are pseudocode. Environment setup and external service calls were not automatically performed while writing.

Study method: explain a failure, run an experiment, and repeat on your data. Choose thresholds from business risk. The book invents no benchmark scores, latency measurements, prices, or production impact; experiment proposals are not measured results.

## Official documentation

- [Using VectorStoreIndex](https://developers.llamaindex.ai/python/framework/module_guides/indexing/vector_store_index/)
- [Ingestion Pipeline](https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/)
- [Building an agent](https://developers.llamaindex.ai/python/framework/understanding/agent/)
- [FunctionAgent / AgentWorkflow Basic Introduction](https://developers.llamaindex.ai/python/examples/agent/agent_workflow_basic/)
- [Multi-agent patterns in LlamaIndex](https://developers.llamaindex.ai/python/framework/understanding/agent/multi_agent/)
- [Workflow API](https://developers.llamaindex.ai/python/workflows-api-reference/workflow/)
- [Workflows Introduction](https://developers.llamaindex.ai/python/llamaagents/workflows/)
- [Events API](https://developers.llamaindex.ai/python/workflows-api-reference/events/)
