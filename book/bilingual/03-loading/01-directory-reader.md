# 03.01 使用 SimpleDirectoryReader / Using SimpleDirectoryReader

[返回全书目录 / Contents](../00-contents.md)

SimpleDirectoryReader 适合目录型导入，支持指定文件、递归扫描和扩展名筛选，但不同格式的解析能力取决于已安装读取器。它不是万能 OCR。读取 PDF 成功只表示产生了对象，不能证明表格、扫描文字或阅读顺序被正确还原。

SimpleDirectoryReader supports directory ingestion, explicit file lists, recursion, and extension filters. Format support depends on installed readers; it is not universal OCR. A successfully loaded PDF does not prove tables, scanned text, or reading order were preserved.

先限定导入边界：只读取已批准目录和扩展名，排除临时文件、密钥、重复副本与导出缓存。文件元数据函数可注入业务来源 ID，但不能盲目信任文件名就是唯一 ID。相对路径在目录迁移后会改变；有业务主键时应优先使用它。

Define ingestion boundaries first: approved directories and extensions, with temporary files, secrets, duplicate copies, and caches excluded. Metadata hooks can supply business identifiers, but filenames are not automatically unique. Relative paths change when folders move; prefer business keys when available.

采用加载清单统计文件数、文档数、字符数、失败数和每个来源的解析器版本。空白文档应进入异常队列。正文中的乱码不能仅靠删除异常字符处理，必须检查编码、字体映射和解析器。批量读取异常不能无声跳过，否则问答系统会把缺失知识误判为“没有相关政策”。

Record file count, document count, character count, failures, and parser versions. Route blank output to an exception queue. Garbled text requires investigating encoding, font mappings, or parsing rather than simply deleting characters. Silent skips turn ingestion failures into misleading knowledge gaps.

## 示例与运行边界 / Example and execution scope

本节示例按正文所列前置条件运行；部分是组件片段，不构成完整应用。

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

```python
# Requires an existing approved input directory.
from llama_index.core import SimpleDirectoryReader
reader = SimpleDirectoryReader(
    input_dir="./approved_data",
    recursive=True,
    required_exts=[".txt", ".md"],
    filename_as_id=True,
)
documents = reader.load_data()
for doc in documents:
    if not doc.text.strip():
        raise ValueError(f"Blank source: {doc.id_}")
print("documents:", len(documents))
```

## 重点与难点 / Key points and difficulties

重点：输入范围与解析验收。难点：一个文件可能生成多条 Document，文件数量不能直接作为文档数量断言。

Key: bound inputs and validate parsing. Difficulty: one file may create multiple Documents, so file counts and document counts are not interchangeable.

## 面试考点与参考回答 / Interview question and answer

问：为什么读取成功但问答失败？答：正文可能为空、表格错序、页眉淹没内容，或根本未切到包含答案的段落，应先抽查解析文本。

Q: Why does QA fail after loading succeeds? A: text may be blank, tables scrambled, headers dominant, or relevant content omitted. Inspect parsed text before tuning generation.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：递归导入整个项目，连私密配置和旧版本都进入索引。处置：白名单输入、来源清单、重复检测和权限校验。

Pitfall: recursively ingesting a project captures secrets and obsolete copies. Use allowlists, manifests, deduplication, and permission checks.

## 动手实验与验收 / Exercise and acceptance criteria

准备 UTF-8 文本、Markdown、空白文件和两个同名文件，记录加载结果。验收：来源唯一、空白有告警、失败不被当成功。

Prepare UTF-8 text, Markdown, an empty file, and duplicate filenames in different folders. Acceptance: unique provenance, blank-file alerts, and explicit failures.
