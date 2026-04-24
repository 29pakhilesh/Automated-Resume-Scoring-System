"""Short-lived in-memory store for snippet PNGs (avoid huge base64 in JSON/localStorage)."""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass


@dataclass
class _Entry:
    png: bytes
    created_at: float


class SnippetBlobStore:
    def __init__(self, *, ttl_seconds: int = 20 * 60, max_items: int = 500) -> None:
        self._ttl = ttl_seconds
        self._max = max_items
        self._items: dict[str, _Entry] = {}
        self._lock = threading.Lock()

    def put(self, png: bytes) -> str:
        token = secrets.token_urlsafe(18)
        now = time.time()
        with self._lock:
            self._gc_locked(now)
            if len(self._items) >= self._max:
                # drop oldest few
                for k, _ in sorted(self._items.items(), key=lambda kv: kv[1].created_at)[:10]:
                    self._items.pop(k, None)
            self._items[token] = _Entry(png=png, created_at=now)
        return token

    def get(self, token: str) -> bytes | None:
        now = time.time()
        with self._lock:
            self._gc_locked(now)
            ent = self._items.get(token)
            return ent.png if ent else None

    def _gc_locked(self, now: float) -> None:
        expired = [k for k, v in self._items.items() if (now - v.created_at) > self._ttl]
        for k in expired:
            self._items.pop(k, None)


SNIPPET_STORE = SnippetBlobStore()
