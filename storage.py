from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

import redis


class StorageError(RuntimeError):
    pass


class LockError(RuntimeError):
    pass


class BaseStore:
    def get(self, key: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        raise NotImplementedError

    def ping(self) -> bool:
        raise NotImplementedError

    @contextmanager
    def lock(self, key: str, ttl_seconds: int = 10) -> Iterator[None]:
        raise NotImplementedError


@dataclass
class MemoryStore(BaseStore):
    data: dict[str, dict[str, Any]] = field(default_factory=dict)
    locks: set[str] = field(default_factory=set)

    def get(self, key: str) -> dict[str, Any] | None:
        return self.data.get(key)

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        self.data[key] = value

    def ping(self) -> bool:
        return True

    @contextmanager
    def lock(self, key: str, ttl_seconds: int = 10) -> Iterator[None]:
        lock_key = f"lock:{key}"

        if lock_key in self.locks:
            raise LockError("Session is locked, please retry.")

        self.locks.add(lock_key)
        try:
            yield
        finally:
            self.locks.discard(lock_key)


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

    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except redis.RedisError as exc:
            raise StorageError("Redis ping failed") from exc

    @contextmanager
    def lock(self, key: str, ttl_seconds: int = 10) -> Iterator[None]:
        lock_key = f"lock:{key}"
        token = f"{uuid.uuid4()}:{time.time()}"

        try:
            acquired = self.client.set(lock_key, token, ex=ttl_seconds, nx=True)
        except redis.RedisError as exc:
            raise StorageError("Could not acquire Redis lock") from exc

        if not acquired:
            raise LockError("Session is locked, please retry.")

        try:
            yield
        finally:
            try:
                current_token = self.client.get(lock_key)
                if current_token == token:
                    self.client.delete(lock_key)
            except redis.RedisError:
                pass
