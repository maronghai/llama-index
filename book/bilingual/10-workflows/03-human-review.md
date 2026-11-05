# 10.03 人工介入与多 Agent 协作 / Human review and multi-agent coordination

[返回全书目录 / Contents](../00-contents.md)

高影响写入、证据冲突和权限例外适合人工介入。人工审核不能只显示“是否同意”，应提供待执行动作、参数、来源、风险和有效期。审核结果绑定具体版本与参数哈希，参数变化后旧批准失效。

High-impact writes, conflicting evidence, and permission exceptions suit human review. Show the proposed action, arguments, evidence, consequences, and expiry. Bind approval to the exact version and argument hash; changed parameters invalidate it.

等待人工时保存可恢复状态，释放不必要连接，不把 Web 请求一直挂到无限期。审批回调需要鉴权、防重放和状态校验。用户拒绝或超时后进入明确终态，不能偷偷选择另一条工具路径执行同样动作。

Persist resumable state while waiting and release unnecessary connections. Approval callbacks need authentication, replay protection, and state validation. Rejection or expiry must prevent alternate paths from executing the same action.

多 Agent 可以按检索、分析和审核分工，但增加交接成本、循环风险与权限传播复杂度。每次交接携带任务目标、结构化结果和证据引用，而不是无限增长的全部历史。先用单 Agent 或工作流建立基线，再证明多 Agent 的额外收益。

Multiple agents can divide retrieval, analysis, and review, but add handoff costs, loops, and permission complexity. Handoffs should carry goals, structured results, and evidence references rather than unbounded history. Establish a simpler baseline before justifying multiple agents.

## 重点与难点 / Key points and difficulties

重点：批准绑定动作，交接绑定证据。难点：长时间等待、重复回调和权限传播。

Key: bind approvals to actions and handoffs to evidence. Difficulty: long waits, duplicate callbacks, and authorization propagation.

## 面试考点与参考回答 / Interview question and answer

问：两个 Agent 互相检查能保证正确吗？答：不能，可能共享模型偏差或同一错误证据；需独立校验、真实标签和外部约束。

Q: Do two agents checking each other guarantee correctness? A: no; they can share biases and evidence errors. Use independent checks and external constraints.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：审批后重新生成参数再执行。处置：执行已批准的不可变动作记录，不再让模型改写。

Pitfall: regenerating arguments after approval. Execute the immutable approved action record.

## 动手实验与验收 / Exercise and acceptance criteria

模拟批准、拒绝、超时和重复回调。验收：同一动作最多执行一次，参数变化必须重新审核。

Test approval, rejection, expiry, and duplicate callbacks. Acceptance: at most one execution and renewed review after parameter changes.
