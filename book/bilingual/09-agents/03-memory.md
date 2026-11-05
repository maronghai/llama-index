# 09.03 会话记忆、压缩与隔离 / Conversation memory, compression, and isolation

[返回全书目录 / Contents](../00-contents.md)

对话记忆解决多轮指代和任务连续性，不是可靠事实库。完整历史会增加 token 与隐私暴露；滑动窗口可能忘记关键约束；摘要压缩会引入失真。将稳定用户偏好、任务状态和近期消息分开管理，比把一切拼接到提示更可控。

Memory supports reference resolution and continuity, not authoritative facts. Full history increases tokens and privacy exposure; windows can drop constraints; summaries can distort them. Separate preferences, task state, and recent messages instead of concatenating everything.

会话标识需要同时绑定用户、租户与授权范围。仅以浏览器传来的 session_id 读取历史可能导致越权。历史与向量记忆都需要保留期限、删除机制和敏感信息策略。模型生成的“用户偏好”也要区分确认事实与推断。

Bind sessions to users, tenants, and authorization scope. Trusting a client-supplied session ID can expose another conversation. Apply retention, deletion, and sensitive-data policies to both message and vector memory. Distinguish confirmed preferences from model inference.

权限变化后，历史中已出现的受限材料可能继续被模型引用。重新校验上下文或重建会话范围，必要时使旧会话失效。工具执行状态应放在可靠状态存储，不要依赖对话摘要记住某次写入是否已经完成。

Permission changes can leave restricted material in history. Revalidate context, rebuild scope, or expire sessions when necessary. Store tool execution status reliably rather than relying on a summary to remember whether a write completed.

## 重点与难点 / Key points and difficulties

重点：记忆分层并绑定身份。难点：压缩保真、撤权后历史清理和跨会话隔离。

Key: layered memory bound to identity. Difficulty: faithful compression, revocation, and isolation.

## 面试考点与参考回答 / Interview question and answer

问：记忆越长越好吗？答：不是，冗余与过时信息会增加成本和干扰；保留与当前任务相关且经过授权的内容。

Q: Is more memory always better? A: no; stale and redundant information adds cost and distraction. Keep relevant, authorized context.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：所有用户共用一个 ChatEngine 实例和历史。处置：按会话隔离状态，测试并发请求与随机 session_id 的负例。

Pitfall: sharing chat history across users. Isolate session state and test concurrent and forged-session cases.

## 动手实验与验收 / Exercise and acceptance criteria

运行两位用户的交错会话，再撤销其中一位权限。验收：无串话，撤权材料不进入后续上下文。

Interleave conversations from two users and revoke one scope. Acceptance: no cross-talk or revoked evidence in later context.

## 代码实现补充 / Implementation supplement: 按租户与会话隔离的有界记忆 / Bounded memory isolated by tenant and session

依赖 / Dependencies: Python 3.10+; 仅标准库 / standard library only.

将完整代码保存为独立 `.py` 文件，在独立进程执行 `python filename.py`。无需密钥，无付费调用；验收为断言通过并输出结果。

Save the full block as a standalone `.py` file and run it in a separate process. No API key or paid call is needed; assertions must pass and results are printed.

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

### 实现说明、验收与项目边界 / Implementation, acceptance and production boundaries

这是内存存储适配层示例，不是对当前 LlamaIndex Memory API 的封装。接入聊天引擎前把 read 的结果转换为 ChatMessage。字符预算仅供演示，生产应使用模型 tokenizer，按完整对话轮裁剪，加 TTL、加密、并发控制和删除接口；摘要也继承租户与删除要求。

This illustrates a storage adapter, not the current LlamaIndex Memory API. Convert read results into ChatMessage objects before calling a chat engine. Character limits are illustrative; production needs token budgets, complete-turn trimming, TTL, encryption, concurrency control and deletion, including summaries.

## 完整代码实现补充 / Code Implementation Supplement:ChatMemoryBuffer 窗口 Token 限流与会话快照持久化 / ChatMemoryBuffer Window Token Throttling and Session Snapshot Persistence

Python 3.10+；`llama-index-core==0.14.25`。混合检索另需 `llama-index-retrievers-bm25==0.8.0`，SQL 依赖 SQLAlchemy，事件流依赖 `llama-index-workflows`（core 的依赖）。独立进程运行完整代码块；首次 tokenizer 初始化可能读取或下载缓存，请离线部署时预置 `TIKTOKEN_CACHE_DIR`。

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

离线夹具只验证接口、来源和控制流，不验证语义质量或安全性。启用真实模型的分支需额外安装 `llama-index-llms-openai`、`llama-index-embeddings-openai`，重排分支另需 `llama-index-postprocessor-sbert-rerank`；设置 `RUN_REAL_MODELS=1`、`OPENAI_API_KEY`、`LLM_MODEL`、`EMBED_MODEL`（按示例需要）。这些外部模型分支本次未运行。

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

### 架构说明与工程边界 / Architecture and execution boundaries

实际触发上下文窗口裁剪，并区分 get 与 get_all；快照仅覆盖纯文本角色和正文，不是多模态消息无损序列化。ChatMemoryBuffer 是兼容旧接口，新项目优先评估 Memory；服务端通过租户、用户、会话联合键隔离，历史库删除需另做。

Actually triggers context trimming and distinguishes get from get_all. The snapshot preserves text roles and content, not arbitrary multimodal messages. ChatMemoryBuffer is a legacy-compatible API; consider Memory for new projects. Scope storage by tenant, user, and session, and implement history deletion separately.
