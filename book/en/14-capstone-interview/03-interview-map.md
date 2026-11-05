# 14.03 Priority map and interview communication

[返回全书目录 / Contents](../00-contents.md)

Use three priority tiers. Essentials: Documents and Nodes, explicit configuration, parsing, chunking, vectors, citations, and evaluation. Intermediate: hybrid retrieval, reranking, parent recovery, routing, and updates. Task-dependent: graphs, multiple agents, and multimodality. Establish reliability before adding complexity.

Interview question one: improve retrieval by first validating labels and failure slices, then parsing, embeddings, chunking, candidate fusion, and reranking, with costs. Question two: reduce hallucination by distinguishing missing data, insufficient retrieval, and unsupported generation. Question three: implement incremental sync with stable IDs, hashes, checkpoints, deletion propagation, and reconciliation.

Question four: production readiness requires separate builds, versioned releases, authorization, limits, traces, gates, and rollback. Question five: choose stores by filtering, scale, operations, recovery, tenancy, and team capability. Question six: establish impact using a fixed baseline, split datasets, paired outcomes, failures, and real costs.

Present projects as goals, constraints, baseline, failures, decisions, validation, and results. Clearly identify designs and unmeasured experiments. Technical terms matter only when you can explain their purpose, failure modes, and verification.

## Key points and difficulties

Key: master a reproducible baseline and add advanced patterns in response to failures. Difficulty: turn concepts into verifiable engineering decisions.

## Interview question and answer

Q: What value does LlamaIndex provide? A: common abstractions and integrations for data, nodes, retrieval, synthesis, tools, and workflows, reducing orchestration work while leaving business and production responsibilities to developers.

## Production pitfalls and mitigation

Pitfall: memorizing APIs without tradeoffs. Prepare one failure, experiment, and unsuitable use case for each concept.

## Exercise and acceptance criteria

Present the project in five minutes, then handle half-budget, offline-only, and immediate-revocation constraints. Acceptance: adapt the design without inventing results.

## Implementation supplement: Structuring interview answers around evidence

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
from dataclasses import dataclass

@dataclass
class Experiment:
    name: str
    recall_before: float
    recall_after: float
    p95_before_ms: int
    p95_after_ms: int
    samples: int

    def report(self):
        if self.samples < 1:
            raise ValueError("sample count is required")
        return {
            "change": self.name,
            "recall_delta_pp": round(100 * (self.recall_after - self.recall_before), 2),
            "latency_delta_ms": self.p95_after_ms - self.p95_before_ms,
            "samples": self.samples,
        }

experiment = Experiment("hybrid retrieval", 0.72, 0.84, 600, 750, 200)
report = experiment.report()
assert report["recall_delta_pp"] == 12.0 and report["latency_delta_ms"] == 150
print(report)
print("Explain: symptom -> hypothesis -> controlled change -> evidence -> tradeoff -> rollback")
```

### Implementation, acceptance and production boundaries

Numbers are hypothetical and must not be presented as personal project results. Explain labeling, sample size, failure slices, latency cost and controlled conditions. A 12-percentage-point change is not 12% relative growth. Replace inputs with your own evaluation artifacts and discuss uncertainty and the next experiment.
