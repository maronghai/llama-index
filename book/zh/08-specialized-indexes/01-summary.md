# 08.01 SummaryIndex 与全局问题

[返回全书目录 / Contents](../00-contents.md)

“全文有哪些主要风险”需要覆盖全篇，而“退款期限是多少”偏向局部事实。SummaryIndex 与摘要树有助于全局覆盖，但对全部节点的处理可能比向量检索昂贵。摘要会压缩细节，不能用摘要替代需要精确金额、条款和例外的原文证据。

设计两条路径：概览问题读分层摘要，细节问题回到原始节点。摘要记录来源节点集合与生成版本；来源更新或删除必须使依赖摘要失效。层层摘要可能积累遗漏，应使用覆盖检查和代表性原文回查。

衡量摘要不仅看语言流畅，还看主题覆盖、事实一致、少数但关键的风险是否保留。一个占原文 1% 的免责条款可能比重复出现十次的背景介绍更重要，频率不能当作重要性的唯一标准。

## 重点与难点

重点：全局覆盖与局部精确分开设计。难点：摘要依赖失效与低频关键事实保留。

## 面试考点与参考回答

问：摘要索引能代替向量索引吗？答：取决于问题；它们适合不同访问模式，组合时要控制成本和证据回溯。

## 项目中的坑与处置

坑：原政策删除后摘要仍泄露旧内容。处置：维护派生依赖图并同步删除或重建。

## 动手实验与验收

对含低频重大风险的长文生成摘要。验收：重大风险不遗漏，每个结论可回溯到原段落。

## 代码实现补充：SummaryIndex 的全量证据基线

依赖：Python 3.10+；安装 `llama-index-core==0.14.25`。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
from llama_index.core import Document, SummaryIndex
from llama_index.core.llms import MockLLM

index = SummaryIndex.from_documents([
    Document(text="Q1: launched a search prototype.", id_="q1"),
    Document(text="Q2: added access control and regression evaluation.", id_="q2"),
])
hits = index.as_retriever().retrieve("Summarize progress across quarters")
assert {h.node.ref_doc_id for h in hits} == {"q1", "q2"}
engine = index.as_query_engine(response_mode="tree_summarize", llm=MockLLM(max_tokens=16))
response = engine.query("Summarize progress across quarters")
assert len(response.source_nodes) == 2
print({"retrieved": len(hits), "sources": len(response.source_nodes)})
```

### 实现说明、验收与项目边界

SummaryIndex 的默认检索返回所有节点，本例验证覆盖范围，不验证摘要准确性。tree_summarize 可以组织分层合成，但不会自动解决漏项与权限传播。文档增多时统计节点总数、模型调用数和输入 token，与向量检索基线比较成本。

首次运行提示：核心包 tokenizer 可能下载编码缓存；离线环境请预置缓存并设置 `TIKTOKEN_CACHE_DIR`。无需模型密钥不代表首次运行不联网。

## 完整代码实现补充：SummaryIndex 针对全局总结问题的完整实现与验证

Python 3.10+；`llama-index-core==0.14.25`。混合检索另需 `llama-index-retrievers-bm25==0.8.0`，SQL 依赖 SQLAlchemy，事件流依赖 `llama-index-workflows`（core 的依赖）。独立进程运行完整代码块；首次 tokenizer 初始化可能读取或下载缓存，请离线部署时预置 `TIKTOKEN_CACHE_DIR`。

离线夹具只验证接口、来源和控制流，不验证语义质量或安全性。启用真实模型的分支需额外安装 `llama-index-llms-openai`、`llama-index-embeddings-openai`，重排分支另需 `llama-index-postprocessor-sbert-rerank`；设置 `RUN_REAL_MODELS=1`、`OPENAI_API_KEY`、`LLM_MODEL`、`EMBED_MODEL`（按示例需要）。这些外部模型分支本次未运行。

```python
from llama_index.core import Document, SummaryIndex
from llama_index.core.llms import MockLLM
from llama_index.core.response_synthesizers import ResponseMode

llm = MockLLM(max_tokens=64)
docs = [
    Document(text="Chapter 1: Vision is high-availability enterprise cloud AI.", id_="ch_1"),
    Document(text="Chapter 2: Security relies on zero trust and tenant isolation.", id_="ch_2"),
    Document(text="Chapter 3: Compliance mandates automated audit logging.", id_="ch_3")
]

# SummaryIndex 不依赖向量计算，保存完整文档节点序列
summary_index = SummaryIndex.from_documents(docs)
retriever = summary_index.as_retriever()
retrieved_nodes = retriever.retrieve("Provide an executive summary")
assert len(retrieved_nodes) == 3

query_engine = summary_index.as_query_engine(
    llm=llm,
    response_mode=ResponseMode.TREE_SUMMARIZE
)
resp = query_engine.query("Summarize all core principles across chapters")
assert resp.source_nodes and len(resp.source_nodes) == 3

print("SummaryIndex verified: scanned all 3 chapters without vector dropouts.")
```

### 架构说明与工程边界

无需向量模型介入，通过 SummaryIndex 保存全文档拓扑序列，结合树状合成器实现对跨节战略总纲的无死角全量扫描；模拟模型仅验证流程。
