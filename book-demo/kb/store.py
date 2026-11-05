"""SQLite is the authoritative store. Every mutation and audit event is atomic."""
import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager
from uuid import uuid4

class Conflict(Exception):
    pass
class Capacity(Exception):
    pass
class Limited(Exception):
    pass

class Store:
    def __init__(self, config):
        self.config = config
        config.db.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS contract (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS documents (
                    tenant TEXT NOT NULL, id TEXT NOT NULL, title TEXT NOT NULL,
                    content TEXT NOT NULL, digest TEXT NOT NULL, version INTEGER NOT NULL,
                    updated REAL NOT NULL, PRIMARY KEY(tenant,id));
                CREATE TABLE IF NOT EXISTS chunks (
                    tenant TEXT NOT NULL, doc TEXT NOT NULL, id TEXT NOT NULL,
                    position INTEGER NOT NULL, text TEXT NOT NULL, vector TEXT NOT NULL,
                    PRIMARY KEY(tenant,id), FOREIGN KEY(tenant,doc) REFERENCES documents(tenant,id) ON DELETE CASCADE);
                CREATE INDEX IF NOT EXISTS ix_chunks_tenant_doc ON chunks(tenant,doc);
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY, time REAL NOT NULL, tenant TEXT NOT NULL,
                    actor TEXT NOT NULL, action TEXT NOT NULL, doc TEXT, request_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS limits (
                    key_id TEXT NOT NULL, window INTEGER NOT NULL, hits INTEGER NOT NULL,
                    PRIMARY KEY(key_id, window));
            ''')
            db.execute('INSERT OR IGNORE INTO contract VALUES(1,?)', (config.contract,))
            if db.execute('SELECT value FROM contract WHERE id=1').fetchone()[0] != config.contract:
                raise ValueError('Index contract changed; reingest into a new database before switching')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.config.db, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA busy_timeout=10000')
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def event(self, db, p, action, doc, request_id):
        db.execute('INSERT INTO audit(time,tenant,actor,action,doc,request_id) VALUES(?,?,?,?,?,?)',
                   (time.time(), p.tenant, p.key_id, action, doc, request_id))

    def limit(self, p):
        minute = int(time.time() // 60)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM limits WHERE window < ?', (minute - 2,))
            db.execute('INSERT INTO limits VALUES(?,?,1) ON CONFLICT(key_id,window) DO UPDATE SET hits=hits+1',
                       (p.key_id, minute))
            hits = db.execute('SELECT hits FROM limits WHERE key_id=? AND window=?', (p.key_id, minute)).fetchone()[0]
            if hits > self.config.rate_limit:
                raise Limited()

    def upsert(self, p, doc_id, title, content, expected, chunks, request_id):
        digest = hashlib.sha256((title+'\0'+content).encode()).hexdigest()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT version,digest FROM documents WHERE tenant=? AND id=?', (p.tenant, doc_id)).fetchone()
            old = row['version'] if row else 0
            if expected != old:
                raise Conflict('Document version changed')
            if row and row['digest'] == digest:
                self.event(db, p, 'ingest_unchanged', doc_id, request_id)
                return {'id': doc_id, 'version': old, 'changed': False}
            count = db.execute('SELECT count(*) FROM chunks WHERE tenant=? AND doc<>?', (p.tenant, doc_id)).fetchone()[0]
            if count + len(chunks) > self.config.max_chunks:
                raise Capacity('Tenant chunk limit exceeded')
            db.execute('''INSERT INTO documents VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(tenant,id) DO UPDATE SET title=excluded.title,content=excluded.content,
                digest=excluded.digest,version=excluded.version,updated=excluded.updated''',
                (p.tenant, doc_id, title, content, digest, old+1, time.time()))
            db.execute('DELETE FROM chunks WHERE tenant=? AND doc=?', (p.tenant, doc_id))
            for position, (text, vector) in enumerate(chunks):
                db.execute('INSERT INTO chunks VALUES(?,?,?,?,?,?)',
                           (p.tenant, doc_id, uuid4().hex, position, text, json.dumps(vector)))
            self.event(db, p, 'ingest', doc_id, request_id)
            return {'id': doc_id, 'version': old+1, 'changed': True, 'chunks': len(chunks)}

    def snapshot(self, p):
        with self.connect() as db:
            # One SELECT gives a consistent snapshot of text, vectors and document versions.
            return [dict(r) for r in db.execute('''SELECT c.*,d.title,d.version
                FROM chunks c JOIN documents d ON c.tenant=d.tenant AND c.doc=d.id
                WHERE c.tenant=? ORDER BY c.doc,c.position''', (p.tenant,))]

    def validate_evidence(self, p, citations, request_id):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            for c in citations:
                row = db.execute('SELECT version FROM documents WHERE tenant=? AND id=?', (p.tenant, c['document_id'])).fetchone()
                if not row or row[0] != c['version']:
                    raise Conflict('Evidence changed during query; retry with fresh data')
            self.event(db, p, 'query', None, request_id)

    def delete(self, p, doc_id, expected, request_id):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT version FROM documents WHERE tenant=? AND id=?', (p.tenant, doc_id)).fetchone()
            if not row:
                return False
            if row[0] != expected:
                raise Conflict('Document version changed')
            db.execute('DELETE FROM documents WHERE tenant=? AND id=?', (p.tenant, doc_id))
            self.event(db, p, 'delete', doc_id, request_id)
            return True

    def list_docs(self, p):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT id,title,version,updated FROM documents WHERE tenant=? ORDER BY id', (p.tenant,))]

    def audit(self, p):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT time,actor,action,doc,request_id FROM audit WHERE tenant=? ORDER BY id DESC LIMIT 100', (p.tenant,))]
