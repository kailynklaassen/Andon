"""A small stale-while-revalidate cache for the backend.

Why it matters for speed: the gold queries behind every page are the same for every user and change only when the
pipeline runs. Each result is computed once per process; after `seconds` it is refreshed IN THE BACKGROUND while
callers keep getting the previous value — so after the first computation (warmed at startup), nobody waits on the
warehouse. That, more than the web framework, is what makes page switches instant. Thread-safe; one refresh per key.
"""
from __future__ import annotations

import functools
import threading
import time


_DATA_CACHES: list = []                                     # every cache of gold data, in definition order


def ttl_cache(seconds: int, data: bool = True):
    """data=False for caches that aren't gold data (e.g. the warehouse connection): refresh_all() leaves them alone."""
    def deco(fn):
        store: dict = {}                                   # key -> (computed_at, value)
        locks: dict = {}
        refreshing: set = set()
        guard = threading.Lock()

        def compute(key, args, kwargs):
            value = fn(*args, **kwargs)
            store[key] = (time.time(), value)
            return value

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            hit = store.get(key)
            if hit:
                if time.time() - hit[0] >= seconds:        # stale: serve it, refresh once in the background
                    with guard:
                        start = key not in refreshing
                        refreshing.add(key)
                    if start:
                        def refresh():
                            try:
                                compute(key, args, kwargs)
                            finally:
                                refreshing.discard(key)
                        threading.Thread(target=refresh, daemon=True).start()
                return hit[1]
            with guard:
                lock = locks.setdefault(key, threading.Lock())
            with lock:                                     # first call: concurrent callers wait for one computation
                hit = store.get(key)
                return hit[1] if hit else compute(key, args, kwargs)

        def recompute_all():
            for key in list(store):
                args, kwargs = key[0], dict(key[1])
                try:
                    compute(key, args, kwargs)
                except Exception as e:                     # keep serving the old value; the TTL retries later
                    print(f"cache refresh failed for {fn.__name__}: {e}")

        wrapper.cache_clear = store.clear
        wrapper.recompute_all = recompute_all
        if data:
            _DATA_CACHES.append(wrapper)
        return wrapper
    return deco


def refresh_all() -> None:
    """The gold data changed (an approved correction reached gold): recompute every cached entry now, in the
    background. Callers keep getting the previous values until each one is replaced, so nobody waits. Caches are
    refreshed in definition order — the raw gold queries (data.py) before the insights, scenes and pages built on
    them — so derived results are computed from the new data."""
    def run():
        for c in list(_DATA_CACHES):
            c.recompute_all()
        print(f"caches refreshed: {len(_DATA_CACHES)} functions")
    threading.Thread(target=run, daemon=True).start()
