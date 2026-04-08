import time
from threading import RLock
from typing import Any


class SimpleCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.store = {}
        self._lock = RLock()

    def get(self, key: str):
        with self._lock:
            entry = self.store.get(key)
        if not entry:
            return None

        value, expiry = entry
        if time.time() > expiry:
            with self._lock:
                self.store.pop(key, None)
            return None

        return value

    def set(self, key: str, value: Any):
        expiry = time.time() + self.ttl
        with self._lock:
            self.store[key] = (value, expiry)
