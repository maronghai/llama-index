# 09.01 FunctionTool 与 QueryEngineTool / FunctionTool and QueryEngineTool

[返回全书目录 / Contents](../00-contents.md)

工具把可执行能力暴露给模型。FunctionTool 适合包装类型明确的函数，QueryEngineTool 可包装已有查询引擎。工具名称、参数类型、描述和返回结构共同构成调用契约。不要把“执行任意 Python”作为普通业务工具，否则输入空间与权限边界难以控制。

Tools expose capabilities to a model. FunctionTool wraps typed functions, while QueryEngineTool wraps query engines. Names, parameter types, descriptions, and result schemas form the contract. Arbitrary Python execution is a poor default business tool because its input and permission space is unbounded.

把读操作与写操作分开。写工具接收幂等键、验证参数、检查权限并返回明确状态；模型不能通过猜测确认成功。工具返回应区分 success、retryable_error 和 permanent_error，避免模型把错误字符串当业务事实。

Separate read and write tools. Writes need idempotency keys, validation, authorization, and explicit status. A model cannot infer success from a guess. Distinguish successful results from retryable and permanent errors so error text is not mistaken for evidence.

工具描述应说明何时用、何时不用、输入单位和限制。参数默认值不能扩大权限。将检索引擎包装成工具时仍要绑定当前用户范围，不能把一个管理员引擎无条件交给所有会话。

Descriptions should specify use cases, exclusions, units, and limits. Defaults must not broaden access. A query-engine tool must retain the caller’s access scope rather than exposing an administrator engine to every session.

## 示例与运行边界 / Example and execution scope

本节示例按正文所列前置条件运行；部分是组件片段，不构成完整应用。

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

## 重点与难点 / Key points and difficulties

重点：工具是受约束的业务接口。难点：调用前后的权限、幂等与状态解释。

Key: tools are constrained business interfaces. Difficulty: authorization, idempotency, and result interpretation.

## 面试考点与参考回答 / Interview question and answer

问：工具调用等于执行成功吗？答：不等于；要看经过验证的执行结果和持久化状态，尤其是支付、工单和写入。

Q: Does a tool call imply success? A: no; use verified execution and persisted status, especially for writes.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：失败后 Agent 换一种措辞重复创建工单。处置：业务幂等键与写入状态查询，不依赖模型记忆。

Pitfall: an agent rephrases and duplicates a failed ticket creation. Use business idempotency and status lookup, not model memory.

## 动手实验与验收 / Exercise and acceptance criteria

把一个纯计算函数包装为工具，测试无效类型和越界值。验收：错误可结构化处理，不会被生成成成功结论。

Wrap a pure function and test invalid types and ranges. Acceptance: structured errors cannot be reported as successful outcomes.
