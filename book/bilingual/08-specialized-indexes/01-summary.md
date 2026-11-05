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
