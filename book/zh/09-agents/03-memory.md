# 09.03 会话记忆、压缩与隔离

[返回全书目录 / Contents](../00-contents.md)

对话记忆解决多轮指代和任务连续性，不是可靠事实库。完整历史会增加 token 与隐私暴露；滑动窗口可能忘记关键约束；摘要压缩会引入失真。将稳定用户偏好、任务状态和近期消息分开管理，比把一切拼接到提示更可控。

会话标识需要同时绑定用户、租户与授权范围。仅以浏览器传来的 session_id 读取历史可能导致越权。历史与向量记忆都需要保留期限、删除机制和敏感信息策略。模型生成的“用户偏好”也要区分确认事实与推断。

权限变化后，历史中已出现的受限材料可能继续被模型引用。重新校验上下文或重建会话范围，必要时使旧会话失效。工具执行状态应放在可靠状态存储，不要依赖对话摘要记住某次写入是否已经完成。

## 重点与难点

重点：记忆分层并绑定身份。难点：压缩保真、撤权后历史清理和跨会话隔离。

## 面试考点与参考回答

问：记忆越长越好吗？答：不是，冗余与过时信息会增加成本和干扰；保留与当前任务相关且经过授权的内容。

## 项目中的坑与处置

坑：所有用户共用一个 ChatEngine 实例和历史。处置：按会话隔离状态，测试并发请求与随机 session_id 的负例。

## 动手实验与验收

运行两位用户的交错会话，再撤销其中一位权限。验收：无串话，撤权材料不进入后续上下文。

## 代码实现补充：按租户与会话隔离的有界记忆

依赖：Python 3.10+；仅使用 Python 标准库。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
from collections import defaultdict

class SessionMemory:
    def __init__(self, max_chars=120):
        self.data = defaultdict(list)
        self.max_chars = max_chars

    def append(self, tenant, user, session, role, text):
        if role not in {"user", "assistant"}:
            raise ValueError("untrusted role")
        if len(text) > self.max_chars:
            raise ValueError("message too long")
        key = (tenant, user, session)
        self.data[key].append({"role": role, "content": text})
        while sum(len(x["content"]) for x in self.data[key]) > self.max_chars:
            self.data[key].pop(0)

    def read(self, tenant, user, session):
        return [dict(x) for x in self.data.get((tenant, user, session), [])]

memory = SessionMemory()
memory.append("a", "u1", "s1", "user", "Hotel policy?")
assert memory.read("b", "u1", "s1") == []
assert memory.read("a", "u2", "s1") == []
assert len(memory.read("a", "u1", "s1")) == 1
print(memory.read("a", "u1", "s1"))
```

### 实现说明、验收与项目边界

这是内存存储适配层示例，不是对当前 LlamaIndex Memory API 的封装。接入聊天引擎前把 read 的结果转换为 ChatMessage。字符预算仅供演示，生产应使用模型 tokenizer，按完整对话轮裁剪，加 TTL、加密、并发控制和删除接口；摘要也继承租户与删除要求。
