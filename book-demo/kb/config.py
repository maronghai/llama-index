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
    dimension: int = 256
    rate_limit: int = 120
    max_chunks: int = 5000
    timeout: float = 25.0

    @classmethod
    def from_env(cls):
        return cls(keys=json.loads(os.getenv('KB_KEYS_JSON', '{}')),
                   mode=os.getenv('KB_MODE', 'offline'),
                   api_base=os.getenv('KB_MODEL_BASE', ''),
                   api_key=os.getenv('KB_MODEL_KEY', ''),
                   embedding_model=os.getenv('KB_EMBEDDING_MODEL', ''),
                   chat_model=os.getenv('KB_CHAT_MODEL', ''),
                   dimension=int(os.getenv('KB_EMBEDDING_DIM', '256')),
                   rate_limit=int(os.getenv('KB_RATE_LIMIT', '120')))

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
        if self.mode == 'remote':
            if not self.api_base.startswith('https://'):
                raise ValueError('Remote model endpoint must use HTTPS')
            if not all((self.api_key, self.embedding_model, self.chat_model)):
                raise ValueError('Remote model configuration is incomplete')

    @property
    def contract(self):
        payload = [self.mode, self.api_base, self.embedding_model,
                   self.dimension, 'unicode-window-600-overlap-80-v1', 'hash-token-v1']
        return hashlib.sha256(json.dumps(payload).encode()).hexdigest()
