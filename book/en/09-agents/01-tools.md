# 09.01 FunctionTool and QueryEngineTool

[返回全书目录 / Contents](../00-contents.md)

Tools expose capabilities to a model. FunctionTool wraps typed functions, while QueryEngineTool wraps query engines. Names, parameter types, descriptions, and result schemas form the contract. Arbitrary Python execution is a poor default business tool because its input and permission space is unbounded.

Separate read and write tools. Writes need idempotency keys, validation, authorization, and explicit status. A model cannot infer success from a guess. Distinguish successful results from retryable and permanent errors so error text is not mistaken for evidence.

Descriptions should specify use cases, exclusions, units, and limits. Defaults must not broaden access. A query-engine tool must retain the caller’s access scope rather than exposing an administrator engine to every session.

## Example and execution scope

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

```python
from llama_index.core.tools import FunctionTool

def growth_percent(current: float, previous: float) -> float:
    """Compute percentage growth; previous must be positive."""
    if previous <= 0:
        raise ValueError("previous must be positive")
    return (current - previous) / previous * 100.0

tool = FunctionTool.from_defaults(fn=growth_percent)
print(tool.call(current=120.0, previous=100.0))
```

## Key points and difficulties

Key: tools are constrained business interfaces. Difficulty: authorization, idempotency, and result interpretation.

## Interview question and answer

Q: Does a tool call imply success? A: no; use verified execution and persisted status, especially for writes.

## Production pitfalls and mitigation

Pitfall: an agent rephrases and duplicates a failed ticket creation. Use business idempotency and status lookup, not model memory.

## Exercise and acceptance criteria

Wrap a pure function and test invalid types and ranges. Acceptance: structured errors cannot be reported as successful outcomes.
