# 12.03 Token 成本与质量约束优化 / Token cost and quality-constrained optimization

[返回全书目录 / Contents](../00-contents.md)

成本既包括生成，也包括嵌入、解析、重排、存储、网络和评估。一次查询可能触发改写、路由、多个子问题及裁判调用，不能只看最终回答的 token。用调用树汇总费用，并区分摄取一次性成本与在线边际成本。

Cost includes generation, embedding, parsing, reranking, storage, networking, and evaluation. Rewriting, routing, subquestions, and judging add calls beyond the final answer. Aggregate through the call tree and separate ingestion costs from online marginal costs.

下面的计算公式是估算器，不包含任何实际报价。输入与输出单价按每百万 token 传入，模型价格变化时更新价格表和生效日期。账单还可能包含缓存折扣、批处理、工具和最小计费单位，应和供应商账单对账，而不是只依赖客户端 tokenizer。

The estimator below contains no actual prices. Supply input and output prices per million tokens and version the rate table. Billing may include caching, batches, tools, or minimum units; reconcile against provider usage rather than relying solely on local tokenization.

优化顺序应先消除重复摄取和无效调用，再减少候选与上下文，最后考虑模型分层。小模型适合部分路由或结构化提取，但必须满足同一质量门禁。按成功任务成本比较，比只看单次请求成本更能体现误答与重试代价。

First remove duplicate ingestion and unnecessary calls, then reduce candidates and context, then consider model tiers. Smaller models can handle selected routing or extraction tasks if quality gates hold. Cost per successful task captures errors and retries better than cost per request.

## 示例与运行边界 / Example and execution scope

纯 Python 独立算法示例；不调用外部服务。

Standalone pure-Python algorithm example without external services.

```python
from decimal import Decimal

def token_cost(input_tokens, output_tokens, input_per_million, output_per_million):
    if min(input_tokens, output_tokens) < 0:
        raise ValueError("Token counts cannot be negative")
    million = Decimal("1000000")
    return (Decimal(input_tokens) * Decimal(str(input_per_million))
            + Decimal(output_tokens) * Decimal(str(output_per_million))) / million
# Supply actual versioned rates; no price is assumed here.
assert token_cost(0, 0, "0", "0") == 0
```

## 重点与难点 / Key points and difficulties

重点：完整调用树计费。难点：价格版本、真实账单对账与质量不退化。

Key: account for the whole call tree. Difficulty: rate versions, billing reconciliation, and quality preservation.

## 面试考点与参考回答 / Interview question and answer

问：怎样降本而不明显降质？答：先测各阶段成本，移除重复工作，缩短无效上下文，按任务选模型，并用回归集验证。

Q: How can cost fall without material quality loss? A: measure stage costs, remove duplicates, trim irrelevant context, select models by task, and validate regressions.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：仅减少输出长度，忽略多次昂贵路由。处置：统计所有调用和每个成功任务的总成本。

Pitfall: trimming answers while ignoring expensive routing loops. Track all calls and total cost per successful task.

## 动手实验与验收 / Exercise and acceptance criteria

为一个含路由、检索和生成的请求建立成本账本。验收：明确哪些数字是估算、实测 usage 和账单金额。

Build a cost ledger for routing, retrieval, and generation. Acceptance: distinguish estimates, measured usage, and billed amounts.
