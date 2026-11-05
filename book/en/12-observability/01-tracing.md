# 12.01 Traces, OpenTelemetry, and Phoenix

[返回全书目录 / Contents](../00-contents.md)

Trace authentication, rewriting, retrieval, reranking, generation, and tools within one request. Spans describe stages. Versions, candidate counts, tokens, latency, and error types make slow responses diagnosable. Verify OpenTelemetry and OpenInference integration details for the deployed versions.

Tools such as Phoenix help inspect traces and experiments, but do not automatically export full prompts, evidence, and messages. Define redaction, sampling, access, and retention first. Production logs can retain IDs and hashes, with authorized source lookup for debugging.

Propagate trace context across async tasks and agent handoffs. Otherwise related work appears unrelated. Telemetry exporters need bounded buffers, timeouts, and degradation so logging outages do not block core queries.

## Key points and difficulties

Key: trace versions and evidence lineage. Difficulty: balance diagnostic detail, privacy, and overhead.

## Interview question and answer

Q: Logs versus traces? A: logs capture discrete events; traces connect a request across components. Join them through trace IDs.

## Production pitfalls and mitigation

Pitfall: indefinite storage of private documents in debug logs. Default to minimal redacted fields and controlled temporary sampling.

## Exercise and acceptance criteria

Trace a request with a simulated model timeout. Acceptance: identify the failed stage and version without sensitive content.
