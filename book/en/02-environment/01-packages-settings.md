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
