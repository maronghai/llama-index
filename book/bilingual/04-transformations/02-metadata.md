# 04.02 元数据、过滤与内容视图 / Metadata, filtering, and content views

[返回全书目录 / Contents](../00-contents.md)

元数据同时服务来源引用、权限过滤、生命周期管理和模型理解。建议最小模式包含 source_id、tenant_id、document_version、effective_from、language 和 heading_path。时间字段应约定时区和类型，金额字段保留单位；不要让同一个字段在不同记录中一会儿是数字一会儿是字符串。

Metadata supports citations, authorization, lifecycle management, and model context. A useful schema includes source_id, tenant_id, document_version, effective_from, language, and heading_path. Define time zones and types, preserve monetary units, and avoid mixed numeric and string representations for the same field.

LlamaIndex 可以分别控制嵌入和生成时包含哪些元数据。excluded_embed_metadata_keys 和 excluded_llm_metadata_keys 影响内容视图，不会自动删除数据库中的字段，也不是访问控制。隐藏 tenant_id 不会阻止跨租户检索；授权必须在可信服务端过滤，并在上下文组装前再次校验。

LlamaIndex can control metadata included in embedding and LLM views through exclusion lists. These views do not delete stored fields and are not authorization controls. Hiding tenant_id from prompts does not prevent cross-tenant retrieval. Enforce access server-side and validate evidence before context assembly.

模型抽取标题、实体和摘要可提高检索，但会引入成本与错误。确定性字段如文件 ID、业务状态和 ACL 应来自可信源，不能由模型推断。抽取结果保存为派生字段，保留生成模型和提取版本，便于重新处理。

Model-extracted titles, entities, and summaries can improve retrieval but add cost and errors. Deterministic fields such as IDs, business status, and ACLs must come from trusted systems. Store extracted attributes as derived fields with model and transformation versions.

## 示例与运行边界 / Example and execution scope

本节示例按正文所列前置条件运行；部分是组件片段，不构成完整应用。

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

## 重点与难点 / Key points and difficulties

重点：元数据有不同用途与信任等级。难点：存储字段、嵌入内容和模型上下文不是同一份视图。

Key: metadata has different uses and trust levels. Difficulty: stored fields, embedding input, and generation context are distinct views.

## 面试考点与参考回答 / Interview question and answer

问：为什么排除文件路径进入嵌入？答：路径可能引入噪声或敏感信息；但标题等语义字段可能有益，应按评估决定而不是全部删除。

Q: Why exclude paths from embeddings? A: paths may add noise or sensitive information; semantic fields such as headings may help, so evaluate selectively.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：将客户端传入的 tenant_id 直接当授权过滤条件。处置：从已验证身份推导允许范围，客户端只能在该范围内收窄条件。

Pitfall: trusting client-provided tenant_id as authorization. Derive scope from verified identity and let clients only narrow it.

## 动手实验与验收 / Exercise and acceptance criteria

比较 MetadataMode.EMBED、LLM 和 NONE 的正文视图。验收：敏感路径不进入模型，tenant_id 仍存在于存储并用于服务端过滤。

Compare EMBED, LLM, and NONE content views. Acceptance: sensitive paths remain out of model input while tenant_id remains available for trusted filtering.
