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

## Implementation supplement: Request correlation, stage timing and exceptions

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
import json
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar

request_id = ContextVar("request_id", default="unset")
spans = []
@contextmanager
def span(name):
    started = time.perf_counter()
    record = {"trace_id": request_id.get(), "name": name, "status": "ok"}
    try:
        yield
    except Exception as exc:
        record.update(status="error", error_type=type(exc).__name__)
        raise
    finally:
        record["duration_ms"] = (time.perf_counter() - started) * 1000
        spans.append(record)

token = request_id.set(uuid.uuid4().hex)
try:
    with span("query"):
        with span("retrieve"):
            evidence = ["policy-1"]
        with span("synthesize"):
            answer = "cited answer"
finally:
    request_id.reset(token)
assert len({s["trace_id"] for s in spans}) == 1
assert {s["name"] for s in spans} == {"query", "retrieve", "synthesize"}
print(json.dumps(spans, indent=2))
```

### Implementation, acceptance and production boundaries

This illustrates a tracing contract without a collector and sends nothing to Phoenix. Replace span with tracer.start_as_current_span, then configure the OpenInference LlamaIndex instrumentor and an OTLP exporter. Production also needs parent IDs, sampling, async propagation and redaction; avoid raw documents, credentials and full prompts.
