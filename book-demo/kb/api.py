import hashlib
import hmac
import json
import logging
import time
from uuid import uuid4
from fastapi import FastAPI, Depends, Request, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from .config import Config, Principal
from .models import Embeddings, ModelFailure, embed_parts
from .store import Store, Conflict, Capacity, Limited
from .retrieval import chunk, query

log = logging.getLogger('kb.access')

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class DocumentInput(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=200000)
    expected_version: int = Field(default=0, ge=0)

class QueryInput(StrictModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=4, ge=1, le=10)

class DeleteInput(StrictModel):
    expected_version: int = Field(ge=1)


class JobSubmitInput(StrictModel):
    idempotency_key: str = Field(min_length=1, max_length=128)
    doc_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=200000)
    expected_version: int = Field(default=0, ge=0)


def create_app(config=None):
    config = config or Config.from_env()
    config.validate()
    store = Store(config)
    embeddings = Embeddings(config)
    app = FastAPI(title='LlamaIndex Enterprise Knowledge Base', version='1.0.0',
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.state.store = store

    @app.middleware('http')
    async def request_context(request, call_next):
        request.state.request_id = uuid4().hex
        start = time.monotonic()
        # Limit body bytes before JSON parsing, including chunked uploads.
        if request.method in ('PUT', 'POST', 'DELETE'):
            body = bytearray()
            async for part in request.stream():
                body.extend(part)
                if len(body) > 900000:
                    return JSONResponse({'detail': 'Request too large'}, status_code=413, headers={'X-Request-ID': request.state.request_id, 'Cache-Control': 'no-store'})
            request._body = bytes(body)
        try:
            response = await call_next(request)
        except Exception:
            log.error(json.dumps({'event': 'request_failed', 'request_id': request.state.request_id}))
            response = JSONResponse({'detail': 'Internal service error'}, status_code=500)
        response.headers['X-Request-ID'] = request.state.request_id
        response.headers['Cache-Control'] = 'no-store'
        log.info(json.dumps({'request_id': request.state.request_id, 'method': request.method,
                             'status': response.status_code, 'duration_ms': round((time.monotonic()-start)*1000, 2)}))
        return response

    def identity(request: Request):
        header = request.headers.get('authorization', '')
        secret = header[7:] if header.startswith('Bearer ') else ''
        value = None
        for key, mapped in config.keys.items():
            if hmac.compare_digest(secret.encode(), key.encode()):
                value = mapped
        if not value:
            raise HTTPException(401, 'Invalid credentials', headers={'WWW-Authenticate': 'Bearer'})
        p = Principal(value['tenant'], value['role'], hashlib.sha256(secret.encode()).hexdigest()[:16])
        try:
            store.limit(p)
        except Limited:
            raise HTTPException(429, 'Rate limit exceeded', headers={'Retry-After': '60'})
        return p

    def writer(p=Depends(identity)):
        if p.role not in ('writer', 'admin'):
            raise HTTPException(403, 'Write permission required')
        return p

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        return JSONResponse({'detail': str(exc)}, status_code=409)

    @app.exception_handler(Capacity)
    async def capacity(request, exc):
        return JSONResponse({'detail': str(exc)}, status_code=413)

    @app.exception_handler(ModelFailure)
    async def provider_failure(request, exc):
        return JSONResponse({'detail': 'Model provider unavailable'}, status_code=503)

    @app.get('/health/live')
    def live():
        return {'status': 'ok'}

    @app.get('/health/ready')
    def ready():
        with store.connect() as db:
            db.execute('SELECT 1').fetchone()
        return {'status': 'ok', 'mode': config.mode}


    @app.get('/v1/documents')
    def documents(limit: int = 100, after: str = '', p=Depends(identity)):
        if limit < 1 or limit > 500:
            raise HTTPException(422, 'limit must be between 1 and 500')
        docs = store.list_docs(p, limit=limit, after=after)
        next_after = docs[-1]['id'] if len(docs) == limit else None
        return {'documents': docs, 'next_after': next_after}

    @app.get('/v1/documents/{doc_id}')
    def document(doc_id: str, p=Depends(identity)):
        doc = store.get_doc(p, doc_id)
        if not doc:
            raise HTTPException(404, 'Document not found')
        return doc

    @app.post('/v1/jobs/ingest')
    def submit_ingest_job(body: JobSubmitInput, request: Request, p=Depends(writer)):
        if not body.doc_id.strip() or not body.text.strip():
            raise HTTPException(422, 'Invalid document ID or blank text')
        payload = {
            'doc_id': body.doc_id,
            'title': body.title,
            'text': body.text,
            'expected_version': body.expected_version,
        }
        job = store.submit_job(p, body.idempotency_key, payload, request.state.request_id)
        return JSONResponse(job, status_code=202)

    @app.get('/v1/jobs/{job_id}')
    def get_job(job_id: str, p=Depends(identity)):
        job = store.get_job(p, job_id)
        if not job:
            raise HTTPException(404, 'Job not found')
        return job

    @app.post('/v1/jobs/{job_id}/cancel')
    def cancel_job(job_id: str, request: Request, p=Depends(writer)):
        res = store.cancel_job(p, job_id, request.state.request_id)
        if not res:
            raise HTTPException(404, 'Job not found')
        return res

    @app.get('/v1/metrics')
    def metrics(p=Depends(identity)):
        if p.role != 'admin':
            raise HTTPException(403, 'Administrator permission required')
        return store.metrics(p)


    @app.put('/v1/documents/{doc_id}')
    def ingest(doc_id: str, body: DocumentInput, request: Request, p=Depends(writer)):
        if len(doc_id) > 128 or not doc_id.strip() or not body.text.strip():
            raise HTTPException(422, 'Invalid document ID or blank text')
        parts = chunk(body.text)
        vectors = embed_parts(embeddings, parts)
        return store.upsert(p, doc_id, body.title, body.text, body.expected_version, vectors, request.state.request_id)

    @app.delete('/v1/documents/{doc_id}')
    def delete(doc_id: str, body: DeleteInput, request: Request, p=Depends(writer)):
        if not store.delete(p, doc_id, body.expected_version, request.state.request_id):
            raise HTTPException(404, 'Document not found')
        return {'deleted': True}

    @app.post('/v1/query')
    def ask(body: QueryInput, request: Request, p=Depends(identity)):
        if not body.question.strip():
            raise HTTPException(422, 'Question cannot be blank')
        return query(config, store, embeddings, p, body.question, body.top_k, request.state.request_id)

    @app.get('/v1/audit')
    def audit(limit: int = Query(100, ge=1, le=500), before: int = Query(9223372036854775807, ge=1), p=Depends(identity)):
        if p.role != 'admin':
            raise HTTPException(403, 'Administrator permission required')
        events = store.audit(p, limit, before)
        return {'events': events, 'next_before': events[-1]['id'] if len(events) == limit else None}

    return app
