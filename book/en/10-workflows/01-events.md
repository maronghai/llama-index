# 10.01 Event-driven workflows and state

[返回全书目录 / Contents](../00-contents.md)

Workflows make steps and events explicit. Events carry data needed by subsequent steps; state retains shared information. These boundaries support timeouts, retries, and observation. Event typing still needs value validation, identity checks, and transition guards.

Modern LlamaIndex workflows can use the standalone llama-index-workflows package and workflows namespace; older examples may import from llama_index.core.workflow. Do not mix generations in one example. The snippet demonstrates a standalone StartEvent, custom event, and StopEvent flow with a tested dependency set required in your environment.

Use explicit business states such as RECEIVED, AUTHORIZED, RETRIEVED, VALIDATED, and COMPLETED, with failure and cancellation as terminal states. Record job identity, versions, and results at transitions. In-memory async execution alone does not provide crash recovery or durable workflows.

## Example and execution scope

See dependencies above; external integration execution has not been verified.

```python
# Requires llama-index-workflows; uses the standalone namespace.
import asyncio
from workflows import Workflow, step
from workflows.events import Event, StartEvent, StopEvent

class QueryReady(Event):
    query: str

class NormalizeFlow(Workflow):
    @step
    async def normalize(self, ev: StartEvent) -> QueryReady:
        query = ev.query.strip()
        if not query:
            raise ValueError("Empty query")
        return QueryReady(query=query)

    @step
    async def finish(self, ev: QueryReady) -> StopEvent:
        return StopEvent(result={"query": ev.query})

async def main():
    result = await NormalizeFlow(timeout=10).run(query="  receipts  ")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## Key points and difficulties

Key: distinguish events, state, and durability. Difficulty: duplicates, invalid transitions, and recovery.

## Interview question and answer

Q: Workflow versus agent? A: workflows explicitly control transitions, agents select actions through model decisions; an agent can run inside a bounded workflow.

## Production pitfalls and mitigation

Pitfall: assuming automatic resumption after restart. Use a durable runtime or explicitly persist checkpoints, idempotency keys, and event status.

## Exercise and acceptance criteria

Run the minimal workflow and add an invalid-input branch. Acceptance: invalid input never reaches retrieval and event fields are validated.
