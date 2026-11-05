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
