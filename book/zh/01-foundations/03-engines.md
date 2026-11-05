# 01.03 Retriever、QueryEngine 与 ChatEngine

[返回全书目录 / Contents](../00-contents.md)

Retriever 返回候选证据，QueryEngine 将检索与响应合成连接起来，ChatEngine 还管理会话上下文。把它们视为不同职责，而不是三个可以随意互换的方法。QueryEngine 的单次调用通常不隐式维护聊天历史，但底层对象可以共享缓存或自定义状态，因此“无状态”是接口使用约定，不是绝对保证。

先调用 as_retriever().retrieve() 能隔离检索问题，再调用 as_query_engine().query() 观察生成。响应中的 source_nodes 通常是 NodeWithScore；score 可能为空，含义由后端决定，不能把所有分数都当余弦相似度，更不能跨库直接比较阈值。

聊天中的“它呢”需要历史改写或上下文解释，但查询改写必须保留原始问题、身份范围和时间约束。历史文本也可能包含过时答案。系统应保存原始查询、检索查询和最终引用，才能判断错误发生在改写、检索还是生成。

## 示例与运行边界

本节示例按正文所列前置条件运行；部分是组件片段，不构成完整应用。

```python
# Requires an initialized index; this is a component-level snippet.
retriever = index.as_retriever(similarity_top_k=5)
hits = retriever.retrieve("What receipts are required?")
for hit in hits:
    score = "n/a" if hit.score is None else f"{hit.score:.4f}"
    print(score, hit.node.get_content())
response = index.as_query_engine(similarity_top_k=5).query("What receipts are required?")
print(str(response))
```

## 重点与难点

重点：检索与生成分开测。难点：多轮指代消解不能扩大访问范围，也不能把历史回答当成新的权威来源。

## 面试考点与参考回答

问：回答不对先换大模型吗？答：先看源节点是否包含正确证据；没有证据先修数据和检索，有证据再检查提示、截断、冲突与生成。

## 项目中的坑与处置

坑：格式化 source.score 为小数时遇到 None 报错。处置：判空并同时记录 score 的定义、模型与检索配置。

## 动手实验与验收

对同一问题保存候选节点和最终答案，人工标注证据是否充分。验收：能提出一条与检索有关和一条与生成有关的独立改进。
