# 06.02 BM25, dense retrieval, and RRF

[返回全书目录 / Contents](../00-contents.md)

BM25 matches terms and is useful for identifiers, rare terminology, and exact names. Dense embeddings handle semantic paraphrases but may confuse nearby numbers. Hybrid retrieval combines candidates from both channels. Chinese BM25 requires suitable tokenization and domain handling; an English default is not a valid Chinese baseline.

Reciprocal rank fusion sums 1/(c+rank), with ranks starting at one. Ranking avoids directly adding incompatible BM25 and vector scores, but channel weights, candidate counts, and deduplication keys still matter. Tune on development data rather than repeatedly optimizing against the final test set.

Maintain authorization through both channels. Different corpus versions can reintroduce deleted or stale content. Align candidates using stable node IDs and retain channel, original rank, and fused score. String-only deduplication can incorrectly merge evidence with different provenance or exceptions.

## Example and execution scope

Standalone pure-Python algorithm example without external services.

```python
from collections import defaultdict
def rrf(rankings, c=60):
    if c < 0:
        raise ValueError("c must be nonnegative")
    scores = defaultdict(float)
    for ranking in rankings:
        unique = list(dict.fromkeys(ranking))
        for rank, node_id in enumerate(unique, start=1):
            scores[node_id] += 1.0 / (c + rank)
    return sorted(scores.items(), key=lambda x: (-x[1], x[0]))
print(rrf([["a", "b", "c"], ["b", "d", "a"]]))
```

## Key points and difficulties

Key: sparse and dense methods complement each other; RRF combines ranks. Difficulty: Chinese tokenization, stable identity, and synchronized corpora.

## Interview question and answer

Q: Why not add BM25 and cosine scores directly? A: their scales differ. Use rank fusion or learned calibration.

## Production pitfalls and mitigation

Pitfall: tiny candidate pools exclude the right evidence before fusion. Measure candidate recall before tuning fusion and reranking.

## Exercise and acceptance criteria

Compare channels and fusion on identifiers, synonyms, and mixed-language questions. Acceptance: show unique wins and fusion failures, not just an aggregate claim.

## Code Implementation Supplement:Hybrid Search: QueryFusionRetriever Combining BM25 and Dense Vectors via RRF

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

from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.llms import MockLLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever

embed_model = MockEmbedding(embed_dim=256)
llm = MockLLM(max_tokens=32)
Settings.embed_model = embed_model
Settings.llm = llm

docs = [
    Document(text="Apollo 11 landed humans on the Moon in July 1969.", id_="apollo_11"),
    Document(text="Artemis 3 program aims to land astronauts near the lunar South Pole.", id_="artemis_3"),
    Document(text="The International Space Station conducts microgravity experiments.", id_="iss")
]
nodes = SentenceSplitter(chunk_size=128, chunk_overlap=16).get_nodes_from_documents(docs)

# 1. 稠密向量检索器 (Dense Vector) 与稀疏关键词检索器 (Sparse BM25)
vector_index = VectorStoreIndex(nodes, embed_model=embed_model)
vector_retriever = vector_index.as_retriever(similarity_top_k=2)
bm25_retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=2)

# 2. QueryFusionRetriever 聚合两路候选，使用 RRF (Reciprocal Rank Fusion)
fusion_retriever = QueryFusionRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    similarity_top_k=2,
    mode="reciprocal_rerank",
    num_queries=1,
    use_async=False,
    llm=llm
)
results = fusion_retriever.retrieve("Apollo Moon landing 1969")

assert len(results) > 0
print("Hybrid Fusion search verified successfully:")
print(f"- Total merged candidates: {len(results)}")
print(f"- Top ranked document: {results[0].node.ref_doc_id}")

assert bm25_retriever.retrieve('Apollo Moon landing 1969')[0].node.ref_doc_id == 'apollo_11'
assert results[0].node.ref_doc_id == 'apollo_11'
assert len({h.node.node_id for h in results}) == len(results)
```

### Architecture and execution boundaries

Integrates official BM25Retriever and VectorStoreIndex via QueryFusionRetriever using Reciprocal Rank Fusion, explicitly configuring Mock models.
