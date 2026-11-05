# 11.02 忠实性、相关性与正确性

[返回全书目录 / Contents](../00-contents.md)

忠实性检查答案是否被给定证据支持；正确性检查答案是否符合事实或参考标准；相关性检查是否回应问题。这些维度不同：模型可以忠实复述过期政策却事实不适用，也可以靠训练知识答对但没有使用检索证据。评估应分别报告。

LLM-as-judge 能扩大评估规模，但受提示、模型偏好、顺序和领域知识影响。固定评估协议，盲化方案名称，对代表性样本人工复核，并记录裁判版本。LlamaIndex 的 FaithfulnessEvaluator 等评估器可用于自动评分，但类名存在不代表评分就是客观真理。

对拒答任务分别统计正确拒答、误拒和错误作答。仅以回答正确率衡量，系统可能通过全部拒答规避错误；仅以回答率衡量，又会鼓励编造。结合风险权重与覆盖率选择阈值，特别关注金额、期限、权限和医疗法律等高影响事实。

## 重点与难点

重点：忠实、正确、相关分开。难点：裁判偏差与拒答权衡。

## 面试考点与参考回答

问：答案与参考答案不同就错了吗？答：不一定，可能措辞或合法答案不同；应核对事实主张、条件、单位和证据支持。

## 项目中的坑与处置

坑：同一模型生成参考答案并评自己，偏差被隐藏。处置：独立人工标签、不同评估视角和争议复核。

## 动手实验与验收

制作“忠实但过时”“正确但无证据”“相关但遗漏条件”三个答案。验收：各维度给出不同评分理由。

## 代码实现补充：事实标签与引用支持的独立评估

依赖：Python 3.10+；仅使用 Python 标准库。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
def evaluate(predicted_claims, expected_claims, evidence_facts):
    # Claims are manually normalized facts, not raw generated sentences.
    correct = set(predicted_claims) & set(expected_claims)
    supported = [claim for claim, refs in predicted_claims.items()
                 if refs and all(claim in evidence_facts.get(ref, set()) for ref in refs)]
    return {
        "fact_precision": len(correct) / max(1, len(predicted_claims)),
        "fact_recall": len(correct) / max(1, len(expected_claims)),
        "citation_support": len(supported) / max(1, len(predicted_claims)),
    }

gold = {"hotel_limit=500", "receipts=required"}
evidence = {"p1": {"hotel_limit=500"}, "p2": {"receipts=required"}}
good = evaluate({"hotel_limit=500": ["p1"], "receipts=required": ["p2"]}, gold, evidence)
bad = evaluate({"hotel_limit=800": ["p1"]}, gold, evidence)
assert good == {"fact_precision": 1.0, "fact_recall": 1.0, "citation_support": 1.0}
assert bad["citation_support"] == 0
print({"good": good, "bad": bad})
```

### 实现说明、验收与项目边界

先人工标注原子事实及其证据，再运行确定性评分，适合作为裁判模型的校准集。此处引用支持采用严格规则：列出的每条引用均需支持该事实；不是自然语言蕴含判断，也不是 LlamaIndex FaithfulnessEvaluator 的替代。真实问答需记录裁判提示、模型、人工抽检与拒答题口径。
