# 10.03 人工介入与多 Agent 协作

[返回全书目录 / Contents](../00-contents.md)

高影响写入、证据冲突和权限例外适合人工介入。人工审核不能只显示“是否同意”，应提供待执行动作、参数、来源、风险和有效期。审核结果绑定具体版本与参数哈希，参数变化后旧批准失效。

等待人工时保存可恢复状态，释放不必要连接，不把 Web 请求一直挂到无限期。审批回调需要鉴权、防重放和状态校验。用户拒绝或超时后进入明确终态，不能偷偷选择另一条工具路径执行同样动作。

多 Agent 可以按检索、分析和审核分工，但增加交接成本、循环风险与权限传播复杂度。每次交接携带任务目标、结构化结果和证据引用，而不是无限增长的全部历史。先用单 Agent 或工作流建立基线，再证明多 Agent 的额外收益。

## 重点与难点

重点：批准绑定动作，交接绑定证据。难点：长时间等待、重复回调和权限传播。

## 面试考点与参考回答

问：两个 Agent 互相检查能保证正确吗？答：不能，可能共享模型偏差或同一错误证据；需独立校验、真实标签和外部约束。

## 项目中的坑与处置

坑：审批后重新生成参数再执行。处置：执行已批准的不可变动作记录，不再让模型改写。

## 动手实验与验收

模拟批准、拒绝、超时和重复回调。验收：同一动作最多执行一次，参数变化必须重新审核。

## 代码实现补充：审批绑定内容与单次执行

依赖：Python 3.10+；仅使用 Python 标准库。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

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

### 实现说明、验收与项目边界

哈希不是审批凭证；此处假定 approval 来自已认证的人工审批服务。实际必须持久化审批人、权限、时间、过期时间与内容哈希，模型不能自行创建批准事件。内存 set 不提供跨进程或崩溃恢复的 exactly-once 保证，需数据库唯一键和下游幂等协议。
