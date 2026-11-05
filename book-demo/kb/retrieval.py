"""LlamaIndex dense retrieval + BM25 + reciprocal rank fusion."""
import json
import math
from collections import Counter
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode
from .models import tokens, answer


def chunk(text, size=600, overlap=80):
    # Character windows are deterministic for both Chinese and English, no tokenizer download.
    return [text[i:i+size] for i in range(0, len(text), size-overlap) if text[i:i+size].strip()]


def search(config, embeddings, rows, question, top_k):
    if not rows:
        return []
    nodes = [TextNode(id_=r['id'], text=r['text'], embedding=json.loads(r['vector']),
                      metadata={'document_id': r['doc'], 'version': r['version']},
                      excluded_embed_metadata_keys=['document_id', 'version']) for r in rows]
    index = VectorStoreIndex(nodes, embed_model=embeddings)
    dense = index.as_retriever(similarity_top_k=min(len(rows), top_k*4)).retrieve(question)
    query = set(tokens(question))
    bags = [Counter(tokens(r['text'])) for r in rows]
    lengths = [sum(b.values()) for b in bags]
    avg = sum(lengths) / len(rows) or 1
    df = {t: sum(t in b for b in bags) for t in query}
    scores = []
    for row, bag, length in zip(rows, bags, lengths):
        score = sum(math.log(1+(len(rows)-df[t]+0.5)/(df[t]+0.5)) *
                    (bag[t]*2.2)/(bag[t]+1.2*(0.25+0.75*length/avg)) for t in query if bag[t])
        if score > 0:
            scores.append((row['id'], score))
    lexical = sorted(scores, key=lambda x: (-x[1], x[0]))[:top_k*4]
    # Offline hashes are not semantic embeddings; require lexical support to avoid hash collisions.
    eligible = {i for i, _ in scores}
    ranks = {}
    for ranking in ([(n.node.node_id, n.score or 0) for n in dense], lexical):
        for rank, (node_id, score) in enumerate(ranking, 1):
            if score <= 0 or (config.mode == 'offline' and node_id not in eligible):
                continue
            ranks[node_id] = ranks.get(node_id, 0) + 1/(60+rank)
    by_id = {r['id']: r for r in rows}
    result = []
    for node_id, score in sorted(ranks.items(), key=lambda x: (-x[1], x[0]))[:top_k]:
        r = by_id[node_id]
        result.append({'document_id': r['doc'], 'title': r['title'], 'version': r['version'],
                       'chunk': r['position'], 'text': r['text'], 'score': score})
    return result


def query(config, store, embeddings, principal, question, top_k, request_id):
    evidence = search(config, embeddings, store.snapshot(principal), question, top_k)
    text, refused = answer(config, question, evidence)
    store.validate_evidence(principal, evidence, request_id)
    return {'answer': text, 'refused': refused, 'citations': evidence,
            'mode': config.mode, 'request_id': request_id}
