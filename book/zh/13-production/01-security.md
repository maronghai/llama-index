# 13.01 提示注入、数据权限与输出安全

[返回全书目录 / Contents](../00-contents.md)

检索内容是不可信数据，文档可能包含“忽略规则”“发送密钥”等恶意文本。把系统指令与证据分区、标明来源能降低风险，但不能从根本上保证模型不会被影响。真正的安全边界在工具授权、数据范围、凭据隔离与执行策略中。

权限在候选召回、扩展、重排、缓存与引用访问全程维持。若只在最终输出过滤，受限内容可能已经进入模型或日志。过滤下推通常有助于安全与效率，但后端能力不同，必须验证实际过滤是在候选前还是候选后执行，并测试召回影响。

输出也可能含 HTML、脚本片段或外部链接。展示层转义不可信文本，工具执行层不自动运行模型生成命令。敏感动作需要可信参数校验和最小权限身份。把攻击样本纳入回归，包括伪造系统消息、越权来源引用和工具结果注入。

## 重点与难点

重点：模型不是权限执行器。难点：跨链路的数据流与派生内容泄漏。

## 面试考点与参考回答

问：提示中写“不要泄密”够吗？答：不够，必须用不可被模型覆盖的服务端授权、工具限制和数据隔离。

## 项目中的坑与处置

坑：检索过滤正确但父块扩展带入秘密。处置：扩展阶段重新授权，权限边界与分块结构对齐。

## 动手实验与验收

构造恶意文档请求调用写工具和泄露密钥。验收：模型即使产生调用意图，工具与数据边界仍阻止越权。

## 代码实现补充：检索前后双重授权与最小上下文

依赖：Python 3.10+；仅使用 Python 标准库。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Principal:
    tenant: str
    groups: frozenset[str]

records = [
    {"id": "1", "tenant": "a", "groups": {"staff"}, "text": "Hotel limit 500"},
    {"id": "2", "tenant": "a", "groups": {"finance"}, "text": "Private payroll"},
    {"id": "3", "tenant": "b", "groups": {"staff"}, "text": "Tenant B secret"},
]
def allowed(user, row):
    return row["tenant"] == user.tenant and bool(row["groups"] & user.groups)

def retrieve(user, query):
    # A real vector backend must enforce this predicate before top-k selection.
    candidates = [r for r in records if allowed(user, r)]
    ranked = sorted(candidates, key=lambda r: len(set(query.lower().split()) & set(r["text"].lower().split())), reverse=True)
    return [{"id": r["id"], "text": r["text"]} for r in ranked[:3] if allowed(user, r)]

user = Principal("a", frozenset({"staff"}))
evidence = retrieve(user, "hotel limit")
assert [r["id"] for r in evidence] == ["1"]
assert retrieve(Principal("c", frozenset({"staff"})), "hotel") == []
print(evidence)
```

### 实现说明、验收与项目边界

Principal 必须来自已认证会话，权限过滤在候选排名前执行，返回前再核验；父块与缓存同样适用。此代码不检测提示注入。抵御文档中恶意指令还需要工具权限收敛、把证据视为数据、输出结构校验，以及写操作的人审与幂等边界。
