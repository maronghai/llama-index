import os
from pathlib import Path
import secrets
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from kb.api import create_app
from kb.config import Config


def fixture():
    admin = secrets.token_urlsafe(32)
    writer = secrets.token_urlsafe(32)
    reader = secrets.token_urlsafe(32)
    tenant_b = secrets.token_urlsafe(32)
    keys = {
        admin: {'tenant': 'tenant_a', 'role': 'admin'},
        writer: {'tenant': 'tenant_a', 'role': 'writer'},
        reader: {'tenant': 'tenant_a', 'role': 'reader'},
        tenant_b: {'tenant': 'tenant_b', 'role': 'writer'},
    }
    return admin, writer, reader, tenant_b, keys


def test_tenant_isolation_and_evidence():
    admin, writer, reader, tenant_b, keys = fixture()
    with TemporaryDirectory(prefix='kb-test-', dir=os.environ.get('FEIBO_TMP')) as temp:
        cfg = Config(db=Path(temp)/'test.db', keys=keys)
        with TestClient(create_app(cfg)) as client:
            ha = {'Authorization': f'Bearer {writer}'}
            hb = {'Authorization': f'Bearer {tenant_b}'}
            hr = {'Authorization': f'Bearer {reader}'}

            # Ingest to tenant A
            r = client.put('/v1/documents/handbook', headers=ha, json={
                'title': '租户A制度', 'text': '租户A的出差每日餐补标准为120元。'
            })
            assert r.status_code == 200, r.text
            assert r.json()['version'] == 1

            # Ingest to tenant B with same doc_id
            r = client.put('/v1/documents/handbook', headers=hb, json={
                'title': '租户B制度', 'text': '租户B的出差每日餐补标准为260元。'
            })
            assert r.status_code == 200

            # Query tenant A
            qa = client.post('/v1/query', headers=hr, json={'question': '出差每日餐补标准是多少？'}).json()
            assert not qa['refused']
            assert '120' in qa['answer']
            assert '260' not in qa['answer']
            assert all(c['document_id'] == 'handbook' for c in qa['citations'])

            # Query tenant B
            qb = client.post('/v1/query', headers=hb, json={'question': '出差每日餐补标准是多少？'}).json()
            assert not qb['refused']
            assert '260' in qb['answer']
            assert '120' not in qb['answer']


def test_concurrency_conflict_and_deletion_propagation():
    admin, writer, reader, tenant_b, keys = fixture()
    with TemporaryDirectory(prefix='kb-test-', dir=os.environ.get('FEIBO_TMP')) as temp:
        cfg = Config(db=Path(temp)/'test.db', keys=keys)
        with TestClient(create_app(cfg)) as client:
            hw = {'Authorization': f'Bearer {writer}'}
            hr = {'Authorization': f'Bearer {reader}'}

            # First ingest: v1
            client.put('/v1/documents/policy', headers=hw, json={
                'title': '年假规定', 'text': '试用期员工享有年假3天。', 'expected_version': 0
            }).raise_for_status()

            # Second ingest: expects v1 -> succeeds to v2
            client.put('/v1/documents/policy', headers=hw, json={
                'title': '年假规定', 'text': '转正员工享有年假10天。', 'expected_version': 1
            }).raise_for_status()

            # Stale update: still expects v1 -> must fail with 409
            stale = client.put('/v1/documents/policy', headers=hw, json={
                'title': '年假规定', 'text': '并发冲突写入', 'expected_version': 1
            })
            assert stale.status_code == 409

            # Query reflects v2
            q = client.post('/v1/query', headers=hr, json={'question': '年假多少天？'}).json()
            assert '10' in q['answer']
            assert '3' not in q['answer']

            # Stale delete fails
            del_stale = client.request('DELETE', '/v1/documents/policy', headers=hw, json={'expected_version': 1})
            assert del_stale.status_code == 409

            # Correct delete succeeds
            del_ok = client.request('DELETE', '/v1/documents/policy', headers=hw, json={'expected_version': 2})
            assert del_ok.status_code == 200

            # Query immediately refuses after deletion
            after = client.post('/v1/query', headers=hr, json={'question': '年假多少天？'}).json()
            assert after['refused']
            assert len(after['citations']) == 0


def test_permission_boundaries_and_audit():
    admin, writer, reader, tenant_b, keys = fixture()
    with TemporaryDirectory(prefix='kb-test-', dir=os.environ.get('FEIBO_TMP')) as temp:
        cfg = Config(db=Path(temp)/'test.db', keys=keys)
        with TestClient(create_app(cfg)) as client:
            hw = {'Authorization': f'Bearer {writer}'}
            hr = {'Authorization': f'Bearer {reader}'}
            ha = {'Authorization': f'Bearer {admin}'}

            # Reader cannot write
            r = client.put('/v1/documents/secret', headers=hr, json={'title': 't', 'text': 'content'})
            assert r.status_code == 403

            # Reader cannot read audit log
            r = client.get('/v1/audit', headers=hr)
            assert r.status_code == 403

            # Writer can ingest
            client.put('/v1/documents/secret', headers=hw, json={'title': 't', 'text': 'content'}).raise_for_status()

            # Admin can inspect audit
            r = client.get('/v1/audit', headers=ha)
            assert r.status_code == 200
            actions = [ev['action'] for ev in r.json()['events']]
            assert 'ingest' in actions


def test_rate_limiting_and_persistence_recovery():
    admin, writer, reader, tenant_b, keys = fixture()
    with TemporaryDirectory(prefix='kb-test-', dir=os.environ.get('FEIBO_TMP')) as temp:
        db_path = Path(temp)/'persist.db'
        cfg = Config(db=db_path, keys=keys, rate_limit=3)

        # 1. Check rate limit
        with TestClient(create_app(cfg)) as client:
            ha = {'Authorization': f'Bearer {admin}'}
            client.put('/v1/documents/faq', headers=ha, json={'title': 'FAQ', 'text': 'FAQ内容'}).raise_for_status()
            client.get('/v1/documents', headers=ha).raise_for_status()
            client.get('/v1/documents', headers=ha).raise_for_status()
            # 4th request in the same minute window exceeds rate_limit=3
            limited = client.get('/v1/documents', headers=ha)
            assert limited.status_code == 429
            assert 'Retry-After' in limited.headers

        # 2. Restart app with fresh client pointing to the same SQLite DB (disaster recovery)
        cfg_recovered = Config(db=db_path, keys=keys, rate_limit=100)
        with TestClient(create_app(cfg_recovered)) as client_recovered:
            hr = {'Authorization': f'Bearer {reader}'}
            q = client_recovered.post('/v1/query', headers=hr, json={'question': 'FAQ内容'}).json()
            assert not q['refused']
            assert len(q['citations']) >= 1


def test_real_parallel_writers():
    from concurrent.futures import ThreadPoolExecutor
    _, writer, _, _, keys = fixture()
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        with TestClient(create_app(Config(db=Path(temp)/'db', keys=keys))) as client:
            headers = {'Authorization': 'Bearer '+writer}
            client.put('/v1/documents/parallel', headers=headers,
                       json={'title': 'policy', 'text': 'initial'}).raise_for_status()
            def update(number):
                return client.put('/v1/documents/parallel', headers=headers,
                                  json={'title': 'policy', 'text': f'value {number}', 'expected_version': 1}).status_code
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(update, [1, 2]))
            assert sorted(results) == [200, 409]


def test_input_limits_and_auth_fail_closed():
    _, writer, _, _, keys = fixture()
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        with TestClient(create_app(Config(db=Path(temp)/'db', keys=keys))) as client:
            headers = {'Authorization': 'Bearer '+writer}
            assert client.get('/v1/documents').status_code == 401
            assert client.get('/v1/documents', headers={'Authorization': 'Bearer wrong'}).status_code == 401
            assert client.post('/v1/query', headers=headers,
                               json={'question': 'policy', 'tenant': 'other'}).status_code == 422
            assert client.put('/v1/documents/blank', headers=headers,
                              json={'title': 't', 'text': '   '}).status_code == 422
            assert client.post('/v1/query', headers=headers, json={'question': ' '}).status_code == 422
            assert client.post('/v1/query', headers=headers, content=b'x'*900001).status_code == 413
            response = client.get('/health/ready')
            assert response.status_code == 200
            assert 'x-request-id' in response.headers


def test_atomic_capacity_and_idempotency():
    _, writer, _, _, keys = fixture()
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        with TestClient(create_app(Config(db=Path(temp)/'db', keys=keys, max_chunks=1))) as client:
            headers = {'Authorization': 'Bearer '+writer}
            data = {'title': 'policy', 'text': 'original policy'}
            client.put('/v1/documents/policy', headers=headers, json=data).raise_for_status()
            unchanged = client.put('/v1/documents/policy', headers=headers,
                                   json={**data, 'expected_version': 1})
            assert unchanged.json()['changed'] is False
            too_large = client.put('/v1/documents/policy', headers=headers,
                                   json={'title': 'policy', 'text': 'x'*1300, 'expected_version': 1})
            assert too_large.status_code == 413
            result = client.post('/v1/query', headers=headers, json={'question': 'original policy'}).json()
            assert 'original policy' in result['answer']
            assert result['citations'][0]['version'] == 1


def test_evidence_invalidated_during_generation():
    from unittest.mock import patch
    from kb.config import Principal
    _, writer, _, _, keys = fixture()
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        app = create_app(Config(db=Path(temp)/'db', keys=keys))
        with TestClient(app) as client:
            headers = {'Authorization': 'Bearer '+writer}
            client.put('/v1/documents/policy', headers=headers,
                       json={'title': 'policy', 'text': 'travel policy'}).raise_for_status()
            def concurrent_delete(config, question, citations):
                app.state.store.delete(Principal('tenant_a', 'writer', 'test'), 'policy', 1, 'parallel')
                return 'stale evidence', False
            with patch('kb.retrieval.answer', side_effect=concurrent_delete):
                result = client.post('/v1/query', headers=headers, json={'question': 'travel policy'})
            assert result.status_code == 409
            assert 'stale evidence' not in result.text


def test_remote_provider_contract_timeout_and_citations():
    import httpx
    import pytest
    from unittest.mock import patch
    from kb.models import Embeddings, answer, ModelFailure
    cfg = Config(mode='remote', api_base='https://model.invalid/v1', api_key='test-only',
                 embedding_model='embedding', chat_model='chat', dimension=32)
    citation = [{'text': 'travel policy'}]
    with patch('httpx.Client.post', side_effect=httpx.ReadTimeout('test')):
        with pytest.raises(ModelFailure):
            Embeddings(cfg).get_text_embedding('travel')
        with pytest.raises(ModelFailure):
            answer(cfg, 'travel', citation)
    bad_vector = httpx.Response(200, json={'data': [{'embedding': [0.1]}]},
                                request=httpx.Request('POST', cfg.api_base))
    with patch('httpx.Client.post', return_value=bad_vector):
        with pytest.raises(ModelFailure):
            Embeddings(cfg).get_text_embedding('travel')
    valid_vector = httpx.Response(200, json={'data': [{'embedding': [0.1]*32}]},
                                  request=httpx.Request('POST', cfg.api_base))
    with patch('httpx.Client.post', return_value=valid_vector):
        assert len(Embeddings(cfg).get_text_embedding('travel')) == 32
    for text, refused in [('unsupported [2]', True), ('no citation', True), ('travel [1]', False)]:
        response = httpx.Response(200, json={'choices': [{'message': {'content': text}}]},
                                  request=httpx.Request('POST', cfg.api_base))
        with patch('httpx.Client.post', return_value=response):
            assert answer(cfg, 'travel', citation)[1] == refused


def test_contract_and_backup_restore():
    import sqlite3
    import subprocess
    import sys
    import pytest
    _, writer, _, _, keys = fixture()
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        source, target = Path(temp)/'live.db', Path(temp)/'backup.db'
        cfg = Config(db=source, keys=keys)
        with TestClient(create_app(cfg)) as client:
            client.put('/v1/documents/backup', headers={'Authorization': 'Bearer '+writer},
                       json={'title': 'backup', 'text': 'persistent backup policy'}).raise_for_status()
            run_py = Path(__file__).resolve().parent.parent / 'run.py'
            subprocess.run([sys.executable, str(run_py), 'backup', '--output', str(target)],
                           env={**os.environ, 'KB_DB': str(source)}, check=True, timeout=20)
        from contextlib import closing
        with closing(sqlite3.connect(target)) as db:
            assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        with TestClient(create_app(Config(db=target, keys=keys))) as restored:
            result = restored.post('/v1/query', headers={'Authorization': 'Bearer '+writer},
                                   json={'question': 'backup policy'}).json()
            assert not result['refused']
        with pytest.raises(ValueError, match='contract'):
            create_app(Config(db=target, keys=keys, dimension=512))
