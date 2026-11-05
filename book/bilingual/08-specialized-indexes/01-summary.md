# 08.01 SummaryIndex 与全局问题 / SummaryIndex and global questions

[返回全书目录 / Contents](../00-contents.md)

“全文有哪些主要风险”需要覆盖全篇，而“退款期限是多少”偏向局部事实。SummaryIndex 与摘要树有助于全局覆盖，但对全部节点的处理可能比向量检索昂贵。摘要会压缩细节，不能用摘要替代需要精确金额、条款和例外的原文证据。

Global questions need broad coverage, unlike local fact lookup. SummaryIndex and summary trees can support coverage at higher processing cost than selective retrieval. Summaries compress detail and should not replace original clauses for precise amounts or exceptions.

设计两条路径：概览问题读分层摘要，细节问题回到原始节点。摘要记录来源节点集合与生成版本；来源更新或删除必须使依赖摘要失效。层层摘要可能积累遗漏，应使用覆盖检查和代表性原文回查。

Use summary paths for overviews and original nodes for details. Record source-node dependencies and summary versions. Updates and deletions invalidate derived summaries. Hierarchical summarization can accumulate omissions, requiring coverage checks and source review.

衡量摘要不仅看语言流畅，还看主题覆盖、事实一致、少数但关键的风险是否保留。一个占原文 1% 的免责条款可能比重复出现十次的背景介绍更重要，频率不能当作重要性的唯一标准。

Evaluate coverage, consistency, and preservation of rare but critical risks, not just fluency. A short exclusion may matter more than repeated background. Frequency alone does not establish importance.

## 重点与难点 / Key points and difficulties

重点：全局覆盖与局部精确分开设计。难点：摘要依赖失效与低频关键事实保留。

Key: distinguish broad coverage from precise facts. Difficulty: dependency invalidation and rare critical details.

## 面试考点与参考回答 / Interview question and answer

问：摘要索引能代替向量索引吗？答：取决于问题；它们适合不同访问模式，组合时要控制成本和证据回溯。

Q: Can summary indexes replace vector indexes? A: they support different query patterns; combinations need cost control and traceability.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：原政策删除后摘要仍泄露旧内容。处置：维护派生依赖图并同步删除或重建。

Pitfall: summaries expose deleted policy content. Track dependencies and invalidate or rebuild derived data.

## 动手实验与验收 / Exercise and acceptance criteria

对含低频重大风险的长文生成摘要。验收：重大风险不遗漏，每个结论可回溯到原段落。

Summarize a document with rare major risks. Acceptance: preserve those risks and trace every conclusion to a passage.

## 代码实现补充 / Implementation supplement: SummaryIndex 的全量证据基线 / A full-evidence SummaryIndex baseline

依赖 / Dependencies: Python 3.10+; `llama-index-core==0.14.25`。

将完整代码保存为独立 `.py` 文件，在独立进程执行 `python filename.py`。无需密钥，无付费调用；验收为断言通过并输出结果。

Save the full block as a standalone `.py` file and run it in a separate process. No API key or paid call is needed; assertions must pass and results are printed.

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

### 实现说明、验收与项目边界 / Implementation, acceptance and production boundaries

SummaryIndex 的默认检索返回所有节点，本例验证覆盖范围，不验证摘要准确性。tree_summarize 可以组织分层合成，但不会自动解决漏项与权限传播。文档增多时统计节点总数、模型调用数和输入 token，与向量检索基线比较成本。

Default SummaryIndex retrieval returns all nodes. This checks coverage, not summary accuracy. tree_summarize organizes hierarchical synthesis but cannot guarantee completeness or permission propagation. As the corpus grows, compare node counts, calls and input tokens against vector retrieval.

首次运行 / First run：tokenizer 可能下载编码缓存。离线运行需预置缓存并设置 `TIKTOKEN_CACHE_DIR`。Tokenization may download an encoding cache; provision it before offline use.

## 完整代码实现补充 / Code Implementation Supplement:SummaryIndex 针对全局总结问题的完整实现与验证 / SummaryIndex Full Implementation for Global Synthesis Queries

Python 3.10+；`llama-index-core==0.14.25`。混合检索另需 `llama-index-retrievers-bm25==0.8.0`，SQL 依赖 SQLAlchemy，事件流依赖 `llama-index-workflows`（core 的依赖）。独立进程运行完整代码块；首次 tokenizer 初始化可能读取或下载缓存，请离线部署时预置 `TIKTOKEN_CACHE_DIR`。

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

离线夹具只验证接口、来源和控制流，不验证语义质量或安全性。启用真实模型的分支需额外安装 `llama-index-llms-openai`、`llama-index-embeddings-openai`，重排分支另需 `llama-index-postprocessor-sbert-rerank`；设置 `RUN_REAL_MODELS=1`、`OPENAI_API_KEY`、`LLM_MODEL`、`EMBED_MODEL`（按示例需要）。这些外部模型分支本次未运行。

Offline fixtures validate interfaces, provenance, and control flow, not semantic quality or security. Real-model branches additionally require `llama-index-llms-openai`, `llama-index-embeddings-openai`, and, for reranking, `llama-index-postprocessor-sbert-rerank`; set `RUN_REAL_MODELS=1`, `OPENAI_API_KEY`, `LLM_MODEL`, and `EMBED_MODEL` as required by the block. External-model branches have not been executed in this revision.

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

### 架构说明与工程边界 / Architecture and execution boundaries

无需向量模型介入，通过 SummaryIndex 保存全文档拓扑序列，结合树状合成器实现对跨节战略总纲的无死角全量扫描；模拟模型仅验证流程。

Operates without vector embeddings by preserving document sequence in SummaryIndex, pairing with tree summarization for full-corpus traversal; the mock tests orchestration only.
