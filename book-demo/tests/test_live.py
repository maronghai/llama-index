"""Real socket/process checks and opt-in real-provider acceptance; no HTTP mocks."""
import json
import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_real_http_api_and_separate_worker_process():
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        key = secrets.token_urlsafe(32)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        env = {**os.environ, 'KB_MODE': 'offline', 'KB_DB': str(Path(temp)/'db'),
               'KB_KEYS_JSON': json.dumps({key: {'tenant': 'live', 'role': 'admin'}}),
               'KB_PORT': str(port), 'KB_BIND': '127.0.0.1', 'PYTHONDONTWRITEBYTECODE': '1'}
        log = Path(temp)/'server.log'
        with log.open('w', encoding='utf-8') as stream:
            process = subprocess.Popen([sys.executable, 'run.py', 'serve'], cwd=ROOT, env=env,
                                       stdout=stream, stderr=subprocess.STDOUT)
            try:
                with httpx.Client(base_url=f'http://127.0.0.1:{port}', timeout=15,
                                  headers={'Authorization': 'Bearer '+key}) as client:
                    deadline = time.monotonic()+40
                    while True:
                        try:
                            if client.get('/health/ready').status_code == 200:
                                break
                        except httpx.TransportError:
                            pass
                        if process.poll() is not None or time.monotonic() > deadline:
                            pytest.fail('Server failed to become ready')
                        time.sleep(0.15)
                    job = client.post('/v1/jobs/ingest', json={'idempotency_key': 'live-job',
                        'doc_id': 'travel', 'title': '差旅', 'text': '差旅报销上限600元。'} )
                    job.raise_for_status()
                    subprocess.run([sys.executable, 'run.py', 'worker', '--once'], cwd=ROOT,
                                   env=env, check=True, timeout=40, capture_output=True)
                    status = client.get('/v1/jobs/'+job.json()['id']).json()
                    assert status['status'] == 'succeeded'
                    response = client.post('/v1/query', json={'question': '差旅报销上限'} )
                    response.raise_for_status()
                    assert '600' in response.json()['answer']
                    assert response.json()['citations'][0]['document_id'] == 'travel'
                    client.request('DELETE', '/v1/documents/travel', json={'expected_version': 1}).raise_for_status()
                    assert client.post('/v1/query', json={'question': '差旅报销上限'}).json()['refused']
            finally:
                if os.name == 'nt':
                    # The Windows Python launcher may spawn the interpreter. Terminate
                    # this test's whole process tree before closing inherited log handles.
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                   capture_output=True, timeout=15, check=False)
                else:
                    process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)


@pytest.mark.skipif(os.getenv('KB_RUN_REAL_MODEL_TESTS') != '1', reason='Real provider explicitly opt-in; no synthetic fallback')
def test_actual_provider_persistence_generation_and_evaluation():
    from kb.config import Config, Principal
    from kb.models import Embeddings, embed_parts
    from kb.store import Store
    from kb.retrieval import query
    cfg = Config.from_env()
    cfg.validate()
    assert cfg.mode == 'remote'
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        cfg.db = Path(temp)/'remote.db'
        store = Store(cfg)
        embedding = Embeddings(cfg)
        p = Principal('real-acceptance', 'admin', 'integration')
        parts = ['本项目差旅报销上限为每晚600元。', '报销申请需要提交发票。']
        vectors = embed_parts(embedding, parts)
        assert len(vectors) == 2 and all(len(v) == cfg.dimension for _, v in vectors)
        store.upsert(p, 'travel', '差旅制度', '\n'.join(parts), 0, vectors, 'real-ingest')
        # Re-open the actual database before querying the actual provider.
        result = query(cfg, Store(cfg), embedding, p, '差旅报销每晚最高金额是多少？', 2, 'real-query')
        assert not result['refused'] and '600' in result['answer']
        assert any(c['document_id'] == 'travel' for c in result['citations'])
        assert store.delete(p, 'travel', 1, 'real-delete')
        assert query(cfg, store, embedding, p, '差旅报销上限', 2, 'real-refuse')['refused']


def test_production_default_and_no_offline_quality_claim():
    from kb.config import Config
    from kb.operations import evaluate
    # from_env uses production mode; explicit Config() remains the deterministic test fixture.
    env = {k: v for k,v in os.environ.items() if k != 'KB_MODE'}
    child = subprocess.run([sys.executable, '-c', 'from kb.config import Config; print(Config.from_env().mode)'],
                           cwd=ROOT, env=env, capture_output=True, text=True, timeout=20, check=True)
    assert child.stdout.strip() == 'remote'
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        path = Path(temp)/'cases.jsonl'
        path.write_text(json.dumps({'question': 'q', 'expected_refused': False}), encoding='utf-8')
        with pytest.raises(ValueError, match='expected_document_ids'):
            evaluate(path, Path(temp)/'report.json')
