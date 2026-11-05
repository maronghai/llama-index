# 02.03 接入真实模型与建立基线 / Real models and a measurable baseline

[返回全书目录 / Contents](../00-contents.md)

真实实验至少记录嵌入模型、生成模型、tokenizer、分块参数、语料快照和索引版本。嵌入模型决定语义空间，生成模型决定如何使用证据。两者可以来自不同服务，也可以本地部署；本地方案仍需要模型文件、内存和推理运行时，并非零依赖。

A real experiment records embedding and generation models, tokenizer, chunking, corpus snapshot, and index version. Embeddings define the retrieval space; generation determines how evidence is used. Providers may differ, or both may run locally. Local deployment still needs model files, memory, and an inference runtime.

以下使用 HuggingFaceEmbedding 的集成形式作为说明，需要 llama-index-embeddings-huggingface 和相应推理依赖。模型标识从环境变量读取，必须选择与语料语言、query/document 前缀约定和许可证相符的模型。首次加载可能联网下载；离线环境应预置经批准的模型路径。

The snippet illustrates HuggingFaceEmbedding and requires llama-index-embeddings-huggingface plus its inference dependencies. Read the model identifier from the environment and select a model suitable for the corpus language, query/document prefix convention, and license. Initial loading may download weights; offline deployments should provision an approved model path.

先固定生成配置，比较检索基线；再固定检索结果，比较生成质量。每次只改变一个主要因素。实验表应至少列出证据召回、回答正确率、拒答表现、延迟和成本。没有真实运行数据时，只写实验方案，不能填看似可信的成绩。

Hold generation fixed while comparing retrieval, then freeze retrieved evidence while comparing generation. Change one main factor per experiment. Track evidence recall, answer correctness, abstention, latency, and cost. If no run was performed, report an experiment plan rather than invented scores.

## 示例与运行边界 / Example and execution scope

本节示例按正文所列前置条件运行；部分是组件片段，不构成完整应用。

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

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

## 重点与难点 / Key points and difficulties

重点：模型、语料与配置共同构成实验版本。难点：不同嵌入模型可能需要不同文本前缀、归一化与最大长度。

Key: models, corpus, and configuration jointly define an experiment. Difficulty: embeddings may differ in prefix conventions, normalization, and maximum input length.

## 面试考点与参考回答 / Interview question and answer

问：同维度模型能直接替换吗？答：不能。同维度不代表同一个语义坐标系，文档和查询必须采用兼容模型与配置，通常需要重建索引。

Q: Can same-dimensional embeddings be swapped directly? A: no. Equal dimensionality does not mean compatible coordinates. Queries and documents need compatible models and settings, usually requiring reindexing.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：只替换查询侧嵌入，旧向量仍来自原模型，服务不报错但召回下降。处置：索引清单绑定模型身份，启动校验不一致就拒绝加载。

Pitfall: swapping only query embeddings silently degrades retrieval. Bind model identity to the index manifest and reject incompatible startup configurations.

## 动手实验与验收 / Exercise and acceptance criteria

用不少于 20 个含同义词、编号、无答案和时间条件的问题建立人工基线。验收：报告每类问题的错误，而不只报告总体平均值。

Create at least 20 labeled questions covering synonyms, identifiers, missing answers, and time conditions. Acceptance: report errors per category rather than only an overall average.
