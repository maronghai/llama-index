# 04.02 Metadata, filtering, and content views

[返回全书目录 / Contents](../00-contents.md)

Metadata supports citations, authorization, lifecycle management, and model context. A useful schema includes source_id, tenant_id, document_version, effective_from, language, and heading_path. Define time zones and types, preserve monetary units, and avoid mixed numeric and string representations for the same field.

LlamaIndex can control metadata included in embedding and LLM views through exclusion lists. These views do not delete stored fields and are not authorization controls. Hiding tenant_id from prompts does not prevent cross-tenant retrieval. Enforce access server-side and validate evidence before context assembly.

Model-extracted titles, entities, and summaries can improve retrieval but add cost and errors. Deterministic fields such as IDs, business status, and ACLs must come from trusted systems. Store extracted attributes as derived fields with model and transformation versions.

## Example and execution scope

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

```python
from llama_index.core import Document
from llama_index.core.schema import MetadataMode
doc = Document(
    text="A receipt is required.",
    metadata={"tenant_id": "acme", "heading": "Travel", "internal_path": "private"},
    excluded_embed_metadata_keys=["tenant_id", "internal_path"],
    excluded_llm_metadata_keys=["tenant_id", "internal_path"],
)
print(doc.get_content(metadata_mode=MetadataMode.EMBED))
print(doc.metadata["tenant_id"])
```

## Key points and difficulties

Key: metadata has different uses and trust levels. Difficulty: stored fields, embedding input, and generation context are distinct views.

## Interview question and answer

Q: Why exclude paths from embeddings? A: paths may add noise or sensitive information; semantic fields such as headings may help, so evaluate selectively.

## Production pitfalls and mitigation

Pitfall: trusting client-provided tenant_id as authorization. Derive scope from verified identity and let clients only narrow it.

## Exercise and acceptance criteria

Compare EMBED, LLM, and NONE content views. Acceptance: sensitive paths remain out of model input while tenant_id remains available for trusted filtering.
