# 13.02 Serving, configuration, and rollout strategies

[返回全书目录 / Contents](../00-contents.md)

Load published indexes at startup rather than rebuilding on each request. Startup checks validate configuration and resources; readiness confirms service with the intended version. Avoid expensive model calls in frequent health probes.

Separate ingestion workers from query serving for scaling and permissions. Bind application, index, embedding, prompt, and schema versions into a release. Support canaries and rollback with compatibility checks. Migrate embeddings through new collections rather than unrestricted in-place rewrites.

APIs need request IDs, error types, deadlines, and cancellation semantics. Responses should contain text, citations, index version, and abstention state. Do not expose stacks, credentials, or all candidates. The pseudocode describes boundaries rather than a runnable server.

## Example and execution scope

This is architecture pseudocode, not executable code.

```text
request = authenticate_and_validate(incoming_request)
scope = authorization_scope(request.identity)
release = load_published_release()
evidence = retrieve(request.query, release, scope)
evidence = validate_and_budget(evidence, scope)
answer = generate_with_deadline(request.query, evidence)
return validate_citations_and_serialize(answer, release.version)
```

## Key points and difficulties

Key: release application and index versions together. Difficulty: compatibility, canary comparison, and rollback.

## Interview question and answer

Q: Why separate ingestion from serving? A: resource patterns, permissions, and failure impact differ; rebuilding should not overwhelm live queries.

## Production pitfalls and mitigation

Pitfall: every replica rebuilds a large index on startup. Build separately and serve only published versions.

## Exercise and acceptance criteria

Plan a canary embedding migration. Acceptance: rollback, access-denial checks, and quality/cost metrics during observation.
