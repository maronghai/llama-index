"""Durable job lifecycle, fencing and API boundary regression tests."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from kb.api import create_app
from kb.config import Config, Principal
from kb.models import Embeddings, ModelFailure
from kb.store import Store, Conflict
from kb.worker import execute_step, run_worker
from .test_service import fixture


def setup(temp, **options):
    admin, writer, reader, other, keys = fixture()
    cfg = Config(db=Path(temp)/'db', keys=keys, **options)
    app = create_app(cfg)
    headers = lambda key: {'Authorization': 'Bearer '+key}
    return cfg, app, [headers(k) for k in (admin, writer, reader, other)]


def payload(**changes):
    return {'idempotency_key':'operation-1', 'doc_id':'policy', 'title':'Policy',
            'text':'出差酒店报销上限600元。', 'expected_version':0, **changes}


def test_async_idempotency_isolation_and_atomic_completion():
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        cfg, app, (ha, hw, hr, hb) = setup(temp)
        with TestClient(app) as c:
            response = c.post('/v1/jobs/ingest', headers=hw, json=payload())
            assert response.status_code == 202
            job_id = response.json()['id']
            assert c.get('/v1/documents', headers=hr).json()['documents'] == []
            assert c.post('/v1/jobs/ingest', headers=hw, json=payload()).json()['id'] == job_id
            assert c.post('/v1/jobs/ingest', headers=hw, json=payload(text='changed')).status_code == 409
            assert c.post('/v1/jobs/ingest', headers=hr, json=payload()).status_code == 403
            assert c.get('/v1/jobs/'+job_id, headers=hb).status_code == 404
            # Simulate restart: a new store/worker sees the durable queue.
            run_worker(cfg, once=True)
            result = c.get('/v1/jobs/'+job_id, headers=hr).json()
            assert result['status'] == 'succeeded' and result['result']['version'] == 1
            assert result['attempts'] == 1 and 'text' not in result
            assert c.post('/v1/jobs/ingest', headers=hw, json=payload()).json()['id'] == job_id
            assert c.get('/v1/documents/policy', headers=hr).json()['version'] == 1
            answer = c.post('/v1/query', headers=hr, json={'question':'出差酒店报销上限'}).json()
            assert '600' in answer['answer']
            metrics = c.get('/v1/metrics', headers=ha).json()
            assert metrics == {'documents':1, 'chunks':1, 'jobs':{'succeeded':1}}
            assert c.get('/v1/metrics', headers=hr).status_code == 403
            with app.state.store.connect() as db:
                assert db.execute('SELECT payload FROM jobs WHERE id=?',(job_id,)).fetchone()[0] == '{}'
                assert db.execute("SELECT count(*) FROM audit WHERE action='ingest'").fetchone()[0] == 1


def test_cancellation_fences_inflight_commit():
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        cfg, app, (_, hw, hr, hb) = setup(temp)
        with TestClient(app) as c:
            job_id=c.post('/v1/jobs/ingest', headers=hw, json=payload()).json()['id']
            job=app.state.store.claim_job()
            assert c.post('/v1/jobs/'+job_id+'/cancel', headers=hb).status_code == 404
            assert c.post('/v1/jobs/'+job_id+'/cancel', headers=hr).status_code == 403
            assert c.post('/v1/jobs/'+job_id+'/cancel', headers=hw).status_code == 200
            execute_step(cfg, app.state.store, Embeddings(cfg), job)
            assert c.get('/v1/jobs/'+job_id, headers=hw).json()['status'] == 'cancelled'
            assert c.get('/v1/documents/policy', headers=hw).status_code == 404


def test_lease_recovery_rejects_old_worker_and_claim_is_exclusive():
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        cfg, app, (_, hw, _, _) = setup(temp)
        with TestClient(app) as c:
            job_id=c.post('/v1/jobs/ingest', headers=hw, json=payload()).json()['id']
        store=app.state.store
        with ThreadPoolExecutor(max_workers=2) as pool:
            claims=list(pool.map(lambda _: store.claim_job(), range(2)))
        assert sum(j is not None for j in claims) == 1
        old=next(j for j in claims if j)
        with store.connect() as db:
            db.execute('UPDATE jobs SET lease_until=0 WHERE id=?',(job_id,))
        current=store.claim_job()
        assert current['attempts']==2 and current['token']!=old['token']
        assert not store.renew_job(old)
        execute_step(cfg,store,Embeddings(cfg),old)
        p=Principal('tenant_a','writer','test')
        assert store.get_doc(p,'policy') is None
        execute_step(cfg,store,Embeddings(cfg),current)
        assert store.get_job(p,job_id)['status']=='succeeded'


def test_retry_budget_and_permanent_conflict():
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        cfg, app, (_, hw, _, _) = setup(temp, job_max_attempts=2)
        with TestClient(app) as c:
            job_id=c.post('/v1/jobs/ingest', headers=hw, json=payload()).json()['id']
            store=app.state.store
            for attempt in (1,2):
                job=store.claim_job()
                with patch.object(Embeddings,'get_text_embedding',side_effect=ModelFailure('private provider message')):
                    execute_step(cfg,store,Embeddings(cfg),job)
                result=c.get('/v1/jobs/'+job_id,headers=hw).json()
                assert result['status']==('queued' if attempt==1 else 'failed')
                assert result['error']=='model_failure'
                with store.connect() as db:
                    db.execute('UPDATE jobs SET available=0 WHERE id=?',(job_id,))
            assert store.claim_job() is None
            assert c.get('/v1/documents/policy',headers=hw).status_code==404
            c.put('/v1/documents/policy',headers=hw,json={'title':'new','text':'new content'}).raise_for_status()
            stale=c.post('/v1/jobs/ingest',headers=hw,json=payload(idempotency_key='stale')).json()['id']
            run_worker(cfg, once=True)
            assert c.get('/v1/jobs/'+stale,headers=hw).json()['status']=='failed'
            assert c.get('/v1/documents/policy',headers=hw).json()['content']=='new content'


def test_crashed_last_attempt_becomes_terminal():
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        cfg, app, (_, hw, _, _) = setup(temp, job_max_attempts=1)
        with TestClient(app) as c:
            job_id=c.post('/v1/jobs/ingest',headers=hw,json=payload()).json()['id']
            store=app.state.store
            assert store.claim_job()
            with store.connect() as db:
                db.execute('UPDATE jobs SET lease_until=0')
            assert store.claim_job() is None
            result=c.get('/v1/jobs/'+job_id,headers=hw).json()
            assert result['status']=='failed' and result['error']=='attempt_limit'


def test_pending_quota_and_pagination_boundaries():
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        cfg, app, (ha, hw, _, hb) = setup(temp, max_pending_jobs=1)
        with TestClient(app) as c:
            c.post('/v1/jobs/ingest',headers=hw,json=payload()).raise_for_status()
            assert c.post('/v1/jobs/ingest',headers=hw,json=payload(idempotency_key='two')).status_code==413
            assert c.post('/v1/jobs/ingest',headers=hb,json=payload()).status_code==202
            for key in ('a','b','c'):
                c.put('/v1/documents/'+key,headers=hw,json={'title':key,'text':key}).raise_for_status()
            first=c.get('/v1/documents?limit=2',headers=hw).json()
            second=c.get('/v1/documents',params={'limit':2,'after':first['next_after']},headers=hw).json()
            assert [d['id'] for d in first['documents']+second['documents']]==['a','b','c']
            assert c.get('/v1/documents?limit=0',headers=hw).status_code==422
            assert c.get('/v1/documents/a',headers=hb).status_code==404
            first=c.get('/v1/audit?limit=2',headers=ha).json()
            second=c.get('/v1/audit',params={'limit':2,'before':first['next_before']},headers=ha).json()
            assert {e['id'] for e in first['events']}.isdisjoint(e['id'] for e in second['events'])


def test_delete_recreate_does_not_validate_old_citations():
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        cfg, app, (_, hw, _, _) = setup(temp)
        with TestClient(app) as c:
            c.put('/v1/documents/a',headers=hw,json={'title':'a','text':'old'}).raise_for_status()
            c.request('DELETE','/v1/documents/a',headers=hw,json={'expected_version':1}).raise_for_status()
            new=c.put('/v1/documents/a',headers=hw,json={'title':'a','text':'new'}).json()
            assert new['version']==2
            with pytest.raises(Conflict):
                app.state.store.validate_evidence(Principal('tenant_a','reader','x'),[{'document_id':'a','version':1}],'old-query')
            assert c.put('/v1/documents/a',headers=hw,json={'title':'a','text':'stale','expected_version':1}).status_code==409


def test_lease_heartbeat_renews_without_waiting():
    # Exercise heartbeat scheduling without time-dependent sleeps.
    with TemporaryDirectory(dir=os.environ.get('FEIBO_TMP')) as temp:
        cfg, app, (_, hw, _, _) = setup(temp)
        with TestClient(app) as c:
            c.post('/v1/jobs/ingest',headers=hw,json=payload()).raise_for_status()
        store=app.state.store
        job=store.claim_job()
        with store.connect() as db:
            db.execute('UPDATE jobs SET lease_until=lease_until-1 WHERE id=?',(job['id'],))
        assert store.renew_job(job)
        with store.connect() as db:
            lease=db.execute('SELECT lease_until FROM jobs').fetchone()[0]
        assert lease>=job['lease_until']
