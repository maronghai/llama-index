# 13.01 Prompt injection, authorization, and output security

[返回全书目录 / Contents](../00-contents.md)

Retrieved documents are untrusted data and may contain malicious instructions. Separating instructions from evidence and labeling sources helps, but cannot guarantee immunity. Enforce boundaries through tool authorization, data scope, credential isolation, and execution policy.

Maintain authorization through retrieval, expansion, reranking, caches, and citation access. Final-output filtering is too late if private data already reached models or logs. Verify whether backend filtering happens before or after candidate selection and test both access and recall behavior.

Outputs may contain HTML, scripts, or links. Escape untrusted display content and do not automatically execute generated commands. Validate sensitive actions with least-privilege identities. Include forged system messages, unauthorized citations, and injected tool results in regression tests.

## Key points and difficulties

Key: models are not authorization engines. Difficulty: data flow and derived-content leaks across the pipeline.

## Interview question and answer

Q: Is a no-leak prompt enough? A: no. Use server-side authorization, tool restrictions, and data isolation outside model control.

## Production pitfalls and mitigation

Pitfall: parent expansion reintroduces secrets after filtered retrieval. Reauthorize expansions and align chunks with access boundaries.

## Exercise and acceptance criteria

Inject a document requesting unauthorized tools and secrets. Acceptance: execution controls block violations even if the model proposes them.

## Implementation supplement: Authorization before and after retrieval

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Principal:
    tenant: str
    groups: frozenset[str]

records = [
    {"id": "1", "tenant": "a", "groups": {"staff"}, "text": "Hotel limit 500"},
    {"id": "2", "tenant": "a", "groups": {"finance"}, "text": "Private payroll"},
    {"id": "3", "tenant": "b", "groups": {"staff"}, "text": "Tenant B secret"},
]
def allowed(user, row):
    return row["tenant"] == user.tenant and bool(row["groups"] & user.groups)

def retrieve(user, query):
    # A real vector backend must enforce this predicate before top-k selection.
    candidates = [r for r in records if allowed(user, r)]
    ranked = sorted(candidates, key=lambda r: len(set(query.lower().split()) & set(r["text"].lower().split())), reverse=True)
    return [{"id": r["id"], "text": r["text"]} for r in ranked[:3] if allowed(user, r)]

user = Principal("a", frozenset({"staff"}))
evidence = retrieve(user, "hotel limit")
assert [r["id"] for r in evidence] == ["1"]
assert retrieve(Principal("c", frozenset({"staff"})), "hotel") == []
print(evidence)
```

### Implementation, acceptance and production boundaries

Principal must come from an authenticated session. Filter before ranking and recheck before returning; apply the same rules to expanded parents and caches. This code does not detect prompt injection. Also constrain tools, treat retrieved text as data, validate outputs, and protect writes with review and idempotency.
