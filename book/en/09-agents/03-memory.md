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
