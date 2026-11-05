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

## 代码实现补充 / Implementation supplement: 审批绑定内容与单次执行 / Content-bound review and one-time execution

依赖 / Dependencies: Python 3.10+; 仅标准库 / standard library only.

将完整代码保存为独立 `.py` 文件，在独立进程执行 `python filename.py`。无需密钥，无付费调用；验收为断言通过并输出结果。

Save the full block as a standalone `.py` file and run it in a separate process. No API key or paid call is needed; assertions must pass and results are printed.

```python
import hashlib
import json
from dataclasses import dataclass

@dataclass(frozen=True)
class Proposal:
    request_id: str
    tenant: str
    action: str
    amount: int

def fingerprint(proposal):
    return hashlib.sha256(json.dumps(vars(proposal), sort_keys=True).encode()).hexdigest()

executed = set()
def execute(proposal, approval, reviewer_tenant):
    if reviewer_tenant != proposal.tenant:
        raise PermissionError("wrong reviewer tenant")
    if approval != fingerprint(proposal):
        raise PermissionError("proposal changed or not approved")
    if proposal.request_id in executed:
        return "already executed"
    # In production, atomically claim the ID and use a downstream idempotency key.
    executed.add(proposal.request_id)
    return "executed"

p = Proposal("r-1", "a", "refund", 100)
approval = fingerprint(p)
assert execute(p, approval, "a") == "executed"
assert execute(p, approval, "a") == "already executed"
try:
    execute(Proposal("r-2", "a", "refund", 999), approval, "a")
except PermissionError:
    print("changed proposal denied")
else:
    raise AssertionError("approval not bound to content")
```

### 实现说明、验收与项目边界 / Implementation, acceptance and production boundaries

哈希不是审批凭证；此处假定 approval 来自已认证的人工审批服务。实际必须持久化审批人、权限、时间、过期时间与内容哈希，模型不能自行创建批准事件。内存 set 不提供跨进程或崩溃恢复的 exactly-once 保证，需数据库唯一键和下游幂等协议。

A hash is not an approval credential. Here approval is assumed to come from an authenticated human review service. Persist reviewer identity, authorization, time, expiration and content hash; models cannot approve themselves. The in-memory set does not provide cross-process or crash-safe exactly-once execution.
