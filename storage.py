from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import redis


class StorageError(RuntimeError):
    pass


class BaseStore:
    def get(self, key: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        raise NotImplementedError


@dataclass
class MemoryStore(BaseStore):
    data: dict[str, dict[str, Any]] = field(default_factory=dict)

    def get(self, key: str) -> dict[str, Any] | None:
        return self.data.get(key)

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        self.data[key] = value


class RedisStore(BaseStore):
    def __init__(self, host: str, port: int) -> None:
        self.client = redis.Redis(host=host, port=port, decode_responses=True)
        try:
            self.client.ping()
        except redis.RedisError as exc:
            raise StorageError(f"Redis is not reachable at {host}:{port}") from exc

    def get(self, key: str) -> dict[str, Any] | None:
        raw = self.client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        self.client.set(key, json.dumps(value), ex=ttl_seconds)
