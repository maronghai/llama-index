# 06.01 Response synthesis, citations, and abstention

[返回全书目录 / Contents](../00-contents.md)

Retrievers supply candidates, node postprocessors filter or rerank them, and response synthesizers generate within a context budget. Refine may revise an answer across chunks; compact packs context first; tree_summarize combines summaries hierarchically. Actual calls also depend on context length and model limits.

Prompts should define the task, evidence boundaries, conflict handling, and abstention. “Use only context” helps but is not a guarantee. Associate important claims with supporting passages. source_nodes shows what material was supplied, not that every generated sentence is entailed by it. Citation access must also be authorized.

Abstain or request missing constraints when evidence is insufficient. Resolve conflicts using authority and effective dates; if unresolved, disclose the conflict and cite both sides. Do not override explicit internal rules with model background knowledge. Validate critical amounts, dates, and identifiers deterministically where possible.

## Key points and difficulties

Key: a source list is not claim-level support. Difficulty: conflicts, exceptions, and truncation need more than a prompt.

## Interview question and answer

Q: Can RAG hallucinate? A: yes, from wrong retrieval, insufficient or truncated context, or unsupported generation. Use layered checks and abstention.

## Production pitfalls and mitigation

Pitfall: citing a whole PDF leaves claims unverifiable. Retain passage/page mappings and check that granular citations support the answer.

## Exercise and acceptance criteria

Create answerable, unanswerable, and version-conflict questions. Acceptance: grounded answer, abstention, and disclosed conflict respectively.

## Implementation supplement: Conservative answers with evidence IDs

Dependencies: Python 3.10+; install `llama-index-core==0.14.25`.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

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

### Implementation, acceptance and production boundaries

This post-retrieval extractive baseline exposes a service signature; question is not used for relevance checking. Retrieval and relevance gates must run first. A generative synthesizer may replace extraction, but citation IDs must come from authorized evidence and support each claim. Nonempty evidence is not sufficient evidence.

First-run note: core tokenization may download an encoding cache. Provision it and set `TIKTOKEN_CACHE_DIR` for offline use. No model key does not imply a network-free first run.

## Code Implementation Supplement:Response Synthesizer Modes (Compact vs Tree Summarize) Comparison

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
from llama_index.core.response_synthesizers import get_response_synthesizer, ResponseMode

embed_model = MockEmbedding(embed_dim=256)
llm = MockLLM(max_tokens=64)
Settings.embed_model = embed_model
Settings.llm = llm

docs = [
    Document(text="Maintenance window is every Sunday at 02:00 AM UTC.", id_="doc_maint"),
    Document(text="Database backup retention is strictly 30 days.", id_="doc_backup")
]
index = VectorStoreIndex.from_documents(docs, embed_model=embed_model)

# 1. Compact 模式: 紧凑填充上下文到 Prompt 模板
synth_compact = get_response_synthesizer(llm=llm, response_mode=ResponseMode.COMPACT)
engine_compact = index.as_query_engine(llm=llm, response_synthesizer=synth_compact)
res_compact = engine_compact.query("When is maintenance?")
assert res_compact.source_nodes and len(res_compact.source_nodes) >= 1

# 2. Tree Summarize 模式: 层次归纳与长文档跨块提炼
synth_tree = get_response_synthesizer(llm=llm, response_mode=ResponseMode.TREE_SUMMARIZE)
engine_tree = index.as_query_engine(llm=llm, response_synthesizer=synth_tree)
res_tree = engine_tree.query("Summarize maintenance and backup rules.")
assert res_tree.source_nodes and len(res_tree.source_nodes) >= 1

print("Synthesis pipelines verified:")
print(f"- Compact source count: {len(res_compact.source_nodes)}")
print(f"- Tree Summarize source count: {len(res_tree.source_nodes)}")
```

### Architecture and execution boundaries

Explicitly configures distinct ResponseMode strategies to verify compact context packing and tree summarization pipelines alongside source tracking.
