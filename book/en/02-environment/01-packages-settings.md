# 02.01 Modular packages and Settings

[返回全书目录 / Contents](../00-contents.md)

LlamaIndex core and provider integrations are published separately. Installing llama-index-core does not install every integration. Examples should name dependency groups and record tested Python and package versions. “Latest” is not a reproducible version. This book does not claim an untested exact version combination is compatible.

Settings provides global defaults for components not supplied explicitly and is preferred over the older ServiceContext pattern. Configure chunking and embeddings before construction. Changing Settings.chunk_size does not rechunk existing nodes, and changing an embedding model does not rewrite stored vectors. Default model names are not a reliable basis for cost or dimension assumptions.

For multi-tenant services, pass models, retrievers, and stores explicitly rather than mutating Settings per request. Global values are shared across concurrent requests. Separate immutable startup defaults, index-build manifests, and request-level authorization parameters.

## Example and execution scope

These are command examples; run them in an isolated environment and record resolved versions.

```bash
# Illustrative installation commands; resolve and pin a tested set in your environment.
python -m pip install llama-index-core
python -m pip freeze
# Later examples name their additional integration packages where needed.
```

## Key points and difficulties

Key: distinguish core from integrations and configure explicitly. Difficulty: configuration changes do not automatically migrate already generated data.

## Interview question and answer

Q: Why does identical code fail on another machine? A: missing integrations, version drift, different services, or implicit defaults. Capture dependencies and configuration, then isolate import, construction, and request failures.

## Production pitfalls and mitigation

Pitfall: notebooks work only because previous cells left hidden state. Use explicit initialization and environment-provided credentials; never put secrets in the manuscript or logs.

## Exercise and acceptance criteria

Install core and required integrations in an isolated environment and record pip freeze and Python version. Acceptance: a fresh process imports successfully and clearly distinguishes offline from service-dependent examples.

## Implementation supplement: Explicit configuration and an environment fingerprint

Dependencies: Python 3.10+; install `llama-index-core==0.14.25`.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
import sys
from importlib.metadata import version
from llama_index.core import Settings, Document, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM

Settings.llm = MockLLM(max_tokens=16)
Settings.embed_model = MockEmbedding(embed_dim=8)
Settings.chunk_size = 128
Settings.chunk_overlap = 16
index = VectorStoreIndex.from_documents([Document(text="A reproducible offline baseline.")])
assert index.as_retriever(similarity_top_k=1).retrieve("baseline")
print({"python": sys.version.split()[0], "core": version("llama-index-core"),
       "embedding_dim": 8, "chunk_size": Settings.chunk_size})
```

### Implementation, acceptance and production boundaries

Run in an isolated process because Settings is global. Inject per-tenant model instances in production. Record this fingerprint plus corpus hashes, model versions and tokenizer; the core package version alone is insufficient.

First-run note: core tokenization may download an encoding cache. Provision it and set `TIKTOKEN_CACHE_DIR` for offline use. No model key does not imply a network-free first run.
