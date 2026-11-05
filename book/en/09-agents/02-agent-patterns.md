# 09.02 FunctionAgent, ReAct, and budgets

[返回全书目录 / Contents](../00-contents.md)

FunctionAgent uses models supporting structured tool calls. ReAct alternates decisions and observations. Neither guarantees termination or correct tool choice. Current official examples use FunctionAgent from llama_index.core.agent.workflow; historical runner-style interfaces need version-aware migration.

Agents suit tasks where observations determine the next action. Fixed validation-retrieval-generation-citation flows are usually easier to test as workflows. Bound steps, calls, tokens, cost, and time. Repeated failures should lead to a controlled exit rather than endless retries.

The snippet is service-dependent wiring. It needs llama-index-llms-openai, credentials, and an available tool-capable model. Select the model through configuration instead of treating a name as a permanent default. Production usage additionally needs budgets and authorization.

## Example and execution scope

See dependencies above; external integration execution has not been verified.

```python
# Service-dependent example; requires llama-index-llms-openai.
import asyncio
import os
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI

def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

async def main():
    llm = OpenAI(model=os.environ["LLM_MODEL"], timeout=30.0)
    agent = FunctionAgent(tools=[multiply], llm=llm,
                          system_prompt="Use the calculator for arithmetic.")
    result = await agent.run(user_msg="What is 17 multiplied by 23?")
    print(str(result))

if __name__ == "__main__":
    asyncio.run(main())
```

## Key points and difficulties

Key: dynamic decisions add uncertainty and cost. Difficulty: budget termination and tool-selection evaluation.

## Interview question and answer

Q: Why not use agents for every RAG task? A: fixed pipelines are often cheaper, more predictable, and easier to trace; use agents when dynamic decisions add value.

## Production pitfalls and mitigation

Pitfall: trusting free-form model plans as execution authority. Validate arguments, authorize in tools, and rely on execution results.

## Exercise and acceptance criteria

Run a multi-step calculation and an impossible task. Acceptance: evidence of tool execution and bounded, explicit failure.
