# 06.01 响应合成、引用与拒答

[返回全书目录 / Contents](../00-contents.md)

检索器提供候选节点，节点后处理负责过滤、去重或重排，响应合成器按上下文预算生成答案。refine 可能逐块修订答案并产生多次调用，compact 倾向先打包上下文，tree_summarize 通过树形合并摘要。具体调用数量还受块长度和模型窗口影响，不能仅凭模式名估算费用。

提示应定义任务、证据边界、冲突规则和无答案行为。“只根据上下文”有帮助，但不是保证。应把答案拆成可验证主张，每个重要主张引用支持它的段落。source_nodes 说明提供过哪些材料，不等于每句话都被这些材料支持。引用可访问性也应受权限控制。

证据不足时可以拒答或请求补充条件。存在多个版本冲突时，优先根据权威来源与生效时间解决；无法解决则说明冲突并引用双方。不要用生成模型的常识覆盖内部制度中的明确约束。对高风险金额、日期和编号，可增加确定性校验。

## 重点与难点

重点：来源列表不等于逐主张支持。难点：长上下文中的冲突、例外和截断，不能仅靠一个提示解决。

## 面试考点与参考回答

问：RAG 仍会幻觉吗？答：会。可能检索错误、上下文不足、证据被截断，或生成超出证据；需要分层检测和拒答。

## 项目中的坑与处置

坑：只引用整份 PDF，用户无法定位支持句。处置：保存段落与页码映射，按主张给出细粒度引用，并核对引用是否真正支持答案。

## 动手实验与验收

构造一条可回答、一条无答案和一条版本冲突的问题。验收：分别给出有据回答、拒答和冲突说明，不能都生成确定性结论。

## 代码实现补充：带证据 ID 的保守回答

依赖：Python 3.10+；安装 `llama-index-core==0.14.25`。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
from llama_index.core.schema import TextNode, NodeWithScore

def answer(question, hits, allowed_ids):
    trusted = [h for h in hits if h.node.node_id in allowed_ids]
    if not trusted:
        return {"answer": "Insufficient evidence", "citations": []}
    # Extractive baseline: do not invent a claim not in evidence.
    return {"answer": trusted[0].node.text,
            "citations": [trusted[0].node.node_id]}

node = TextNode(id_="policy-2-p3", text="Hotel allowance is CNY 500 per night.")
hits = [NodeWithScore(node=node, score=0.9)]
result = answer("Hotel allowance?", hits, {"policy-2-p3"})
assert result["citations"] == ["policy-2-p3"]
assert answer("Hotel allowance?", hits, set())["citations"] == []
print(result)
```

### 实现说明、验收与项目边界

这是检索后抽取式基线，question 参数仅用于展示服务接口，尚未用于相关性判断；必须先由检索与相关性门禁筛选候选。生产可将正文交给响应合成器，但引用 ID 必须从授权证据集合选择，并检查每个事实是否被引用支持。非空证据不等于足以回答。

首次运行提示：核心包 tokenizer 可能下载编码缓存；离线环境请预置缓存并设置 `TIKTOKEN_CACHE_DIR`。无需模型密钥不代表首次运行不联网。
