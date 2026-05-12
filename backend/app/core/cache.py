"""Simple in-process LRU cache for workflow results.

Keyed by a stable hash of the request payload. Bounded by RESULT_CACHE_SIZE
in settings; oldest entries are evicted when full. In-memory only — restarts
lose the cache.
"""

from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from threading import Lock
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class LRUCache(Generic[T]):
    def __init__(self, max_size: int) -> None:
        self._max = max_size
        self._data: OrderedDict[str, T] = OrderedDict()
        self._lock = Lock()

    def get(self, key: str) -> T | None:
        with self._lock:
            if key not in self._data:
                return None
            self._data.move_to_end(key)
            return self._data[key]

    def put(self, key: str, value: T) -> None:
        with self._lock:
            self._data[key] = value
            self._data.move_to_end(key)
            while len(self._data) > self._max:
                self._data.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


def hash_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
