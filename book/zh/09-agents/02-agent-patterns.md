# 09.02 FunctionAgent、ReAct 与预算

[返回全书目录 / Contents](../00-contents.md)

FunctionAgent 利用支持工具调用的模型输出结构化调用；ReAct 模式交替执行决策与观察。两者都不保证任务一定结束，也不保证工具选择正确。当前官方示例采用 llama_index.core.agent.workflow 中的 FunctionAgent；旧 AgentRunner 风格代码应按版本迁移，不能混搭接口。

Agent 适合步骤不完全固定、需要根据观察选择行动的任务。确定流程如“校验—检索—生成—引用”通常用工作流更易测试。设定最大步骤、工具调用数、总 token、总费用和期限；工具重复失败后要转为受控退出，而不是循环尝试。

下例只是服务依赖型接线示例，需要 llama-index-llms-openai、有效凭据，以及支持工具调用的可用模型。模型名由环境变量选择，不把某个名字写成永久默认。生产还要接入本节的预算和授权控制。

## 示例与运行边界

依赖说明见正文；本例未完成外部集成运行验证。

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

## 重点与难点

重点：Agent 为动态决策付出不确定性成本。难点：预算终止与工具选择评估。

## 面试考点与参考回答

问：为什么不用 Agent 做所有 RAG？答：固定链路通常更便宜、更稳定、更容易追踪；仅在动态决策确有收益时增加 Agent。

## 项目中的坑与处置

坑：把模型内部自由文本当成可信执行计划。处置：验证结构化参数，工具端重新授权，实际执行结果作为最终事实。

## 动手实验与验收

用计算工具完成三步任务，并设计无法完成的任务。验收：正确任务有工具证据，失败任务在预算内明确结束。
