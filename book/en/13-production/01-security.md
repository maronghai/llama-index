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
