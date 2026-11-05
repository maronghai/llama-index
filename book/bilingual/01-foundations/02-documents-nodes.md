# 01.02 Document、Node 与证据溯源 / Documents, nodes, and provenance

[返回全书目录 / Contents](../00-contents.md)

Document 是来源记录的统一容器，不保证等于一个物理文件；PDF 读取器可能按页输出多个 Document。Node 是检索、嵌入与上下文组装的常见粒度。节点正文、元数据和关系应共同描述“这段证据来自哪里”，而不是只保存一串无法追溯的文本。

A Document represents a source record, not necessarily a whole file: a PDF reader may produce one Document per page. A Node is a common unit for retrieval, embedding, and context construction. Content, metadata, and relationships should jointly identify the evidence source.

使用 SentenceSplitter.get_nodes_from_documents 可由文档生成带来源关系的节点。手工构造 TextNode 时，不能假定框架知道其父文档；应显式设置 NodeRelationship.SOURCE 和 RelatedNodeInfo。原始笔记中的 node.relationships[node.relationships.keys()] 不能建立关系，且会把不可用的对象当键。

SentenceSplitter.get_nodes_from_documents creates nodes with source relationships. When constructing TextNode manually, explicitly assign NodeRelationship.SOURCE and RelatedNodeInfo. The expression node.relationships[node.relationships.keys()] from the original notes neither creates provenance nor supplies a valid relationship key.

文档 ID 标识业务来源，内容哈希表示版本变化，节点 ID 标识分块结果。三者职责不同。采用稳定文档 ID 加版本化节点 ID，可以解释一次更新删除了哪些旧节点。页码、标题路径和原文偏移有助于引用，但必须由解析器可靠提供；不要让模型猜页码。

Document IDs identify business sources, content hashes detect changes, and node IDs identify chunks. Stable document IDs with versioned node IDs make updates auditable. Page numbers, heading paths, and source offsets improve citations only when reliably supplied by parsing, not guessed by a model.

## 示例与运行边界 / Example and execution scope

本节示例按正文所列前置条件运行；部分是组件片段，不构成完整应用。

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

```python
from llama_index.core import Document
from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo

doc = Document(text="Travel policy: hotel receipts are required.", id_="policy:travel")
node = TextNode(text=doc.text, id_="policy:travel:v1:0")
node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=doc.id_)
assert node.ref_doc_id == doc.id_
print(node.ref_doc_id)
```

## 重点与难点 / Key points and difficulties

重点：来源关系与业务 ID。难点：一份文件、多页文档、多级节点之间的映射，以及更新后的旧节点清理。

Key: source relationships and business identity. Difficulty: mapping files to page documents and hierarchical nodes while removing obsolete chunks after updates.

## 面试考点与参考回答 / Interview question and answer

问：Document 和 Node 为什么分开？答：来源管理与检索粒度不同；节点让局部检索和上下文预算可控，同时保留指向来源的关系。

Q: Why separate Documents and Nodes? A: source management and retrieval use different granularities. Nodes allow targeted retrieval and bounded context while preserving provenance.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：每次导入随机生成 doc_id，增量同步会积累重复证据。处置：以来源系统主键构造稳定 ID，将内容版本单独记录。

Pitfall: random document IDs on every import accumulate duplicate evidence. Derive IDs from source-system keys and track content revisions separately.

## 动手实验与验收 / Exercise and acceptance criteria

运行下例并检查 node.ref_doc_id。再对文档重新切块，比较节点数与来源 ID。验收：每个节点能定位到源文档，来源 ID 不随重新切块变化。

Run the example and inspect node.ref_doc_id. Rechunk the document and compare node counts and source IDs. Acceptance: every node resolves to its source, and source identity remains stable.
