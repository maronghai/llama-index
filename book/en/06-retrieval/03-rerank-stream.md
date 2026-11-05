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
