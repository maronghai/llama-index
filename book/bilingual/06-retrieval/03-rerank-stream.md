# 06.03 重排、阈值与流式响应 / Reranking, thresholds, and streaming

[返回全书目录 / Contents](../00-contents.md)

Cross-encoder 对查询与候选文本联合编码，通常比单独向量相似度更能识别细粒度相关性，但增加候选逐对计算成本。先粗召回，再对有限候选重排，最后按上下文预算选证据。重排不能恢复从未召回的节点，也不自动验证来源权威或时间适用性。

Cross-encoders jointly encode queries and candidates, often improving fine-grained relevance at extra per-pair cost. Retrieve broadly, rerank a bounded pool, then select evidence under a context budget. Reranking cannot recover missing candidates or automatically establish authority and temporal validity.

阈值要按业务与分数语义标定。过高会漏答，过低会给无答案问题硬找材料。记录拒答率、误拒率和错误回答率的权衡，必要时用额外的证据充分性分类，而不是单个相似度值。对长块检查重排器输入截断，否则例外可能在不可见的尾部。

Calibrate thresholds for the business task and score semantics. High thresholds suppress valid answers; low thresholds force weak evidence into unanswerable questions. Measure abstention, false rejection, and incorrect answers. A separate sufficiency decision can be more appropriate than one similarity cutoff. Check reranker truncation on long passages.

流式输出降低首 token 等待感，但不减少全部计算，也不保证总延迟更低。部分合成模式可能先完成多次非流式调用再输出最终流。流式接口还要处理断连、取消、背压和错误事件。高风险答案在校验前就展示不可撤回的片段，可能形成错误承诺，应选择先校验再输出关键结论。

Streaming improves perceived responsiveness but does not eliminate computation or guarantee lower total latency. Some synthesis modes perform earlier calls before streaming the final one. Handle disconnects, cancellation, backpressure, and error events. For high-risk answers, validate critical claims before exposing irreversible partial text.

## 重点与难点 / Key points and difficulties

重点：候选召回、重排、预算选择各自优化。难点：首 token 延迟与总延迟不同，流式内容的校验时机影响产品行为。

Key: optimize recall, reranking, and context selection separately. Difficulty: first-token and total latency differ, and validation timing affects streamed output.

## 面试考点与参考回答 / Interview question and answer

问：重排后质量下降为什么？答：可能候选已错、重排模型不懂领域、截断丢失条件，或 top-n 太小；检查成对样例而非盲目换模型。

Q: Why can reranking hurt? A: bad candidates, domain mismatch, truncation, or an overly small final pool. Inspect examples before replacing models.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：客户端断连后服务器继续完整生成。处置：传播取消信号，清理资源，并把被取消请求和正常完成分开统计。

Pitfall: generation continues after disconnection. Propagate cancellation, release resources, and distinguish canceled from completed requests.

## 动手实验与验收 / Exercise and acceptance criteria

测量无重排与重排的候选命中、首 token 和总延迟，再模拟断连。验收：能证明质量收益是否值得新增延迟，取消确实终止工作。

Measure candidate hits, first-token latency, and completion time with and without reranking, then disconnect a client. Acceptance: justify the latency tradeoff and verify cancellation.

## 代码实现补充 / Implementation supplement: 候选重排、空分数与流式边界 / Reranking, missing scores and streaming boundaries

依赖 / Dependencies: Python 3.10+; `llama-index-core==0.14.25`。

将完整代码保存为独立 `.py` 文件，在独立进程执行 `python filename.py`。无需密钥，无付费调用；验收为断言通过并输出结果。

Save the full block as a standalone `.py` file and run it in a separate process. No API key or paid call is needed; assertions must pass and results are printed.

```python
from llama_index.core.schema import TextNode, NodeWithScore

def lexical_rerank(question, candidates):
    terms = set(question.lower().split())
    def score(hit):
        return len(terms & set(hit.node.text.lower().split())) / max(1, len(terms))
    return sorted([(score(h), h) for h in candidates], key=lambda x: x[0], reverse=True)

def stream_selected(question, candidates, threshold=0.5):
    ranked = lexical_rerank(question, candidates)
    if not ranked or ranked[0][0] < threshold:
        yield "Insufficient evidence"
        return
    # Evidence is selected before the first visible token.
    for word in ranked[0][1].node.text.split():
        yield word + " "

candidates = [NodeWithScore(node=TextNode(text="office lunch noon"), score=None),
              NodeWithScore(node=TextNode(text="hotel allowance 500"), score=0.6)]
result = "".join(stream_selected("hotel allowance", candidates))
assert result.strip() == "hotel allowance 500"
assert "Insufficient" in "".join(stream_selected("payroll", candidates))
print(result)
```

### 实现说明、验收与项目边界 / Implementation, acceptance and production boundaries

词重合只是可解释的重排替身，不是 Cross-Encoder，也不适合直接处理未分词中文。真实项目可替换为 SentenceTransformerRerank，安装相应 postprocessor 集成并预置模型。阈值针对此重排器标定，不能混用向量距离；此处展示的是分块输出边界，并未调用模型流式接口。

Lexical overlap is an interpretable stand-in, not a cross-encoder, and requires tokenization for Chinese. Replace it with SentenceTransformerRerank plus its integration and a provisioned model. Calibrate thresholds for the actual reranker, not vector distances. This demonstrates chunk emission boundaries, not model streaming.

首次运行 / First run：tokenizer 可能下载编码缓存。离线运行需预置缓存并设置 `TIKTOKEN_CACHE_DIR`。Tokenization may download an encoding cache; provision it before offline use.
