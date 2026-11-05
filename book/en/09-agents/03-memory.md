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
