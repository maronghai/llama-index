# 10.01 事件驱动工作流与状态

[返回全书目录 / Contents](../00-contents.md)

工作流把步骤与事件显式化。事件包含下一步需要的数据，状态保存跨步骤共享的信息。与长串嵌套函数相比，事件边界更容易设置超时、重试和观测。事件类型不是运行时安全的全部：仍需验证字段值、身份和状态转移条件。

现代 LlamaIndex 生态中的工作流可使用独立 llama-index-workflows 包及 workflows 命名空间；历史示例也可能从 llama_index.core.workflow 导入。不要在同一示例中混用版本来源。下例展示独立包的最小 StartEvent—自定义事件—StopEvent 流程，具体环境需锁定相容版本。

业务工作流建议显式定义状态机，例如 RECEIVED、AUTHORIZED、RETRIEVED、VALIDATED、COMPLETED。失败与取消也是合法终态。每次状态转移记录作业 ID、输入版本和结果摘要。仅仅在内存里运行异步步骤不等于持久化工作流，进程崩溃后的恢复能力要另外设计。

## 示例与运行边界

依赖说明见正文；本例未完成外部集成运行验证。

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

## 重点与难点

重点：事件、状态和持久化是不同概念。难点：重复事件、非法转移与崩溃恢复。

## 面试考点与参考回答

问：Workflow 与 Agent 有什么区别？答：Workflow 显式控制步骤和转移，Agent 根据模型判断选工具；可以把 Agent 放进受控 Workflow。

## 项目中的坑与处置

坑：进程重启后认为工作流会自动续跑。处置：选用明确支持持久化的运行方式，或自行保存检查点、幂等键和事件处理状态。

## 动手实验与验收

运行最小工作流，再添加一条非法输入分支。验收：非法输入不进入检索，事件字段可验证。
