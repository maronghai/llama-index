# 10.03 Human review and multi-agent coordination

[返回全书目录 / Contents](../00-contents.md)

High-impact writes, conflicting evidence, and permission exceptions suit human review. Show the proposed action, arguments, evidence, consequences, and expiry. Bind approval to the exact version and argument hash; changed parameters invalidate it.

Persist resumable state while waiting and release unnecessary connections. Approval callbacks need authentication, replay protection, and state validation. Rejection or expiry must prevent alternate paths from executing the same action.

Multiple agents can divide retrieval, analysis, and review, but add handoff costs, loops, and permission complexity. Handoffs should carry goals, structured results, and evidence references rather than unbounded history. Establish a simpler baseline before justifying multiple agents.

## Key points and difficulties

Key: bind approvals to actions and handoffs to evidence. Difficulty: long waits, duplicate callbacks, and authorization propagation.

## Interview question and answer

Q: Do two agents checking each other guarantee correctness? A: no; they can share biases and evidence errors. Use independent checks and external constraints.

## Production pitfalls and mitigation

Pitfall: regenerating arguments after approval. Execute the immutable approved action record.

## Exercise and acceptance criteria

Test approval, rejection, expiry, and duplicate callbacks. Acceptance: at most one execution and renewed review after parameter changes.
