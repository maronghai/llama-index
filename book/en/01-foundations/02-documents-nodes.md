# 01.02 Documents, nodes, and provenance

[返回全书目录 / Contents](../00-contents.md)

A Document represents a source record, not necessarily a whole file: a PDF reader may produce one Document per page. A Node is a common unit for retrieval, embedding, and context construction. Content, metadata, and relationships should jointly identify the evidence source.

SentenceSplitter.get_nodes_from_documents creates nodes with source relationships. When constructing TextNode manually, explicitly assign NodeRelationship.SOURCE and RelatedNodeInfo. The expression node.relationships[node.relationships.keys()] from the original notes neither creates provenance nor supplies a valid relationship key.

Document IDs identify business sources, content hashes detect changes, and node IDs identify chunks. Stable document IDs with versioned node IDs make updates auditable. Page numbers, heading paths, and source offsets improve citations only when reliably supplied by parsing, not guessed by a model.

## Example and execution scope

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

## Key points and difficulties

Key: source relationships and business identity. Difficulty: mapping files to page documents and hierarchical nodes while removing obsolete chunks after updates.

## Interview question and answer

Q: Why separate Documents and Nodes? A: source management and retrieval use different granularities. Nodes allow targeted retrieval and bounded context while preserving provenance.

## Production pitfalls and mitigation

Pitfall: random document IDs on every import accumulate duplicate evidence. Derive IDs from source-system keys and track content revisions separately.

## Exercise and acceptance criteria

Run the example and inspect node.ref_doc_id. Rechunk the document and compare node counts and source IDs. Acceptance: every node resolves to its source, and source identity remains stable.
