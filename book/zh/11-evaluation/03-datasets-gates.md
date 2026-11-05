# 11.03 合成数据、数据泄漏与回归门禁

[返回全书目录 / Contents](../00-contents.md)

合成问题有助于扩大覆盖，但常贴近原文措辞，低估真实用户的省略、歧义和错误前提。将合成数据、真实脱敏问题、人工对抗问题分开标记。测试集应包含无答案、版本冲突、多语言、权限负例、表格计算和长文边界。

按来源、时间或业务实体切分开发集与测试集，避免同一政策的近重复问题跨集合泄漏。参数在开发集选择，最终测试集只用于确认。持续从真实失败中建立回归集，但不要只收集已知错误而忘记正常样本和流量分布。

发布门禁应包括质量、权限、性能、成本和恢复，而不是只有一个总分。为高风险类别设置不能退化的底线。比较两版时采用同一问题的配对结果，检查改善与退化样例；样本很小时不要把微小百分比变化解释为稳定收益。

## 重点与难点

重点：测试集必须包含失败与负例。难点：泄漏、分布变化和小样本不确定性。

## 面试考点与参考回答

问：如何证明一个优化有效？答：固定基线与数据，记录单因素改动，进行配对评测，报告分组结果、成本和退化案例。

## 项目中的坑与处置

坑：反复看测试集调参数，最后成绩虚高。处置：保留封存集，并把所有调参过程与发布版本绑定。

## 动手实验与验收

设计一份 50 题评测计划和门禁表，数字标为拟定阈值而非实测成绩。验收：每项门禁有失败处置和负责人。

## 代码实现补充：按来源分组切分与回归门禁

依赖：Python 3.10+；仅使用 Python 标准库。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
import hashlib

rows = [{"source_id": "doc-" + str(i), "question": "q" + str(i)} for i in range(30)]
def bucket(source_id):
    return int(hashlib.sha256(source_id.encode()).hexdigest()[:8], 16) % 10
train = [r for r in rows if bucket(r["source_id"]) < 7]
test = [r for r in rows if bucket(r["source_id"]) >= 7]
assert train and test
assert not ({r["source_id"] for r in train} & {r["source_id"] for r in test})

def release_gate(metrics):
    return (metrics["recall_at_5"] >= 0.9 and metrics["unauthorized_hits"] == 0
            and metrics["p95_ms"] <= 1800)

assert release_gate({"recall_at_5": 0.93, "unauthorized_hits": 0, "p95_ms": 1500})
assert not release_gate({"recall_at_5": 0.99, "unauthorized_hits": 1, "p95_ms": 100})
print({"train": len(train), "test": len(test), "gate": "passed example assertions"})
```

### 实现说明、验收与项目边界

同源问题固定落入同一分区，避免对同一文档只换问法产生泄漏。近重复文档仍可能跨分区，需先做聚类；还应按时间留出并覆盖无答案、冲突和权限题。门禁指标是合成输入，不代表真实系统成绩，小样本切片需同时报告样本量与不确定性。
