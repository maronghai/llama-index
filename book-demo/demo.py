"""Deterministic acceptance demo; generated secrets and isolated temporary database."""
from pathlib import Path
from tempfile import TemporaryDirectory
import secrets
from fastapi.testclient import TestClient
from kb.api import create_app
from kb.config import Config


def exercise():
    a, b = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    with TemporaryDirectory(prefix='kb-demo-', dir=__import__('os').environ.get('FEIBO_TMP')) as temp:
        cfg = Config(db=Path(temp)/'demo.db', keys={a: {'tenant': 'alpha', 'role': 'admin'}, b: {'tenant': 'beta', 'role': 'admin'}})
        with TestClient(create_app(cfg)) as client:
            ha, hb = {'Authorization': 'Bearer '+a}, {'Authorization': 'Bearer '+b}
            ingest = client.put('/v1/documents/handbook', headers=ha, json={'title': '差旅制度', 'text': '差旅酒店报销上限为每晚600元。报销需要提供发票。'})
            assert ingest.status_code == 200, ingest.text
            client.put('/v1/documents/handbook', headers=hb, json={'title': '乙部门制度', 'text': '乙部门差旅酒店报销上限为每晚900元。'}) .raise_for_status()
            answer = client.post('/v1/query', headers=ha, json={'question': '差旅酒店报销上限是多少？'}).json()
            isolated = client.post('/v1/query', headers=hb, json={'question': '差旅酒店报销上限是多少？'}).json()
            refusal = client.post('/v1/query', headers=ha, json={'question': 'ZXQ_UNSEEN_99383'}).json()
            passed = ('600' in answer['answer'] and '900' not in answer['answer'] and
                      '900' in isolated['answer'] and refusal['refused'])
            assert passed
            return {'passed': passed, 'mode': 'offline-extractive', 'answer': answer,
                    'checks': ['evidence retrieval', 'tenant isolation', 'unknown-question refusal']}
