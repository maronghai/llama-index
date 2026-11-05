# 03.03 PDF、表格、图像与解析质量 / PDFs, tables, images, and parsing quality

[返回全书目录 / Contents](../00-contents.md)

复杂文档的关键是保留结构，而不是尽可能多地抽出字符。两栏 PDF 需要正确阅读顺序，表格需要保留列标题与单位，扫描页需要 OCR，图表需要能回溯到原页的描述。托管解析服务与本地解析各有成本、隐私、延迟和版面能力边界，应通过样本评测选择。

Complex parsing is about preserving structure, not maximizing extracted character count. Two-column PDFs need reading order, tables need headers and units, scans need OCR, and chart descriptions need page provenance. Compare hosted and local parsers on representative samples, including cost, privacy, latency, and layout fidelity.

例如“销售额 120”如果丢掉“万元”和“2025 年”就会产生错误答案。把表头、行键、时间、单位和脚注一起保存，必要时把表格行转成带列名的文本。对金额计算，优先从结构化数据执行确定性计算，再由模型解释，而不是让模型心算。

A value such as sales 120 becomes misleading when its unit and reporting year disappear. Preserve headers, row keys, time, units, and footnotes. When useful, serialize rows with explicit column names. For financial calculations, compute from structured data deterministically and let the model explain the result.

质量检查应从业务问题反推：条款是否完整、表格单元格是否对应、页码能否定位、图片中是否含必要证据。多模态检索与“把图片描述转成文本检索”不是同一种方案；前者需要兼容的图文表示，后者会受描述遗漏影响。

Validate parsing against business tasks: clause completeness, table-cell alignment, reliable page locations, and image-only evidence. Multimodal retrieval differs from indexing generated image descriptions: the former needs compatible representations, while the latter can lose facts during captioning.

## 重点与难点 / Key points and difficulties

重点：版面、单位与出处。难点：跨页表格、嵌套表头和图表描述中的信息损失无法靠扩大 top-k 修复。

Key: layout, units, and provenance. Difficulty: cross-page tables and caption omissions are parsing losses that a larger top-k cannot repair.

## 面试考点与参考回答 / Interview question and answer

问：PDF RAG 为什么难？答：PDF 保存视觉布局而不保证逻辑结构；必须把阅读顺序、表格、OCR 和来源映射纳入评估。

Q: Why is PDF RAG difficult? A: visual layout does not guarantee logical structure. Evaluate reading order, tables, OCR, and provenance explicitly.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：把模型生成的表格解释当成原始事实。处置：区分原文、结构化提取和推导描述，并给每种结果记录生成方式和置信边界。

Pitfall: treating generated table explanations as source facts. Distinguish original content, structured extraction, and derived descriptions, with provenance for each.

## 动手实验与验收 / Exercise and acceptance criteria

选取含两栏、跨页表格、扫描页的三份样本，人工核对十个事实。验收：每个事实可定位原页、单位不丢失，失败样本有明确处理策略。

Select samples with columns, cross-page tables, and scanned pages; verify ten facts manually. Acceptance: source-page traceability, preserved units, and explicit handling for failures.
