"""Real model diagnostics and HTTP service ingestion/evaluation; no synthetic responses."""
import hashlib
import json
import math
import os
import time
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from .config import Config
from .models import Embeddings, answer


def doctor():
    config = Config.from_env()
    config.validate()
    if config.mode != 'remote':
        raise ValueError('doctor requires KB_MODE=remote; offline demo is not model verification')
    start = time.monotonic()
    embeddings = Embeddings(config)
    vectors = embeddings.get_text_embedding_batch(['差旅报销制度', 'Travel reimbursement policy'])
    text, refused = answer(config, '报销上限是多少？', [{'text': '报销上限为每晚600元。'}])
    # Tests connectivity and contract only, never equates this to semantic quality.
    return {'mode': 'remote', 'embedding_count': len(vectors), 'dimension': len(vectors[0]),
            'generation_cited': not refused, 'passed': not refused,
            'elapsed_ms': round((time.monotonic()-start)*1000, 2),
            'scope': 'Real embedding and generation connectivity; not a quality benchmark'}


def service_client():
    base = os.environ.get('KB_SERVICE_URL', '').rstrip('/')
    key = os.environ.get('KB_CLIENT_KEY', '')
    url = urlsplit(base)
    if not key or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError('Set KB_SERVICE_URL and KB_CLIENT_KEY')
    if url.scheme != 'https' and not (url.scheme == 'http' and url.hostname in ('127.0.0.1', 'localhost', '::1')):
        raise ValueError('Service requires HTTPS except on loopback')
    return httpx.Client(base_url=base, headers={'Authorization': 'Bearer '+key},
                        timeout=float(os.getenv('KB_CLIENT_TIMEOUT', '120')), follow_redirects=False)


def ingest_directory(root):
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Input must be a directory')
    results = []
    with service_client() as client:
        for source in sorted(root.rglob('*')):
            if source.is_symlink() or not source.is_file() or source.suffix.lower() not in ('.txt', '.md'):
                continue
            relative = source.relative_to(root).as_posix()
            if source.stat().st_size > 800000:
                raise ValueError('Text file exceeds byte budget: '+relative)
            text = source.read_text(encoding='utf-8-sig')
            if not text.strip() or len(text) > 200000:
                raise ValueError('Blank or oversized text: '+relative)
            # Stable within this import namespace. A separate root with identical relative paths
            # is the same logical collection; use a distinct prefix for independent collections.
            namespace = os.getenv('KB_IMPORT_NAMESPACE', 'directory')
            doc_id = hashlib.sha256((namespace+'\0'+relative).encode()).hexdigest()
            current = client.get('/v1/documents/'+doc_id)
            if current.status_code == 404:
                version = 0
            else:
                current.raise_for_status()
                doc = current.json()
                if doc['content'] == text and doc['title'] == relative[:200]:
                    results.append({'source': relative, 'document_id': doc_id, 'status': 'unchanged'})
                    continue
                version = doc['version']
            payload = {'doc_id': doc_id, 'title': relative[:200], 'text': text, 'expected_version': version}
            payload['idempotency_key'] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
            response = client.post('/v1/jobs/ingest', json=payload)
            response.raise_for_status()
            job = response.json()
            results.append({'source': relative, 'document_id': doc_id, 'job_id': job['id'], 'status': job['status']})
    return {'files': results, 'note': 'Accepted jobs require a running worker; no missing-file deletion is performed'}


def evaluate(dataset, output, min_score=0.8):
    if not math.isfinite(min_score) or not 0 <= min_score <= 1:
        raise ValueError('min-score must be between 0 and 1')
    if output.exists():
        raise ValueError('Report target already exists')
    cases = [json.loads(line) for line in dataset.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    if not cases:
        raise ValueError('Evaluation dataset is empty')
    for case in cases:
        if not isinstance(case.get('question'), str) or not case['question'].strip():
            raise ValueError('Each case requires question')
        if type(case.get('expected_refused')) is not bool:
            raise ValueError('Each case requires boolean expected_refused')
        if not case['expected_refused'] and (not case.get('expected_document_ids') or not case.get('answer_contains')):
            raise ValueError('Answer cases require expected_document_ids and answer_contains')
        for field in ('expected_document_ids', 'answer_contains'):
            if field in case and (not isinstance(case[field], list) or not all(isinstance(v,str) and v for v in case[field])):
                raise ValueError(field+' must be a list of nonempty strings')
    rows = []
    with service_client() as client:
        for number, case in enumerate(cases, 1):
            start = time.monotonic()
            try:
                response = client.post('/v1/query', json={'question': case['question'], 'top_k': case.get('top_k', 4)})
                response.raise_for_status()
                data = response.json()
                if data['mode'] != 'remote':
                    raise ValueError('Real evaluation refuses an offline service')
                found = list(dict.fromkeys(c['document_id'] for c in data['citations']))
                expected = set(case.get('expected_document_ids', []))
                recall = len(expected.intersection(found))/len(expected) if expected else None
                rank = next((i for i, doc in enumerate(found, 1) if doc in expected), None)
                mrr = (1/rank if rank else 0) if expected else None
                answer_ok = all(value.casefold() in data['answer'].casefold() for value in case.get('answer_contains', []))
                passed = (data['refused'] == case['expected_refused'] and answer_ok and (recall is None or recall == 1))
                rows.append({'case': number, 'passed': passed, 'recall_at_k': recall, 'reciprocal_rank': mrr,
                             'refusal_correct': data['refused'] == case['expected_refused'],
                             'answer_contains_passed': answer_ok, 'request_id': data['request_id'],
                             'latency_ms': round((time.monotonic()-start)*1000, 2)})
            except (httpx.HTTPError, KeyError, TypeError) as exc:
                rows.append({'case': number, 'passed': False, 'error': type(exc).__name__,
                             'latency_ms': round((time.monotonic()-start)*1000, 2)})
    rate = sum(row['passed'] for row in rows)/len(rows)
    recalls = [row['recall_at_k'] for row in rows if row.get('recall_at_k') is not None]
    ranks = [row['reciprocal_rank'] for row in rows if row.get('reciprocal_rank') is not None]
    report = {'passed': rate >= min_score and not any('error' in row for row in rows), 'pass_rate': rate,
              'min_score': min_score, 'mean_recall_at_k': sum(recalls)/len(recalls) if recalls else None,
              'mrr': sum(ranks)/len(ranks) if ranks else None, 'cases': rows,
              'scope': 'Live HTTP retrieval, refusal and literal answer checks; not a faithfulness judge'}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    return report
