# 04.02 元数据、过滤与内容视图

[返回全书目录 / Contents](../00-contents.md)

元数据同时服务来源引用、权限过滤、生命周期管理和模型理解。建议最小模式包含 source_id、tenant_id、document_version、effective_from、language 和 heading_path。时间字段应约定时区和类型，金额字段保留单位；不要让同一个字段在不同记录中一会儿是数字一会儿是字符串。

LlamaIndex 可以分别控制嵌入和生成时包含哪些元数据。excluded_embed_metadata_keys 和 excluded_llm_metadata_keys 影响内容视图，不会自动删除数据库中的字段，也不是访问控制。隐藏 tenant_id 不会阻止跨租户检索；授权必须在可信服务端过滤，并在上下文组装前再次校验。

模型抽取标题、实体和摘要可提高检索，但会引入成本与错误。确定性字段如文件 ID、业务状态和 ACL 应来自可信源，不能由模型推断。抽取结果保存为派生字段，保留生成模型和提取版本，便于重新处理。

## 示例与运行边界

本节示例按正文所列前置条件运行；部分是组件片段，不构成完整应用。

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

## 重点与难点

重点：元数据有不同用途与信任等级。难点：存储字段、嵌入内容和模型上下文不是同一份视图。

## 面试考点与参考回答

问：为什么排除文件路径进入嵌入？答：路径可能引入噪声或敏感信息；但标题等语义字段可能有益，应按评估决定而不是全部删除。

## 项目中的坑与处置

坑：将客户端传入的 tenant_id 直接当授权过滤条件。处置：从已验证身份推导允许范围，客户端只能在该范围内收窄条件。

## 动手实验与验收

比较 MetadataMode.EMBED、LLM 和 NONE 的正文视图。验收：敏感路径不进入模型，tenant_id 仍存在于存储并用于服务端过滤。
