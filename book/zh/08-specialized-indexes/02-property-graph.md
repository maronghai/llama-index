# 08.02 属性图、实体消歧与图检索

[返回全书目录 / Contents](../00-contents.md)

图索引适合关系明确、需要多跳解释的问题，例如“哪些供应商间接依赖同一零件”。现代方案应考察 PropertyGraphIndex 与相应图存储集成；历史 KnowledgeGraphIndex 教程不能直接当作当前推荐接口。具体抽取器、图存储和向量组合需按所选版本核对。

抽取三元组或属性关系只是起点。需要定义实体类型、关系方向、允许属性、来源证据和生效时间。“Apple”是公司还是水果要通过上下文与业务主键消歧。模型抽取的关系不是已验证事实；错误边经过多跳传播可能放大误导。

图与向量可互补：向量定位相关实体与段落，图约束关系遍历，再返回原文支撑答案。限制跳数、节点数和路径类型，避免无界遍历。图中每条边也要执行租户和权限检查，不能只过滤最终文本。

## 重点与难点

重点：图结构需要模式与证据。难点：实体消歧、时态关系和错误传播。

## 面试考点与参考回答

问：Graph RAG 总比向量 RAG 好吗？答：不。关系密集任务可能受益，但抽取、维护和查询更复杂，应比较质量收益与成本。

## 项目中的坑与处置

坑：同名实体合并导致跨公司关系。处置：使用来源命名空间与可信主键，低置信匹配进入审核。

## 动手实验与验收

建立含同名公司的小图，设计两跳问题。验收：不会错误合并实体，每条答案路径可定位原始证据。

## 代码实现补充：有证据的属性图与受限遍历

依赖：Python 3.10+；仅使用 Python 标准库。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
from collections import deque

edges = [
    {"src": "org:acme", "rel": "OWNS", "dst": "product:x", "tenant": "a", "evidence": "doc-1"},
    {"src": "product:x", "rel": "USES", "dst": "tech:y", "tenant": "a", "evidence": "doc-2"},
    {"src": "product:x", "rel": "USES", "dst": "secret:z", "tenant": "b", "evidence": "doc-3"},
]

def traverse(start, tenant, max_hops=2):
    queue = deque([(start, 0)])
    visited = {start}
    result = []
    while queue:
        node, depth = queue.popleft()
        if depth >= max_hops:
            continue
        for edge in edges:
            if edge["src"] == node and edge["tenant"] == tenant:
                result.append(edge)
                if edge["dst"] not in visited:
                    visited.add(edge["dst"])
                    queue.append((edge["dst"], depth + 1))
    return result

result = traverse("org:acme", "a")
assert len(result) == 2 and all(e["evidence"] for e in result)
assert all(e["dst"] != "secret:z" for e in result)
print(result)
```

### 实现说明、验收与项目边界

这是属性图检索的参考算法，不是 PropertyGraphIndex 集成测试。实体使用命名空间稳定 ID，关系携带证据与租户。真实抽取器输出三元组后必须校验实体消歧、关系类型与证据，再写入 PropertyGraphIndex 的图存储；生产遍历还要限制边数、时间与高出度节点。
