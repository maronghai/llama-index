# 07.01 Parent recovery and sentence windows

[返回全书目录 / Contents](../00-contents.md)

Retrieval and generation need not use the same granularity. Sentence-window retrieval matches short text then expands neighboring sentences. Parent recovery retrieves leaves and restores a broader parent passage. Both retain conditions without embedding entire chapters.

Window text is often stored in metadata and substituted during postprocessing. Exclude the window field from embedding to preserve narrow retrieval. Hierarchical methods require persisted nodes and parent-child relations. Merge overlapping parents before budgeting context.

Expanded context must still satisfy authorization and version constraints. Visibility of one sentence does not authorize its whole parent document. Align chunk boundaries with access boundaries when documents contain mixed permissions.

## Key points and difficulties

Key: narrow matching with broader synthesis. Difficulty: deduplication, permissions, and token budgets after expansion.

## Interview question and answer

Q: Why not embed parents directly? A: large parents may dilute semantics; leaves locate evidence and parents supply context, subject to measured benefit.

## Production pitfalls and mitigation

Pitfall: leaf vectors survive but parent text is missing. Validate relationships at build time and test parent restoration.

## Exercise and acceptance criteria

Compare sentence-only, window, and parent retrieval on a rule followed by an exception. Acceptance: preserve the exception without duplicated context.

## Implementation supplement: Sentence-window restoration and parent authorization

Dependencies: Python 3.10+; install `llama-index-core==0.14.25`.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
from llama_index.core import Document
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
from llama_index.core.schema import NodeWithScore

parser = SentenceWindowNodeParser.from_defaults(
    window_size=1, window_metadata_key="window", original_text_metadata_key="original",
    sentence_splitter=lambda text: [s.strip() + "." for s in text.split(".") if s.strip()])
doc = Document(text="Default limit is 500. Approved trips may use 800. Keep receipts.",
               metadata={"tenant": "a"})
nodes = parser.get_nodes_from_documents([doc])
hit = NodeWithScore(node=nodes[1], score=0.8)
assert hit.node.metadata["tenant"] == "a"
# Authorize every expanded source before applying this processor.
expanded = MetadataReplacementPostProcessor(target_metadata_key="window").postprocess_nodes([hit])
assert "500" in expanded[0].node.text and "800" in expanded[0].node.text
print(expanded[0].node.text)
```

### Implementation, acceptance and production boundaries

Retrieval uses one sentence while synthesis receives neighboring sentences. The custom splitter avoids downloading a sentence model; use language-aware splitting in production. Parent restoration must authorize expanded content, not only the matched child.

First-run note: core tokenization may download an encoding cache. Provision it and set `TIKTOKEN_CACHE_DIR` for offline use. No model key does not imply a network-free first run.
