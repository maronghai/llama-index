# 01.03 Retriever、QueryEngine 与 ChatEngine / Retrievers, query engines, and chat engines

[返回全书目录 / Contents](../00-contents.md)

Retriever 返回候选证据，QueryEngine 将检索与响应合成连接起来，ChatEngine 还管理会话上下文。把它们视为不同职责，而不是三个可以随意互换的方法。QueryEngine 的单次调用通常不隐式维护聊天历史，但底层对象可以共享缓存或自定义状态，因此“无状态”是接口使用约定，不是绝对保证。

A retriever returns candidate evidence. A query engine combines retrieval with response synthesis. A chat engine additionally manages conversational context. These are separate responsibilities. A query call usually does not implicitly retain chat history, although underlying components can still share caches or custom state.

先调用 as_retriever().retrieve() 能隔离检索问题，再调用 as_query_engine().query() 观察生成。响应中的 source_nodes 通常是 NodeWithScore；score 可能为空，含义由后端决定，不能把所有分数都当余弦相似度，更不能跨库直接比较阈值。

Use as_retriever().retrieve() to isolate evidence selection, then as_query_engine().query() to inspect synthesis. Response source_nodes commonly contain NodeWithScore objects. Scores may be absent, and their meaning depends on the backend; do not assume every score is cosine similarity or transfer cutoffs between stores.

聊天中的“它呢”需要历史改写或上下文解释，但查询改写必须保留原始问题、身份范围和时间约束。历史文本也可能包含过时答案。系统应保存原始查询、检索查询和最终引用，才能判断错误发生在改写、检索还是生成。

Follow-up questions such as “what about it?” need contextual interpretation. Rewriting must preserve the original intent, authorization scope, and time constraints. History may contain stale answers. Record the original query, rewritten retrieval query, and final citations to locate failures.

## 示例与运行边界 / Example and execution scope

本节示例按正文所列前置条件运行；部分是组件片段，不构成完整应用。

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

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

## 重点与难点 / Key points and difficulties

重点：检索与生成分开测。难点：多轮指代消解不能扩大访问范围，也不能把历史回答当成新的权威来源。

Key: test retrieval and generation separately. Difficulty: conversational rewriting must not broaden access or treat prior answers as authoritative evidence.

## 面试考点与参考回答 / Interview question and answer

问：回答不对先换大模型吗？答：先看源节点是否包含正确证据；没有证据先修数据和检索，有证据再检查提示、截断、冲突与生成。

Q: Should a wrong answer trigger a model upgrade? A: first inspect source nodes. Missing evidence points to data or retrieval; present evidence points to prompts, truncation, conflicts, or generation.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：格式化 source.score 为小数时遇到 None 报错。处置：判空并同时记录 score 的定义、模型与检索配置。

Pitfall: formatting a missing score as a float crashes diagnostics. Handle None and log the score definition with the embedding and retrieval configuration.

## 动手实验与验收 / Exercise and acceptance criteria

对同一问题保存候选节点和最终答案，人工标注证据是否充分。验收：能提出一条与检索有关和一条与生成有关的独立改进。

Save retrieved nodes and the final answer for one question. Label evidence sufficiency. Acceptance: propose separate retrieval and generation improvements.

## 完整代码实现补充 / Code Implementation Supplement:Retriever、QueryEngine 与 ChatEngine 完整对比实现 / End-to-End Implementation of Retriever, QueryEngine, and ChatEngine

Python 3.10+；`llama-index-core==0.14.25`。混合检索另需 `llama-index-retrievers-bm25==0.8.0`，SQL 依赖 SQLAlchemy，事件流依赖 `llama-index-workflows`（core 的依赖）。独立进程运行完整代码块；首次 tokenizer 初始化可能读取或下载缓存，请离线部署时预置 `TIKTOKEN_CACHE_DIR`。

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

离线夹具只验证接口、来源和控制流，不验证语义质量或安全性。启用真实模型的分支需额外安装 `llama-index-llms-openai`、`llama-index-embeddings-openai`，重排分支另需 `llama-index-postprocessor-sbert-rerank`；设置 `RUN_REAL_MODELS=1`、`OPENAI_API_KEY`、`LLM_MODEL`、`EMBED_MODEL`（按示例需要）。这些外部模型分支本次未运行。

Offline fixtures validate interfaces, provenance, and control flow, not semantic quality or security. Real-model branches additionally require `llama-index-llms-openai`, `llama-index-embeddings-openai`, and, for reranking, `llama-index-postprocessor-sbert-rerank`; set `RUN_REAL_MODELS=1`, `OPENAI_API_KEY`, `LLM_MODEL`, and `EMBED_MODEL` as required by the block. External-model branches have not been executed in this revision.

```python
import hashlib
import math
import re
from llama_index.core.embeddings import MockEmbedding as _MockEmbedding

class MockEmbedding(_MockEmbedding):
    # Test-only hashed lexical vectors; NOT a semantic embedding model.
    def _vector(self, text):
        values = [0.0] * 256
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            slot = int(hashlib.sha256(word.encode()).hexdigest()[:8], 16) % 256
            values[slot] += 1.0
        norm = math.sqrt(sum(v*v for v in values)) or 1.0
        return [v / norm for v in values]
    def _get_text_embedding(self, text):
        return self._vector(text)
    def _get_query_embedding(self, query):
        return self._vector(query)
    async def _aget_query_embedding(self, query):
        return self._vector(query)

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.llms import MockLLM
from llama_index.core.schema import TextNode

embed_model = MockEmbedding(embed_dim=256)
llm = MockLLM(max_tokens=64)

nodes = [
    TextNode(text="Annual health checkup is scheduled every October.", id_="node_health"),
    TextNode(text="Gym reimbursement limit is 1000 CNY per employee per year.", id_="node_gym")
]
index = VectorStoreIndex(nodes, embed_model=embed_model)

# 1. Retriever: 纯证据检索器，无模型调用，返回 NodeWithScore
retriever = index.as_retriever(similarity_top_k=1)
retrieved = retriever.retrieve("gym reimbursement policy")
assert len(retrieved) == 1
assert retrieved[0].node.node_id == "node_gym"

# 2. QueryEngine: 单轮问答，执行 检索 -> 上下文装配 -> 合成回答
query_engine = index.as_query_engine(llm=llm, similarity_top_k=1)
query_resp = query_engine.query("What is the gym reimbursement policy?")
assert query_resp.source_nodes and len(query_resp.source_nodes) == 1
assert query_resp.source_nodes[0].node.node_id == "node_gym"

# 3. ChatEngine: 多轮会话引擎，自动维护对话记忆与上下文
chat_engine = index.as_chat_engine(llm=llm, chat_mode="context")
chat_resp_1 = chat_engine.chat("Tell me about gym benefits.")
assert chat_resp_1.source_nodes
chat_resp_2 = chat_engine.chat("What about health checkups?")
assert chat_resp_2.source_nodes

print("Engines successfully verified:")
print(f"- Retriever hit: {retrieved[0].node.node_id}")
print(f"- QueryEngine sources: {len(query_resp.source_nodes)}")
print(f"- ChatEngine rounds: {len(chat_engine.chat_history)}")
```

### 架构说明与工程边界 / Architecture and execution boundaries

演示底层索引如何分别派生出只读检索器 (Retriever)、单轮生成引擎 (QueryEngine) 与维护多轮上下文的对话引擎 (ChatEngine)，并分别校验检索命中与证据追溯。

Demonstrates deriving a read-only Retriever, a single-turn QueryEngine, and a context-maintaining ChatEngine from the same index, validating node retrieval and evidence citations.
