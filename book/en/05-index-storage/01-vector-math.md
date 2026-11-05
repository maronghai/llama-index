# 05.01 VectorStoreIndex and vector retrieval

[返回全书目录 / Contents](../00-contents.md)

Vector retrieval maps queries and nodes into a compatible representation space and ranks candidates by distance or similarity. Cosine divides the dot product by vector norms; normalized dot-product ranking equals cosine ranking. Euclidean distance normally decreases with closeness, but returned scores may be transformed. Confirm backend semantics before setting cutoffs.

VectorStoreIndex connects nodes with vector storage; it is not a particular database. from_documents builds nodes from documents, while direct node construction requires awareness of existing embeddings. In-memory defaults suit experiments but do not survive restart automatically. Large stores often use approximate search with recall, latency, and memory tradeoffs.

Top-k specifies candidate count, not confidence. Nearest-neighbor search returns something even when the answer is absent. Add evidence-sufficiency checks and abstention. Larger k cannot repair model mismatch, bad indexing, or incorrect authorization filters.

## Example and execution scope

Standalone pure-Python algorithm example without external services.

```python
import math
def cosine(a, b):
    denom = math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(y*y for y in b))
    if denom == 0:
        raise ValueError("Zero vector has undefined cosine")
    return sum(x*y for x,y in zip(a,b, strict=True)) / denom
assert abs(cosine([1, 0], [2, 0]) - 1.0) < 1e-12
print(cosine([1, 0], [0, 1]))
```

## Key points and difficulties

Key: similarity is not probability. Difficulty: approximation, filtering, and candidate counts jointly affect recall.

## Interview question and answer

Q: Does vector retrieval guarantee truth? A: no. It measures representation-level relevance; validity, provenance, and evidence still need checking.

## Production pitfalls and mitigation

Pitfall: interpreting 0.8 as 80% correctness. Calibrate decision thresholds on labeled examples and bind them to a model and backend.

## Exercise and acceptance criteria

Compute cosine on two-dimensional vectors and compare raw versus normalized dot products. Acceptance: explain equal cosine for vectors with the same direction but different magnitudes.

## Code Implementation Supplement:Cosine Similarity Math Formulation Aligned with VectorStoreIndex

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

Offline fixtures validate interfaces, provenance, and control flow, not semantic quality or security. Real-model branches additionally require `llama-index-llms-openai`, `llama-index-embeddings-openai`, and, for reranking, `llama-index-postprocessor-sbert-rerank`; set `RUN_REAL_MODELS=1`, `OPENAI_API_KEY`, `LLM_MODEL`, and `EMBED_MODEL` as required by the block. External-model branches have not been executed in this revision.

```python
import hashlib
import math
import re
from llama_index.core.embeddings import MockEmbedding as _MockEmbedding

class MockEmbedding(_MockEmbedding):
    # Test-only hashed lexical vectors; NOT a semantic embedding model.
    def _vector(self, text):
        values = [0.0] * 256
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            slot = int(hashlib.sha256(word.encode()).hexdigest()[:8], 16) % 256
            values[slot] += 1.0
        norm = math.sqrt(sum(v*v for v in values)) or 1.0
        return [v / norm for v in values]
    def _get_text_embedding(self, text):
        return self._vector(text)
    def _get_query_embedding(self, query):
        return self._vector(query)
    async def _aget_query_embedding(self, query):
        return self._vector(query)

import math
from llama_index.core import Document, VectorStoreIndex

def manual_cosine(v1: list, v2: list) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    return dot / (norm1 * norm2) if norm1 and norm2 else 0.0

embed_model = MockEmbedding(embed_dim=256)
doc1 = Document(text="Deep learning neural network architectures", id_="doc_ai")
doc2 = Document(text="Financial investment and asset management", id_="doc_finance")

index = VectorStoreIndex.from_documents([doc1, doc2], embed_model=embed_model)
retriever = index.as_retriever(similarity_top_k=2)
candidates = retriever.retrieve("neural network models")

assert len(candidates) == 2
print("VectorStoreIndex retrieved nodes:")
for c in candidates:
    print(f"- Node: {c.node.ref_doc_id}, score: {getattr(c, 'score', 'N/A')}")

query_vec = embed_model.get_query_embedding('neural network models')
for hit in candidates:
    node_vec = embed_model.get_text_embedding(hit.node.get_content())
    expected = manual_cosine(query_vec, node_vec)
    assert abs(hit.score - expected) < 1e-6
assert candidates[0].node.ref_doc_id == 'doc_ai'
assert manual_cosine([0,0], [1,0]) == 0
```

### Architecture and execution boundaries

Reproducible hashed lexical vectors allow every framework score to be compared with manual cosine, including zero-vector handling. This test encoder does not measure semantic quality; changing the embedding model requires rebuilding vectors.
