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

## Code Implementation Supplement:SimilarityPostprocessor Confidence Threshold Filtering Pipeline

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

Offline fixtures validate interfaces, provenance, and control flow, not semantic quality or security. Real-model branches additionally require `llama-index-llms-openai`, `llama-index-embeddings-openai`, and, for reranking, `llama-index-postprocessor-sbert-rerank`; set `RUN_REAL_MODELS=1`, `OPENAI_API_KEY`, `LLM_MODEL`, and `EMBED_MODEL` as required by the block. External-model branches have not been executed in this revision.

```python
import os
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.schema import NodeWithScore, TextNode

# Controlled scores verify the threshold contract, independent of model calibration.
candidates = [NodeWithScore(node=TextNode(text='Restart the server.'), score=0.9),
              NodeWithScore(node=TextNode(text='Cafeteria menu.'), score=0.2)]
filtered = SimilarityPostprocessor(similarity_cutoff=0.7).postprocess_nodes(candidates)
assert len(filtered) == 1 and filtered[0].node.text == 'Restart the server.'

real = os.getenv('RUN_REAL_MODELS') == '1'
if real:
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.llms.openai import OpenAI
    from llama_index.core.postprocessor import SentenceTransformerRerank
    embed = OpenAIEmbedding(model=os.environ['EMBED_MODEL'])
    llm = OpenAI(model=os.environ['LLM_MODEL'], timeout=30, max_retries=1)
    # Set RERANK_MODEL to a previously provisioned local model directory.
    reranker = SentenceTransformerRerank(model=os.environ['RERANK_MODEL'], top_n=1)
    processors = [reranker]
else:
    embed, llm = MockEmbedding(embed_dim=8), MockLLM(max_tokens=16)
    processors = []
index = VectorStoreIndex.from_documents([
    Document(text='Restart: drain requests, restart one replica, check health.'),
    Document(text='Cafeteria serves lunch at noon.')], embed_model=embed)
engine = index.as_query_engine(llm=llm, similarity_top_k=2,
                              node_postprocessors=processors, streaming=True)
response = engine.query('How should I restart a server?')
parts = []
for delta in response.response_gen:
    print(delta, end='', flush=True)
    parts.append(delta)
assert parts and response.source_nodes
print(chr(10), {'sources': len(response.source_nodes), 'real_reranker': real})
```

### Architecture and execution boundaries

Includes threshold filtering, an optional Cross-Encoder, and actual generator-based streaming. Default mode tests thresholds and streaming interfaces, not reranking quality. RUN_REAL_MODELS=1 enables real models and a provisioned local Cross-Encoder. Do not apply vector cutoffs directly to RRF scores.
