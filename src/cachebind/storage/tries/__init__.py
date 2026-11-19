"""Trie storage.

``TrieStorage`` and ``AsyncTrieStorage`` do not require Redis.
Importing a Redis storage class requires the ``redis`` extra.
"""

from cachebind.storage.tries.async_storage import AsyncTrieStorage
from cachebind.storage.tries.storage import TrieStorage

__all__ = [
    "AsyncRedisTrieStorage",
    "AsyncTrieStorage",
    "RedisTrieStorage",
    "TrieStorage",
]


def __getattr__(name: str) -> type:
    if name == "AsyncRedisTrieStorage":
        from cachebind.storage.tries.async_redis_trie_storage import AsyncRedisTrieStorage

        return AsyncRedisTrieStorage
    if name == "RedisTrieStorage":
        from cachebind.storage.tries.redis_trie_storage import RedisTrieStorage

        return RedisTrieStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
