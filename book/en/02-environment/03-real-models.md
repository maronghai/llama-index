# 02.03 Real models and a measurable baseline

[返回全书目录 / Contents](../00-contents.md)

A real experiment records embedding and generation models, tokenizer, chunking, corpus snapshot, and index version. Embeddings define the retrieval space; generation determines how evidence is used. Providers may differ, or both may run locally. Local deployment still needs model files, memory, and an inference runtime.

The snippet illustrates HuggingFaceEmbedding and requires llama-index-embeddings-huggingface plus its inference dependencies. Read the model identifier from the environment and select a model suitable for the corpus language, query/document prefix convention, and license. Initial loading may download weights; offline deployments should provision an approved model path.

Hold generation fixed while comparing retrieval, then freeze retrieved evidence while comparing generation. Change one main factor per experiment. Track evidence recall, answer correctness, abstention, latency, and cost. If no run was performed, report an experiment plan rather than invented scores.

## Example and execution scope

Run with the prerequisites described above; some snippets demonstrate components rather than full applications.

```python
# Integration snippet; model weights and dependencies must be provisioned.
import os
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Document, VectorStoreIndex

embed = HuggingFaceEmbedding(model_name=os.environ["EMBED_MODEL"])
index = VectorStoreIndex.from_documents(
    [Document(text="Hotel claims require receipts.", id_="hotel")],
    embed_model=embed,
)
print(index.as_retriever(similarity_top_k=1).retrieve("hotel documentation"))
```

## Key points and difficulties

Key: models, corpus, and configuration jointly define an experiment. Difficulty: embeddings may differ in prefix conventions, normalization, and maximum input length.

## Interview question and answer

Q: Can same-dimensional embeddings be swapped directly? A: no. Equal dimensionality does not mean compatible coordinates. Queries and documents need compatible models and settings, usually requiring reindexing.

## Production pitfalls and mitigation

Pitfall: swapping only query embeddings silently degrades retrieval. Bind model identity to the index manifest and reject incompatible startup configurations.

## Exercise and acceptance criteria

Create at least 20 labeled questions covering synonyms, identifiers, missing answers, and time conditions. Acceptance: report errors per category rather than only an overall average.
