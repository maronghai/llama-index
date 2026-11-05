# 01.03 Retrievers, query engines, and chat engines

[返回全书目录 / Contents](../00-contents.md)

A retriever returns candidate evidence. A query engine combines retrieval with response synthesis. A chat engine additionally manages conversational context. These are separate responsibilities. A query call usually does not implicitly retain chat history, although underlying components can still share caches or custom state.

Use as_retriever().retrieve() to isolate evidence selection, then as_query_engine().query() to inspect synthesis. Response source_nodes commonly contain NodeWithScore objects. Scores may be absent, and their meaning depends on the backend; do not assume every score is cosine similarity or transfer cutoffs between stores.

Follow-up questions such as “what about it?” need contextual interpretation. Rewriting must preserve the original intent, authorization scope, and time constraints. History may contain stale answers. Record the original query, rewritten retrieval query, and final citations to locate failures.

## Example and execution scope

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

## Key points and difficulties

Key: test retrieval and generation separately. Difficulty: conversational rewriting must not broaden access or treat prior answers as authoritative evidence.

## Interview question and answer

Q: Should a wrong answer trigger a model upgrade? A: first inspect source nodes. Missing evidence points to data or retrieval; present evidence points to prompts, truncation, conflicts, or generation.

## Production pitfalls and mitigation

Pitfall: formatting a missing score as a float crashes diagnostics. Handle None and log the score definition with the embedding and retrieval configuration.

## Exercise and acceptance criteria

Save retrieved nodes and the final answer for one question. Label evidence sufficiency. Acceptance: propose separate retrieval and generation improvements.

## Code Implementation Supplement:End-to-End Implementation of Retriever, QueryEngine, and ChatEngine

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

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

### Architecture and execution boundaries

Demonstrates deriving a read-only Retriever, a single-turn QueryEngine, and a context-maintaining ChatEngine from the same index, validating node retrieval and evidence citations.
