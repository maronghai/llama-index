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

## Implementation supplement: Content-bound review and one-time execution

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
import hashlib
import json
from dataclasses import dataclass

@dataclass(frozen=True)
class Proposal:
    request_id: str
    tenant: str
    action: str
    amount: int

def fingerprint(proposal):
    return hashlib.sha256(json.dumps(vars(proposal), sort_keys=True).encode()).hexdigest()

executed = set()
def execute(proposal, approval, reviewer_tenant):
    if reviewer_tenant != proposal.tenant:
        raise PermissionError("wrong reviewer tenant")
    if approval != fingerprint(proposal):
        raise PermissionError("proposal changed or not approved")
    if proposal.request_id in executed:
        return "already executed"
    # In production, atomically claim the ID and use a downstream idempotency key.
    executed.add(proposal.request_id)
    return "executed"

p = Proposal("r-1", "a", "refund", 100)
approval = fingerprint(p)
assert execute(p, approval, "a") == "executed"
assert execute(p, approval, "a") == "already executed"
try:
    execute(Proposal("r-2", "a", "refund", 999), approval, "a")
except PermissionError:
    print("changed proposal denied")
else:
    raise AssertionError("approval not bound to content")
```

### Implementation, acceptance and production boundaries

A hash is not an approval credential. Here approval is assumed to come from an authenticated human review service. Persist reviewer identity, authorization, time, expiration and content hash; models cannot approve themselves. The in-memory set does not provide cross-process or crash-safe exactly-once execution.
