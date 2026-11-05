# 02.03 接入真实模型与建立基线

[返回全书目录 / Contents](../00-contents.md)

真实实验至少记录嵌入模型、生成模型、tokenizer、分块参数、语料快照和索引版本。嵌入模型决定语义空间，生成模型决定如何使用证据。两者可以来自不同服务，也可以本地部署；本地方案仍需要模型文件、内存和推理运行时，并非零依赖。

以下使用 HuggingFaceEmbedding 的集成形式作为说明，需要 llama-index-embeddings-huggingface 和相应推理依赖。模型标识从环境变量读取，必须选择与语料语言、query/document 前缀约定和许可证相符的模型。首次加载可能联网下载；离线环境应预置经批准的模型路径。

先固定生成配置，比较检索基线；再固定检索结果，比较生成质量。每次只改变一个主要因素。实验表应至少列出证据召回、回答正确率、拒答表现、延迟和成本。没有真实运行数据时，只写实验方案，不能填看似可信的成绩。

## 示例与运行边界

本节示例按正文所列前置条件运行；部分是组件片段，不构成完整应用。

```python
# Integration snippet; model weights and dependencies must be provisioned.
import os
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Document, VectorStoreIndex

embed = HuggingFaceEmbedding(model_name=os.environ["EMBED_MODEL"])
index = VectorStoreIndex.from_documents(
    [Document(text="Hotel claims require receipts.", id_="hotel")],
    embed_model=embed,
)
print(index.as_retriever(similarity_top_k=1).retrieve("hotel documentation"))
```

## 重点与难点

重点：模型、语料与配置共同构成实验版本。难点：不同嵌入模型可能需要不同文本前缀、归一化与最大长度。

## 面试考点与参考回答

问：同维度模型能直接替换吗？答：不能。同维度不代表同一个语义坐标系，文档和查询必须采用兼容模型与配置，通常需要重建索引。

## 项目中的坑与处置

坑：只替换查询侧嵌入，旧向量仍来自原模型，服务不报错但召回下降。处置：索引清单绑定模型身份，启动校验不一致就拒绝加载。

## 动手实验与验收

用不少于 20 个含同义词、编号、无答案和时间条件的问题建立人工基线。验收：报告每类问题的错误，而不只报告总体平均值。
