# 06.03 Reranking, thresholds, and streaming

[返回全书目录 / Contents](../00-contents.md)

Cross-encoders jointly encode queries and candidates, often improving fine-grained relevance at extra per-pair cost. Retrieve broadly, rerank a bounded pool, then select evidence under a context budget. Reranking cannot recover missing candidates or automatically establish authority and temporal validity.

Calibrate thresholds for the business task and score semantics. High thresholds suppress valid answers; low thresholds force weak evidence into unanswerable questions. Measure abstention, false rejection, and incorrect answers. A separate sufficiency decision can be more appropriate than one similarity cutoff. Check reranker truncation on long passages.

Streaming improves perceived responsiveness but does not eliminate computation or guarantee lower total latency. Some synthesis modes perform earlier calls before streaming the final one. Handle disconnects, cancellation, backpressure, and error events. For high-risk answers, validate critical claims before exposing irreversible partial text.

## Key points and difficulties

Key: optimize recall, reranking, and context selection separately. Difficulty: first-token and total latency differ, and validation timing affects streamed output.

## Interview question and answer

Q: Why can reranking hurt? A: bad candidates, domain mismatch, truncation, or an overly small final pool. Inspect examples before replacing models.

## Production pitfalls and mitigation

Pitfall: generation continues after disconnection. Propagate cancellation, release resources, and distinguish canceled from completed requests.

## Exercise and acceptance criteria

Measure candidate hits, first-token latency, and completion time with and without reranking, then disconnect a client. Acceptance: justify the latency tradeoff and verify cancellation.

## Implementation supplement: Reranking, missing scores and streaming boundaries

Dependencies: Python 3.10+; install `llama-index-core==0.14.25`.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

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

### Implementation, acceptance and production boundaries

Lexical overlap is an interpretable stand-in, not a cross-encoder, and requires tokenization for Chinese. Replace it with SentenceTransformerRerank plus its integration and a provisioned model. Calibrate thresholds for the actual reranker, not vector distances. This demonstrates chunk emission boundaries, not model streaming.

First-run note: core tokenization may download an encoding cache. Provision it and set `TIKTOKEN_CACHE_DIR` for offline use. No model key does not imply a network-free first run.
