# 07.01 父文档恢复与句子窗口 / Parent recovery and sentence windows

[返回全书目录 / Contents](../00-contents.md)

检索粒度与生成粒度不必相同。句子窗口检索用短句表示精确命中，再把周围句子作为生成上下文；父文档恢复先命中叶节点，再获取更完整的父段落。这样能保留条件和解释，避免把所有嵌入都扩大到整章。

Retrieval and generation need not use the same granularity. Sentence-window retrieval matches short text then expands neighboring sentences. Parent recovery retrieves leaves and restores a broader parent passage. Both retain conditions without embedding entire chapters.

句子窗口通常把窗口正文放在元数据中，后处理时替换节点内容；窗口字段应排除出嵌入，否则实际检索粒度又变大。层级方案需要持久化所有相关节点和父子关系。多个叶节点属于同一父块时应合并去重，再检查预算。

Window text is often stored in metadata and substituted during postprocessing. Exclude the window field from embedding to preserve narrow retrieval. Hierarchical methods require persisted nodes and parent-child relations. Merge overlapping parents before budgeting context.

扩展得到的上下文仍必须满足授权与版本要求。不能因为某一句可见，就把包含受限内容的整个父文档一并送给模型。对混合权限文档，分块与访问边界要提前对齐。

Expanded context must still satisfy authorization and version constraints. Visibility of one sentence does not authorize its whole parent document. Align chunk boundaries with access boundaries when documents contain mixed permissions.

## 重点与难点 / Key points and difficulties

重点：精确召回与完整生成分离。难点：扩展后的去重、权限和 token 预算。

Key: narrow matching with broader synthesis. Difficulty: deduplication, permissions, and token budgets after expansion.

## 面试考点与参考回答 / Interview question and answer

问：为什么父块不直接做向量？答：父块可能过长并稀释语义；叶块负责定位，父块提供解释上下文，但需通过评测判断收益。

Q: Why not embed parents directly? A: large parents may dilute semantics; leaves locate evidence and parents supply context, subject to measured benefit.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：只保存叶向量，没有父节点正文。处置：恢复测试覆盖父节点查找，构建时校验关系完整。

Pitfall: leaf vectors survive but parent text is missing. Validate relationships at build time and test parent restoration.

## 动手实验与验收 / Exercise and acceptance criteria

构造一条规则及后面的例外，比较仅句子、窗口和父块。验收：例外被保留，重复窗口不会重复消耗上下文。

Compare sentence-only, window, and parent retrieval on a rule followed by an exception. Acceptance: preserve the exception without duplicated context.
