"""Authoritative worker process executing async ingestion jobs."""
import json
import logging
import signal
import time
from .config import Principal
from .models import Embeddings, ModelFailure, embed_parts
from .retrieval import chunk
from .store import Conflict, Capacity

log = logging.getLogger('kb.worker')


def _execute_step(config, store, embeddings, job):
    p = Principal(job['tenant'], 'writer', job['actor'])
    try:
        data = json.loads(job['payload'])
    except Exception as e:
        store.fail_job(job, False, 'Corrupted payload')
        return
    parts = chunk(data['text'])
    try:
        vectors = embed_parts(embeddings, parts)
    except ModelFailure as e:
        store.fail_job(job, True, 'model_failure')
        return
    except Exception as e:
        store.fail_job(job, False, 'embedding_computation_error')
        return
    try:
        store.upsert(p, data['doc_id'], data['title'], data['text'],
                     data['expected_version'], vectors, 'job:'+job['id'], job=(job['id'], job['token']))
    except (Conflict, Capacity) as e:
        store.fail_job(job, False, str(e))
    except Exception as e:
        store.fail_job(job, True, 'storage_transaction_failed')


def execute_step(config, store, embeddings, job):
    import threading
    stopped = threading.Event()

    def heartbeat():
        while not stopped.wait(max(0.1, config.job_lease_seconds / 3)):
            try:
                if not store.renew_job(job):
                    return
            except Exception:
                log.warning('Job heartbeat failed: %s', job['id'])
                return

    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    try:
        _execute_step(config, store, embeddings, job)
    finally:
        stopped.set()
        thread.join(timeout=12)


def run_worker(config, store=None, embeddings=None, poll=1.0, once=False):
    from .store import Store
    store = store or Store(config)
    embeddings = embeddings or Embeddings(config)
    stop = False

    def handle(sig, frame):
        nonlocal stop
        stop = True

    try:
        signal.signal(signal.SIGINT, handle)
        signal.signal(signal.SIGTERM, handle)
    except (ValueError, AttributeError):
        pass

    while not stop:
        job = store.claim_job()
        if job:
            execute_step(config, store, embeddings, job)
            if once:
                break
        else:
            if once:
                break
            time.sleep(poll)
