# 08.02 Property graphs, entity resolution, and graph retrieval

[返回全书目录 / Contents](../00-contents.md)

Graphs suit explicit relationships and multi-hop questions, such as suppliers indirectly dependent on the same part. Evaluate PropertyGraphIndex and compatible graph stores for modern implementations. Historical KnowledgeGraphIndex tutorials are not automatically current recommendations. Check extractors and integrations for the selected release.

Extracting triples is only a start. Define entity types, directions, allowed properties, provenance, and effective dates. Resolve ambiguous names using context and business keys. Extracted edges are not verified facts, and errors can amplify across multiple hops.

Vectors can locate entities and passages, graphs can constrain traversal, and original text can ground the answer. Bound hops, visited nodes, and relationship types. Enforce tenant and access scope on graph edges, not just final text.

## Key points and difficulties

Key: graphs need schema and evidence. Difficulty: entity resolution, temporal relations, and error propagation.

## Interview question and answer

Q: Is graph RAG always better? A: no. Relationship-heavy tasks may benefit, but extraction and maintenance add complexity that needs measured justification.

## Production pitfalls and mitigation

Pitfall: merging names creates false cross-company relationships. Use namespaces and trusted keys; review uncertain matches.

## Exercise and acceptance criteria

Build a small graph with duplicate company names and a two-hop question. Acceptance: separate entities and evidence for every answer path.
