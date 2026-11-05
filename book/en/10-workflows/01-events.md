# 10.01 Event-driven workflows and state

[返回全书目录 / Contents](../00-contents.md)

Workflows make steps and events explicit. Events carry data needed by subsequent steps; state retains shared information. These boundaries support timeouts, retries, and observation. Event typing still needs value validation, identity checks, and transition guards.

Modern LlamaIndex workflows can use the standalone llama-index-workflows package and workflows namespace; older examples may import from llama_index.core.workflow. Do not mix generations in one example. The snippet demonstrates a standalone StartEvent, custom event, and StopEvent flow with a tested dependency set required in your environment.

Use explicit business states such as RECEIVED, AUTHORIZED, RETRIEVED, VALIDATED, and COMPLETED, with failure and cancellation as terminal states. Record job identity, versions, and results at transitions. In-memory async execution alone does not provide crash recovery or durable workflows.

## Example and execution scope

See dependencies above; external integration execution has not been verified.

```python
# Requires llama-index-workflows; uses the standalone namespace.
import asyncio
from workflows import Workflow, step
from workflows.events import Event, StartEvent, StopEvent

class QueryReady(Event):
    query: str

class NormalizeFlow(Workflow):
    @step
    async def normalize(self, ev: StartEvent) -> QueryReady:
        query = ev.query.strip()
        if not query:
            raise ValueError("Empty query")
        return QueryReady(query=query)

    @step
    async def finish(self, ev: QueryReady) -> StopEvent:
        return StopEvent(result={"query": ev.query})

async def main():
    result = await NormalizeFlow(timeout=10).run(query="  receipts  ")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## Key points and difficulties

Key: distinguish events, state, and durability. Difficulty: duplicates, invalid transitions, and recovery.

## Interview question and answer

Q: Workflow versus agent? A: workflows explicitly control transitions, agents select actions through model decisions; an agent can run inside a bounded workflow.

## Production pitfalls and mitigation

Pitfall: assuming automatic resumption after restart. Use a durable runtime or explicitly persist checkpoints, idempotency keys, and event status.

## Exercise and acceptance criteria

Run the minimal workflow and add an invalid-input branch. Acceptance: invalid input never reaches retrieval and event fields are validated.

## Code Implementation Supplement:Event-Driven Decoupled RAG Pipeline with workflows

Python 3.10+; `llama-index-core==0.14.25`. Hybrid search additionally requires `llama-index-retrievers-bm25==0.8.0`; SQL uses SQLAlchemy; workflows uses the core dependency `llama-index-workflows`. Run the complete block in its own process. Tokenizer initialization may require a cache download; provision `TIKTOKEN_CACHE_DIR` for offline use.

Offline fixtures validate interfaces, provenance, and control flow, not semantic quality or security. Real-model branches additionally require `llama-index-llms-openai`, `llama-index-embeddings-openai`, and, for reranking, `llama-index-postprocessor-sbert-rerank`; set `RUN_REAL_MODELS=1`, `OPENAI_API_KEY`, `LLM_MODEL`, and `EMBED_MODEL` as required by the block. External-model branches have not been executed in this revision.

```python
import asyncio
from workflows import Workflow, step
from workflows.events import Event, StartEvent, StopEvent
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM
from llama_index.core.response_synthesizers import get_response_synthesizer

class QueryReady(Event):
    query: str
class EvidenceReady(Event):
    query: str
    nodes: list
class RAGWorkflow(Workflow):
    def __init__(self, retriever, **kwargs):
        super().__init__(**kwargs)
        self.retriever = retriever
        self.synthesizer = get_response_synthesizer(llm=MockLLM(max_tokens=16))
    @step
    async def validate(self, ev: StartEvent) -> QueryReady:
        query = str(ev.get('query', '')).strip()
        if not query or len(query) > 500:
            raise ValueError('Query must contain 1..500 characters')
        return QueryReady(query=query)
    @step
    async def retrieve(self, ev: QueryReady) -> EvidenceReady:
        nodes = await self.retriever.aretrieve(ev.query)
        return EvidenceReady(query=ev.query, nodes=nodes)
    @step
    async def answer(self, ev: EvidenceReady) -> StopEvent:
        if not ev.nodes:
            return StopEvent(result={'status': 'no_evidence', 'sources': []})
        response = await self.synthesizer.asynthesize(query=ev.query, nodes=ev.nodes)
        return StopEvent(result={'status': 'ok', 'answer': str(response),
            'sources': [n.node.ref_doc_id for n in response.source_nodes]})
async def main():
    index = VectorStoreIndex.from_documents([
        Document(text='Vacation requests require manager approval.', id_='policy')],
        embed_model=MockEmbedding(embed_dim=8))
    flow = RAGWorkflow(index.as_retriever(similarity_top_k=1), timeout=10)
    result = await flow.run(query='How do I request vacation?')
    assert result['sources'] == ['policy']
    class EmptyRetriever:
        async def aretrieve(self, query):
            return []
    empty = await RAGWorkflow(EmptyRetriever(), timeout=10).run(query='Unknown policy?')
    assert empty['status'] == 'no_evidence'
    print(result, empty)
if __name__ == '__main__':
    asyncio.run(main())
```

### Architecture and execution boundaries

The workflow invokes an actual asynchronous retriever and synthesizer and tests the no-evidence branch. Input length checks are not prompt-injection protection. Event decoupling alone does not guarantee throughput; measure blocking calls, resource budgets, and cancellation propagation.
