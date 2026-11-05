"""Environment-only configuration; no secrets committed to the project."""
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path

@dataclass(frozen=True)
class Principal:
    tenant: str
    role: str
    key_id: str

@dataclass
class Config:
    db: Path = field(default_factory=lambda: Path(os.getenv('KB_DB', 'data/knowledge.db')))
    keys: dict = field(default_factory=dict)
    mode: str = 'offline'
    api_base: str = ''
    api_key: str = ''
    embedding_model: str = ''
    chat_model: str = ''
    embedding_base: str = ''
    embedding_key: str = ''
    batch_size: int = 16
    dimension: int = 256
    rate_limit: int = 120
    max_chunks: int = 5000
    timeout: float = 25.0
    max_pending_jobs: int = 100
    job_max_attempts: int = 3
    job_lease_seconds: int = 300

    @classmethod
    def from_env(cls):
        return cls(keys=json.loads(os.getenv('KB_KEYS_JSON', '{}')),
                   mode=os.getenv('KB_MODE', 'remote'),
                   api_base=os.getenv('KB_MODEL_BASE', ''),
                   api_key=os.getenv('KB_MODEL_KEY', ''),
                   embedding_model=os.getenv('KB_EMBEDDING_MODEL', ''),
                   chat_model=os.getenv('KB_CHAT_MODEL', ''),
                   embedding_base=os.getenv('KB_EMBEDDING_BASE', ''),
                   embedding_key=os.getenv('KB_EMBEDDING_KEY', ''),
                   batch_size=int(os.getenv('KB_EMBEDDING_BATCH_SIZE', '16')),
                   dimension=int(os.getenv('KB_EMBEDDING_DIM', '256')),
                   rate_limit=int(os.getenv('KB_RATE_LIMIT', '120')),
                   max_chunks=int(os.getenv('KB_MAX_CHUNKS', '5000')),
                   timeout=float(os.getenv('KB_MODEL_TIMEOUT', '25')),
                   max_pending_jobs=int(os.getenv('KB_MAX_PENDING_JOBS', '100')),
                   job_max_attempts=int(os.getenv('KB_JOB_MAX_ATTEMPTS', '3')),
                   job_lease_seconds=int(os.getenv('KB_JOB_LEASE_SECONDS', '300')))

    def validate(self):
        if self.mode not in ('offline', 'remote'):
            raise ValueError('KB_MODE must be offline or remote')
        if not self.keys:
            raise ValueError('KB_KEYS_JSON must contain at least one API key')
        for secret, value in self.keys.items():
            if len(secret) < 24 or not isinstance(value, dict):
                raise ValueError('Each API key must be at least 24 characters')
            if value.get('role') not in ('reader', 'writer', 'admin'):
                raise ValueError('Invalid role')
            if not value.get('tenant') or len(value['tenant']) > 100:
                raise ValueError('Invalid tenant')
        if not 32 <= self.dimension <= 8192 or self.rate_limit < 1:
            raise ValueError('Invalid dimension or rate limit')
        import math
        if not math.isfinite(self.timeout) or self.timeout <= 0 or self.max_chunks < 1 or self.max_pending_jobs < 1 or self.job_max_attempts < 1 or self.job_lease_seconds < 1:
            raise ValueError('Invalid capacity, timeout or job limits')
        if not 1 <= self.batch_size <= 128:
            raise ValueError('Embedding batch size must be between 1 and 128')
        if self.mode == 'remote':
            from urllib.parse import urlsplit
            for endpoint in (self.api_base, self.embedding_base or self.api_base):
                url = urlsplit(endpoint)
                if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
                    raise ValueError('Remote model endpoint must be an HTTPS URL without credentials/query/fragment')
            if not all((self.api_key, self.embedding_model, self.chat_model)):
                raise ValueError('Remote model configuration is incomplete')

    @property
    def contract(self):
        payload = [self.mode, self.embedding_base or self.api_base, self.embedding_model,
                   self.dimension, 'unicode-window-600-overlap-80-v1', 'hash-token-v1']
        return hashlib.sha256(json.dumps(payload).encode()).hexdigest()
