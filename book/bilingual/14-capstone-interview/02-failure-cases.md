# 14.02 八类典型故障与修复思路 / Eight recurring failures and their remedies

[返回全书目录 / Contents](../00-contents.md)

故障一：检索总返回相似但无用的内容。先查语料覆盖、模型兼容与查询约束，再查切块和候选召回。故障二：答案遗漏例外。检查解析与上下文截断，尝试窗口恢复并加入条件题评测。不要把两种问题都归因于模型不够大。

Failure one: similar but useless retrieval. Inspect coverage, embedding compatibility, and query constraints before chunking and candidate recall. Failure two: missing exceptions. Check parsing and truncation, try window recovery, and add conditional questions. These failures need distinct diagnoses.

故障三：更新后重复回答。查来源 ID 稳定性、旧节点删除和混合通道版本。故障四：权限撤销后仍可见。查父块、摘要、会话和缓存的传播。修复需要沿派生依赖清理，不能只删除一条向量。

Failure three: duplicated answers after updates. Check source identity, old-node removal, and channel versions. Failure four: content remains after revocation. Check parent nodes, summaries, history, and caches. Cleanup must follow derived dependencies, not only delete one vector.

故障五：流量升高后超时。观察排队、连接池、并发限额与模型配额，实施背压。故障六：成本突增。检查子问题爆炸、Agent 循环、缓存失效和重复摄取。先找调用数变化，再看单价。

Failure five: timeouts under load. Inspect queues, pools, concurrency, and provider quotas; apply backpressure. Failure six: cost spikes. Check subquestion fan-out, agent loops, cache invalidation, and duplicate ingestion. Inspect call counts before prices.

故障七：升级后不能导入或调用参数失效。区分核心、集成和独立工作流包的版本，回到受测依赖集。故障八：指标很好但用户不满意。检查测试集泄漏、合成问题偏差、无答案覆盖和真实业务条件，补充脱敏真实问题并重做分组评估。

Failure seven: imports or arguments break after upgrades. Separate core, integration, and standalone workflow versions and restore a tested set. Failure eight: good metrics but unhappy users. Inspect leakage, synthetic bias, missing-answer coverage, and business constraints; add anonymized real questions and slice-level evaluation.

## 重点与难点 / Key points and difficulties

重点：从证据和最近变更出发。难点：同一表面症状可能有多个根因，修复要有回归验证。

Key: start with evidence and recent changes. Difficulty: similar symptoms can have distinct causes; every fix needs regression coverage.

## 面试考点与参考回答 / Interview question and answer

问：如何展示排障能力？答：说清症状、假设、观测、排除过程、根因、修复和回归，不只报最终使用了哪个库。

Q: How do you demonstrate debugging ability? A: explain symptoms, hypotheses, observations, elimination, cause, fix, and regression checks.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：修复线上问题时同时改模型、切块和数据库参数。处置：先止损，再做可归因的独立实验。

Pitfall: changing models, chunks, and store settings at once. Contain first, then run attributable experiments.

## 动手实验与验收 / Exercise and acceptance criteria

任选两类故障，写一页排障记录并给出反证条件。验收：每个假设都有可观测证据，失败假设被明确排除。

Choose two failures and write diagnostic records with falsification conditions. Acceptance: observable evidence for each hypothesis and explicit elimination.

## 代码实现补充 / Implementation supplement: 八类故障的可执行诊断器 / An executable diagnostic triage for eight failure classes

依赖 / Dependencies: Python 3.10+; 仅标准库 / standard library only.

将完整代码保存为独立 `.py` 文件，在独立进程执行 `python filename.py`。无需密钥，无付费调用；验收为断言通过并输出结果。

Save the full block as a standalone `.py` file and run it in a separate process. No API key or paid call is needed; assertions must pass and results are printed.

```python
def diagnose(s):
    findings = []
    rules = [
        (s["recall"] < 0.7, "retrieval", "inspect corpus, chunks and embeddings"),
        (s["missing_conditions"] > 0, "omitted exceptions", "inspect parsing and context truncation"),
        (s["duplicate_sources"] > 0, "duplicate ingestion", "inspect stable IDs and deletion"),
        (s["unauthorized_hits"] > 0, "authorization leak", "block affected reads and audit derived artifacts"),
        (s["p95_ms"] > 2000, "latency", "inspect queueing, concurrency and provider limits"),
        (s["calls_per_query"] > 8, "cost amplification", "inspect decomposition and agent budgets"),
        (not s["import_ok"], "upgrade regression", "restore tested package set"),
        (s["online_success"] < s["offline_success"] - 0.15, "distribution shift", "evaluate real anonymized query slices"),
    ]
    for condition, symptom, next_step in rules:
        if condition:
            findings.append({"symptom": symptom, "next_step": next_step})
    return findings

sample = dict(recall=0.5, missing_conditions=1, duplicate_sources=2, unauthorized_hits=1,
              p95_ms=3000, calls_per_query=12, import_ok=False, online_success=0.6, offline_success=0.95)
assert len(diagnose(sample)) == 8
print(diagnose(sample))
```

### 实现说明、验收与项目边界 / Implementation, acceptance and production boundaries

这些阈值只是教学配置，输出是排查方向而不是根因结论。线上权限泄漏需先止损，再保留审计证据。接入 trace 和评测数据后按优先级告警，给每个假设补充反证与回归；不要因为命中规则便自动同时修改模型、切块和数据库。

Thresholds are instructional; findings suggest investigations, not proven causes. Contain authorization leaks first and retain audit evidence. Connect traces and evaluations, prioritize alerts, and add falsification and regression checks. Do not automatically change models, chunks and storage together.
