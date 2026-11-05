import hashlib
import hmac
import json
import logging
import time
from uuid import uuid4
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from .config import Config, Principal
from .models import Embeddings, ModelFailure
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
                    return JSONResponse({'detail': 'Request too large'}, status_code=413)
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
    def documents(p=Depends(identity)):
        return {'documents': store.list_docs(p)}

    @app.put('/v1/documents/{doc_id}')
    def ingest(doc_id: str, body: DocumentInput, request: Request, p=Depends(writer)):
        if len(doc_id) > 128 or not doc_id.strip() or not body.text.strip():
            raise HTTPException(422, 'Invalid document ID or blank text')
        parts = chunk(body.text)
        vectors = [(part, embeddings.get_text_embedding(part)) for part in parts]
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
    def audit(p=Depends(identity)):
        if p.role != 'admin':
            raise HTTPException(403, 'Administrator permission required')
        return {'events': store.audit(p)}

    return app
