# 09.03 Conversation memory, compression, and isolation

[返回全书目录 / Contents](../00-contents.md)

Memory supports reference resolution and continuity, not authoritative facts. Full history increases tokens and privacy exposure; windows can drop constraints; summaries can distort them. Separate preferences, task state, and recent messages instead of concatenating everything.

Bind sessions to users, tenants, and authorization scope. Trusting a client-supplied session ID can expose another conversation. Apply retention, deletion, and sensitive-data policies to both message and vector memory. Distinguish confirmed preferences from model inference.

Permission changes can leave restricted material in history. Revalidate context, rebuild scope, or expire sessions when necessary. Store tool execution status reliably rather than relying on a summary to remember whether a write completed.

## Key points and difficulties

Key: layered memory bound to identity. Difficulty: faithful compression, revocation, and isolation.

## Interview question and answer

Q: Is more memory always better? A: no; stale and redundant information adds cost and distraction. Keep relevant, authorized context.

## Production pitfalls and mitigation

Pitfall: sharing chat history across users. Isolate session state and test concurrent and forged-session cases.

## Exercise and acceptance criteria

Interleave conversations from two users and revoke one scope. Acceptance: no cross-talk or revoked evidence in later context.

## Implementation supplement: Bounded memory isolated by tenant and session

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
from collections import defaultdict

class SessionMemory:
    def __init__(self, max_chars=120):
        self.data = defaultdict(list)
        self.max_chars = max_chars

    def append(self, tenant, user, session, role, text):
        if role not in {"user", "assistant"}:
            raise ValueError("untrusted role")
        if len(text) > self.max_chars:
            raise ValueError("message too long")
        key = (tenant, user, session)
        self.data[key].append({"role": role, "content": text})
        while sum(len(x["content"]) for x in self.data[key]) > self.max_chars:
            self.data[key].pop(0)

    def read(self, tenant, user, session):
        return [dict(x) for x in self.data.get((tenant, user, session), [])]

memory = SessionMemory()
memory.append("a", "u1", "s1", "user", "Hotel policy?")
assert memory.read("b", "u1", "s1") == []
assert memory.read("a", "u2", "s1") == []
assert len(memory.read("a", "u1", "s1")) == 1
print(memory.read("a", "u1", "s1"))
```

### Implementation, acceptance and production boundaries

This illustrates a storage adapter, not the current LlamaIndex Memory API. Convert read results into ChatMessage objects before calling a chat engine. Character limits are illustrative; production needs token budgets, complete-turn trimming, TTL, encryption, concurrency control and deletion, including summaries.

## Code Implementation Supplement:ChatMemoryBuffer Window Token Throttling and Session Snapshot Persistence

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

Offline fixtures validate interfaces, provenance, and control flow, not semantic quality or security. Real-model branches additionally require `llama-index-llms-openai`, `llama-index-embeddings-openai`, and, for reranking, `llama-index-postprocessor-sbert-rerank`; set `RUN_REAL_MODELS=1`, `OPENAI_API_KEY`, `LLM_MODEL`, and `EMBED_MODEL` as required by the block. External-model branches have not been executed in this revision.

```python
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.base.llms.types import ChatMessage, MessageRole

# 构造带严格 Token 预算的会话缓冲器
memory = ChatMemoryBuffer.from_defaults(token_limit=120)

# 写入多轮对话历史
memory.put(ChatMessage(role=MessageRole.USER, content="Hello, I need to check my leave allowance."))
memory.put(ChatMessage(role=MessageRole.ASSISTANT, content="You have 15 days of annual leave remaining."))
memory.put(ChatMessage(role=MessageRole.USER, content="Can I carry over unused leave to next year?"))
memory.put(ChatMessage(role=MessageRole.ASSISTANT, content="Yes, up to 5 days can be carried over."))

history = memory.get()
assert len(history) > 0

# 提取稳定会话快照 (Portable Snapshot) 用于存储或跨服务传递
snapshot = [{"role": msg.role.value, "content": msg.content} for msg in history]

# 恢复至新的内存实例
restored_memory = ChatMemoryBuffer.from_defaults(token_limit=120)
for item in snapshot:
    restored_memory.put(ChatMessage(role=MessageRole(item["role"]), content=item["content"]))

assert len(restored_memory.get()) == len(history)
print(f"ChatMemoryBuffer verified: {len(history)} messages preserved and restored.")

# Force truncation using a predictable test tokenizer, not production token estimates.
limited = ChatMemoryBuffer.from_defaults(token_limit=20, tokenizer_fn=lambda t: t.split())
for i in range(8):
    limited.put(ChatMessage(role=MessageRole.USER, content=f'Question {i} about annual leave'))
    limited.put(ChatMessage(role=MessageRole.ASSISTANT, content=f'Answer {i} please check policy'))
assert 0 < len(limited.get()) < len(limited.get_all())
# Budgeting returns a window; it does not erase historical storage.
assert len(limited.get_all()) == 16
sessions = {('finance', 'alice', 'session1'): limited,
            ('hr', 'alice', 'session1'): ChatMemoryBuffer.from_defaults(token_limit=20)}
assert sessions[('hr', 'alice', 'session1')].get_all() == []
print({'retained': len(limited.get()), 'stored': len(limited.get_all())})
```

### Architecture and execution boundaries

Actually triggers context trimming and distinguishes get from get_all. The snapshot preserves text roles and content, not arbitrary multimodal messages. ChatMemoryBuffer is a legacy-compatible API; consider Memory for new projects. Scope storage by tenant, user, and session, and implement history deletion separately.
