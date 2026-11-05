# 07.03 子问题分解与多文档比较 / Question decomposition and multi-document comparison

[返回全书目录 / Contents](../00-contents.md)

“比较两家公司三年的收入变化并解释差异”包含多个实体、时间点和计算步骤。子问题分解把任务拆为可检索的事实，再汇总。LlamaIndex 的子问题查询模式适合这种场景，但规划本身也会出错，必须检查子问题是否覆盖原问题且没有新增假设。

A multi-company revenue comparison contains entities, years, and calculations. Decomposition retrieves individual facts before synthesis. Sub-question patterns support this workflow, but plans can omit requirements or add assumptions and therefore need validation.

为每个子结果保留单位、期间、来源和缺失状态。财年与自然年、合并口径与单体口径不能直接比较。先用结构化记录对齐口径，再用确定性函数计算增长率；分母为零或数据缺失时明确输出不可计算，而不是让模型补值。

Retain units, periods, provenance, and missingness for each result. Fiscal and calendar years or consolidated and standalone figures are not directly comparable. Align structured facts before deterministic growth calculations; zero denominators and missing values require explicit unavailable results.

并行运行独立子问题可减少关键路径时间，但会放大 API 并发与预算。设置总任务期限、单步期限、最大子问题数和部分失败语义。汇总回答应区分完整结论与仅基于部分数据的观察。

Parallel independent questions can reduce critical-path latency while increasing concurrency and cost. Bound task duration, step duration, question count, and partial-failure behavior. Clearly distinguish complete conclusions from observations based on incomplete evidence.

## 重点与难点 / Key points and difficulties

重点：规划、事实提取、计算、汇总分层。难点：跨来源单位和期间对齐。

Key: separate planning, extraction, computation, and synthesis. Difficulty: aligning units and reporting periods.

## 面试考点与参考回答 / Interview question and answer

问：如何避免分解后答非所问？答：把原需求转成检查项，验证子问题覆盖率，并在最终汇总时逐项核对。

Q: How do you prevent decomposition drift? A: convert requirements into a checklist, validate sub-question coverage, and verify final coverage.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：子问题失败被当成零值参与平均。处置：用显式缺失状态，不允许缺失值进入计算。

Pitfall: failed subqueries become zeros in calculations. Preserve missingness and reject incomplete computation.

## 动手实验与验收 / Exercise and acceptance criteria

比较两份不同期间的报告。验收：先拒绝错误口径比较，补齐可比数据后再计算并逐项引用。

Compare reports with different periods. Acceptance: reject incompatible comparisons, obtain aligned facts, then calculate with citations.

## 代码实现补充 / Implementation supplement: 有预算的子问题计划与合并 / Budgeted sub-question planning and aggregation

依赖 / Dependencies: Python 3.10+; 仅标准库 / standard library only.

将完整代码保存为独立 `.py` 文件，在独立进程执行 `python filename.py`。无需密钥，无付费调用；验收为断言通过并输出结果。

Save the full block as a standalone `.py` file and run it in a separate process. No API key or paid call is needed; assertions must pass and results are printed.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Task:
    source: str
    question: str

facts = {"a": {"hotel": 500}, "b": {"hotel": 650}}

def execute_plan(tasks, authorized, max_calls=3):
    if len(tasks) > max_calls:
        raise ValueError("plan exceeds call budget")
    results = []
    for task in tasks:
        if task.source not in authorized:
            raise PermissionError(task.source)
        value = facts.get(task.source, {}).get(task.question)
        results.append({"source": task.source, "value": value, "ok": value is not None})
    return results

plan = [Task("a", "hotel"), Task("b", "hotel")]
rows = execute_plan(plan, {"a", "b"})
assert all(r["ok"] for r in rows)
difference = rows[1]["value"] - rows[0]["value"]
assert difference == 150
print({"evidence": rows, "difference": difference})
```

### 实现说明、验收与项目边界 / Implementation, acceptance and production boundaries

此处手写计划隔离“分解是否合理”和“执行是否可靠”。接入 SubQuestionQueryEngine 时让模型产生同类结构，再执行源授权、调用数和时间预算校验。缺失值必须标记失败，不能补成 0；金额、单位和生效日期一致后才可比较。

A manual plan separates decomposition quality from execution reliability. With SubQuestionQueryEngine, validate generated plans against source authorization, call and time budgets. Missing values are failures, not zero; align units, currencies and effective dates before comparison.
