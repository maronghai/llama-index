# 07.03 Question decomposition and multi-document comparison

[返回全书目录 / Contents](../00-contents.md)

A multi-company revenue comparison contains entities, years, and calculations. Decomposition retrieves individual facts before synthesis. Sub-question patterns support this workflow, but plans can omit requirements or add assumptions and therefore need validation.

Retain units, periods, provenance, and missingness for each result. Fiscal and calendar years or consolidated and standalone figures are not directly comparable. Align structured facts before deterministic growth calculations; zero denominators and missing values require explicit unavailable results.

Parallel independent questions can reduce critical-path latency while increasing concurrency and cost. Bound task duration, step duration, question count, and partial-failure behavior. Clearly distinguish complete conclusions from observations based on incomplete evidence.

## Key points and difficulties

Key: separate planning, extraction, computation, and synthesis. Difficulty: aligning units and reporting periods.

## Interview question and answer

Q: How do you prevent decomposition drift? A: convert requirements into a checklist, validate sub-question coverage, and verify final coverage.

## Production pitfalls and mitigation

Pitfall: failed subqueries become zeros in calculations. Preserve missingness and reject incomplete computation.

## Exercise and acceptance criteria

Compare reports with different periods. Acceptance: reject incompatible comparisons, obtain aligned facts, then calculate with citations.

## Implementation supplement: Budgeted sub-question planning and aggregation

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Task:
    source: str
    question: str

facts = {"a": {"hotel": 500}, "b": {"hotel": 650}}

def execute_plan(tasks, authorized, max_calls=3):
    if len(tasks) > max_calls:
        raise ValueError("plan exceeds call budget")
    results = []
    for task in tasks:
        if task.source not in authorized:
            raise PermissionError(task.source)
        value = facts.get(task.source, {}).get(task.question)
        results.append({"source": task.source, "value": value, "ok": value is not None})
    return results

plan = [Task("a", "hotel"), Task("b", "hotel")]
rows = execute_plan(plan, {"a", "b"})
assert all(r["ok"] for r in rows)
difference = rows[1]["value"] - rows[0]["value"]
assert difference == 150
print({"evidence": rows, "difference": difference})
```

### Implementation, acceptance and production boundaries

A manual plan separates decomposition quality from execution reliability. With SubQuestionQueryEngine, validate generated plans against source authorization, call and time budgets. Missing values are failures, not zero; align units, currencies and effective dates before comparison.

## Code Implementation Supplement:SubQuestionQueryEngine Atomic Decomposition and Execution Pipeline

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

from typing import Sequence, List
from llama_index.core import Document, VectorStoreIndex, Settings, QueryBundle
from llama_index.core.llms import MockLLM
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.question_gen.types import BaseQuestionGenerator, SubQuestion

embed_model = MockEmbedding(embed_dim=256)
llm = MockLLM(max_tokens=64)
Settings.embed_model = embed_model
Settings.llm = llm

docs_2024 = [Document(text="Year 2024 Revenue was 100M USD.", id_="doc_2024")]
docs_2025 = [Document(text="Year 2025 Revenue was 130M USD.", id_="doc_2025")]

idx_2024 = VectorStoreIndex.from_documents(docs_2024, embed_model=embed_model)
idx_2025 = VectorStoreIndex.from_documents(docs_2025, embed_model=embed_model)

tools = [
    QueryEngineTool(query_engine=idx_2024.as_query_engine(llm=llm), metadata=ToolMetadata(name="fin_2024", description="2024 Financials")),
    QueryEngineTool(query_engine=idx_2025.as_query_engine(llm=llm), metadata=ToolMetadata(name="fin_2025", description="2025 Financials"))
]

# 确定性子问题生成器：将复合对比转化为两个原子查询
class DeterministicQuestionGenerator(BaseQuestionGenerator):
    def _get_prompts(self):
        return {}
    def _update_prompts(self, prompts):
        pass
    def generate(self, tools: Sequence[ToolMetadata], query: QueryBundle) -> List[SubQuestion]:
        return [
            SubQuestion(sub_question="What was the revenue in 2024?", tool_name="fin_2024"),
            SubQuestion(sub_question="What was the revenue in 2025?", tool_name="fin_2025")
        ]
    async def agenerate(self, tools: Sequence[ToolMetadata], query: QueryBundle) -> List[SubQuestion]:
        return self.generate(tools, query)

sub_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=tools,
    question_gen=DeterministicQuestionGenerator(),
    llm=llm,
    use_async=False
)

response = sub_engine.query("Compare revenue between 2024 and 2025")
assert response.source_nodes is not None
print("SubQuestionQueryEngine verified; gathered source count:", len(response.source_nodes))

source_ids = {s.node.ref_doc_id for s in response.source_nodes if s.node.ref_doc_id}
assert {'doc_2024', 'doc_2025'} <= source_ids
# Compute with verified structured values rather than asking the LLM to do arithmetic.
revenue = {'2024': 100, '2025': 130}
growth = (revenue['2025'] / revenue['2024'] - 1) * 100
assert round(growth, 2) == 30.0
print({'verified_growth_percent': round(growth, 2)})
```

### Architecture and execution boundaries

The deterministic generator is limited to this two-year fixture. Replace it with LLMQuestionGenerator.from_defaults(llm=real_llm) for open-ended planning, validating tool names, call budgets, and authorization. Both yearly sources are checked; growth is computed separately from verified structured values.
