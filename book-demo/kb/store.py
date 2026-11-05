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
            db.executescript("""
                CREATE TABLE IF NOT EXISTS document_versions (
                    tenant TEXT NOT NULL, doc TEXT NOT NULL, version INTEGER NOT NULL,
                    PRIMARY KEY(tenant,doc));
                INSERT OR IGNORE INTO document_versions SELECT tenant,id,version FROM documents;
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, tenant TEXT NOT NULL, actor TEXT NOT NULL,
                    idem TEXT NOT NULL, digest TEXT NOT NULL, payload TEXT NOT NULL,
                    status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                    available REAL NOT NULL, lease_until REAL, token TEXT,
                    result TEXT, error TEXT, created REAL NOT NULL, updated REAL NOT NULL,
                    UNIQUE(tenant,actor,idem));
                CREATE INDEX IF NOT EXISTS ix_jobs_claim ON jobs(status,available,lease_until);
                PRAGMA user_version=2;
            """)
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

    def upsert(self, p, doc_id, title, content, expected, chunks, request_id, job=None):
        digest = hashlib.sha256((title+'\0'+content).encode()).hexdigest()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT version,digest FROM documents WHERE tenant=? AND id=?', (p.tenant, doc_id)).fetchone()
            if job:
                active = db.execute('SELECT status,token,lease_until FROM jobs WHERE id=?', (job[0],)).fetchone()
                if not active or active['status'] != 'running' or active['token'] != job[1] or active['lease_until'] <= time.time():
                    raise Conflict('Job lease lost')
            old = row['version'] if row else 0
            if expected != old:
                raise Conflict('Document version changed')
            if row and row['digest'] == digest:
                self.event(db, p, 'ingest_unchanged', doc_id, request_id)
                result = {'id': doc_id, 'version': old, 'changed': False}
                if job:
                    self.complete_job(db, job, result)
                return result
            count = db.execute('SELECT count(*) FROM chunks WHERE tenant=? AND doc<>?', (p.tenant, doc_id)).fetchone()[0]
            if count + len(chunks) > self.config.max_chunks:
                raise Capacity('Tenant chunk limit exceeded')
            previous = db.execute('SELECT version FROM document_versions WHERE tenant=? AND doc=?', (p.tenant, doc_id)).fetchone()
            version = max(old, previous[0] if previous else 0) + 1
            db.execute('INSERT INTO document_versions VALUES(?,?,?) ON CONFLICT(tenant,doc) DO UPDATE SET version=excluded.version', (p.tenant, doc_id, version))
            db.execute('''INSERT INTO documents VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(tenant,id) DO UPDATE SET title=excluded.title,content=excluded.content,
                digest=excluded.digest,version=excluded.version,updated=excluded.updated''',
                (p.tenant, doc_id, title, content, digest, version, time.time()))
            db.execute('DELETE FROM chunks WHERE tenant=? AND doc=?', (p.tenant, doc_id))
            for position, (text, vector) in enumerate(chunks):
                db.execute('INSERT INTO chunks VALUES(?,?,?,?,?,?)',
                           (p.tenant, doc_id, uuid4().hex, position, text, json.dumps(vector)))
            self.event(db, p, 'ingest', doc_id, request_id)
            result = {'id': doc_id, 'version': version, 'changed': True, 'chunks': len(chunks)}
            if job:
                self.complete_job(db, job, result)
            return result

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

    def list_docs(self, p, limit=100, after=""):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT id,title,version,updated FROM documents WHERE tenant=? AND id>? ORDER BY id LIMIT ?', (p.tenant, after, limit))]

    def audit(self, p, limit=100, before=9223372036854775807):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT id,time,actor,action,doc,request_id FROM audit WHERE tenant=? AND id<? ORDER BY id DESC LIMIT ?', (p.tenant,before,limit))]

    def get_doc(self, p, doc_id):
        with self.connect() as db:
            row = db.execute('SELECT id,title,content,version,updated FROM documents WHERE tenant=? AND id=?', (p.tenant, doc_id)).fetchone()
            return dict(row) if row else None

    def submit_job(self, p, idem, payload, request_id):
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        now = time.time()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM jobs WHERE tenant=? AND actor=? AND idem=?', (p.tenant, p.key_id, idem)).fetchone()
            if row:
                if row['digest'] != digest:
                    raise Conflict('Idempotency key reused with different input')
                return self.public_job(row)
            pending = db.execute("SELECT count(*) FROM jobs WHERE tenant=? AND status IN ('queued','running')", (p.tenant,)).fetchone()[0]
            if pending >= self.config.max_pending_jobs:
                raise Capacity('Tenant pending job limit exceeded')
            job_id = uuid4().hex
            db.execute("INSERT INTO jobs(id,tenant,actor,idem,digest,payload,status,available,created,updated) VALUES(?,?,?,?,?,?,'queued',?,?,?)",
                       (job_id,p.tenant,p.key_id,idem,digest,encoded,now,now,now))
            self.event(db,p,'job_submit',job_id,request_id)
            return self.public_job(db.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone())

    @staticmethod
    def public_job(row):
        return {k: (json.loads(row[k]) if k == 'result' and row[k] else row[k]) for k in
                ('id','status','attempts','result','error','created','updated')}

    def get_job(self, p, job_id):
        with self.connect() as db:
            row = db.execute('SELECT * FROM jobs WHERE tenant=? AND id=?',(p.tenant,job_id)).fetchone()
            return self.public_job(row) if row else None

    def cancel_job(self, p, job_id, request_id):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT status FROM jobs WHERE tenant=? AND id=?',(p.tenant,job_id)).fetchone()
            if not row:
                return None
            if row[0] not in ('queued','running','cancelled'):
                raise Conflict('Completed job cannot be cancelled')
            db.execute("UPDATE jobs SET status='cancelled',token=NULL,payload='{}',updated=? WHERE tenant=? AND id=?",(time.time(),p.tenant,job_id))
            self.event(db,p,'job_cancel',job_id,request_id)
            return {'id':job_id,'status':'cancelled'}

    def claim_job(self):
        now=time.time()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute("UPDATE jobs SET status='failed',error='attempt_limit',payload='{}',updated=? WHERE status='running' AND lease_until<=? AND attempts>=?",(now,now,self.config.job_max_attempts))
            row=db.execute("SELECT * FROM jobs WHERE (status='queued' AND available<=?) OR (status='running' AND lease_until<=? AND attempts<?) ORDER BY created,id LIMIT 1",(now,now,self.config.job_max_attempts)).fetchone()
            if not row:
                return None
            token=uuid4().hex
            db.execute("UPDATE jobs SET status='running',attempts=attempts+1,token=?,lease_until=?,updated=? WHERE id=?",(token,now+self.config.job_lease_seconds,now,row['id']))
            return dict(db.execute('SELECT * FROM jobs WHERE id=?',(row['id'],)).fetchone())

    def complete_job(self, db, job, result):
        db.execute("UPDATE jobs SET status='succeeded',result=?,error=NULL,payload='{}',token=NULL,updated=? WHERE id=? AND token=?",(json.dumps(result),time.time(),job[0],job[1]))

    def fail_job(self, job, retryable, error):
        now=time.time()
        retry=retryable and job['attempts'] < self.config.job_max_attempts
        with self.connect() as db:
            db.execute("UPDATE jobs SET status=?,error=?,available=?,token=NULL,payload=CASE WHEN ? THEN payload ELSE '{}' END,updated=? WHERE id=? AND token=? AND status='running'",
                       ('queued' if retry else 'failed',error,now+min(60,2**job['attempts']),retry,now,job['id'],job['token']))

    def metrics(self, p):
        with self.connect() as db:
            docs=db.execute('SELECT count(*) FROM documents WHERE tenant=?',(p.tenant,)).fetchone()[0]
            chunks=db.execute('SELECT count(*) FROM chunks WHERE tenant=?',(p.tenant,)).fetchone()[0]
            jobs={r[0]:r[1] for r in db.execute('SELECT status,count(*) FROM jobs WHERE tenant=? GROUP BY status',(p.tenant,))}
            return {'documents':docs,'chunks':chunks,'jobs':jobs}

    def renew_job(self, job):
        now = time.time()
        with self.connect() as db:
            result = db.execute("UPDATE jobs SET lease_until=?,updated=? WHERE id=? AND token=? AND status='running' AND lease_until>?",
                                (now+self.config.job_lease_seconds,now,job['id'],job['token'],now))
            return result.rowcount == 1
