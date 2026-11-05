# 13.01 提示注入、数据权限与输出安全 / Prompt injection, authorization, and output security

[返回全书目录 / Contents](../00-contents.md)

检索内容是不可信数据，文档可能包含“忽略规则”“发送密钥”等恶意文本。把系统指令与证据分区、标明来源能降低风险，但不能从根本上保证模型不会被影响。真正的安全边界在工具授权、数据范围、凭据隔离与执行策略中。

Retrieved documents are untrusted data and may contain malicious instructions. Separating instructions from evidence and labeling sources helps, but cannot guarantee immunity. Enforce boundaries through tool authorization, data scope, credential isolation, and execution policy.

权限在候选召回、扩展、重排、缓存与引用访问全程维持。若只在最终输出过滤，受限内容可能已经进入模型或日志。过滤下推通常有助于安全与效率，但后端能力不同，必须验证实际过滤是在候选前还是候选后执行，并测试召回影响。

Maintain authorization through retrieval, expansion, reranking, caches, and citation access. Final-output filtering is too late if private data already reached models or logs. Verify whether backend filtering happens before or after candidate selection and test both access and recall behavior.

输出也可能含 HTML、脚本片段或外部链接。展示层转义不可信文本，工具执行层不自动运行模型生成命令。敏感动作需要可信参数校验和最小权限身份。把攻击样本纳入回归，包括伪造系统消息、越权来源引用和工具结果注入。

Outputs may contain HTML, scripts, or links. Escape untrusted display content and do not automatically execute generated commands. Validate sensitive actions with least-privilege identities. Include forged system messages, unauthorized citations, and injected tool results in regression tests.

## 重点与难点 / Key points and difficulties

重点：模型不是权限执行器。难点：跨链路的数据流与派生内容泄漏。

Key: models are not authorization engines. Difficulty: data flow and derived-content leaks across the pipeline.

## 面试考点与参考回答 / Interview question and answer

问：提示中写“不要泄密”够吗？答：不够，必须用不可被模型覆盖的服务端授权、工具限制和数据隔离。

Q: Is a no-leak prompt enough? A: no. Use server-side authorization, tool restrictions, and data isolation outside model control.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：检索过滤正确但父块扩展带入秘密。处置：扩展阶段重新授权，权限边界与分块结构对齐。

Pitfall: parent expansion reintroduces secrets after filtered retrieval. Reauthorize expansions and align chunks with access boundaries.

## 动手实验与验收 / Exercise and acceptance criteria

构造恶意文档请求调用写工具和泄露密钥。验收：模型即使产生调用意图，工具与数据边界仍阻止越权。

Inject a document requesting unauthorized tools and secrets. Acceptance: execution controls block violations even if the model proposes them.

## 代码实现补充 / Implementation supplement: 检索前后双重授权与最小上下文 / Authorization before and after retrieval

依赖 / Dependencies: Python 3.10+; 仅标准库 / standard library only.

将完整代码保存为独立 `.py` 文件，在独立进程执行 `python filename.py`。无需密钥，无付费调用；验收为断言通过并输出结果。

Save the full block as a standalone `.py` file and run it in a separate process. No API key or paid call is needed; assertions must pass and results are printed.

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

### 实现说明、验收与项目边界 / Implementation, acceptance and production boundaries

Principal 必须来自已认证会话，权限过滤在候选排名前执行，返回前再核验；父块与缓存同样适用。此代码不检测提示注入。抵御文档中恶意指令还需要工具权限收敛、把证据视为数据、输出结构校验，以及写操作的人审与幂等边界。

Principal must come from an authenticated session. Filter before ranking and recheck before returning; apply the same rules to expanded parents and caches. This code does not detect prompt injection. Also constrain tools, treat retrieved text as data, validate outputs, and protect writes with review and idempotency.
