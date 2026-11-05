# 02.02 离线链路冒烟测试

[返回全书目录 / Contents](../00-contents.md)

先证明对象可以流动，再证明语义检索有效。MockEmbedding 与 MockLLM 可用于不调用外部服务的链路测试，但模拟向量不表达真实语义，不能用其排名证明检索正确，也不能用模拟回答衡量忠实性。这是把软件连通性和 AI 质量分开测试。

下例创建两条政策，使用固定维度的模拟嵌入构建索引，再进行检索与查询。验收只检查非空响应、节点存在、来源关系以及对象类型。随后替换为真实嵌入模型，才开始比较“住宿”“酒店”等同义表达的召回。

任何“预期输出”都应区分确定性断言与生成文本。模型输出措辞可能变化，测试应围绕业务事实、引用和拒答，不要逐字匹配一段流畅答案。对于计费或写入接口，离线测试还应验证不会真的产生外部调用。

## 示例与运行边界

独立离线冒烟示例；需要 llama-index-core。Mock 结果不能证明语义质量。

```python
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM

embed = MockEmbedding(embed_dim=8)
docs = [
    Document(text="Hotel claims require itemized receipts.", id_="hotel"),
    Document(text="Meal claims require manager approval.", id_="meal"),
]
index = VectorStoreIndex.from_documents(docs, embed_model=embed)
hits = index.as_retriever(similarity_top_k=2).retrieve("hotel receipts")
assert hits and all(h.node.ref_doc_id for h in hits)
response = index.as_query_engine(llm=MockLLM(max_tokens=32)).query("hotel receipts")
print(type(response).__name__)
print([h.node.ref_doc_id for h in hits])
```

## 重点与难点

重点：Mock 只验证链路。难点：防止把“能跑”写成“效果好”，也防止弱测试掩盖真实检索问题。

## 面试考点与参考回答

问：没有 API 凭据如何开发？答：用 Mock 测组件编排和异常处理，用固定检索样本测业务逻辑；语义质量必须在真实模型条件下另测。

## 项目中的坑与处置

坑：模拟嵌入给所有文档近似相同向量，却报告 Recall@k 很高。处置：隔离冒烟集和质量集，禁止用 Mock 结果比较模型。

## 动手实验与验收

运行示例并打印来源 ID；将 embedding 维度改为另一个数，在新索引重建。验收：清楚解释为什么这不是嵌入模型质量实验。
