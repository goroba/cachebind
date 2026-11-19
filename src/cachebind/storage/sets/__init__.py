"""Set storage.

``SetStorage`` and ``AsyncSetStorage`` do not require Redis.
Importing a Redis storage class requires the ``redis`` extra.
"""

from cachebind.storage.sets.async_storage import AsyncSetStorage
from cachebind.storage.sets.storage import SetStorage

__all__ = [
    "AsyncRedisSetStorage",
    "AsyncSetStorage",
    "RedisSetStorage",
    "SetStorage",
]


def __getattr__(name: str) -> type:
    if name == "AsyncRedisSetStorage":
        from cachebind.storage.sets.async_redis_set_storage import AsyncRedisSetStorage

        return AsyncRedisSetStorage
    if name == "RedisSetStorage":
        from cachebind.storage.sets.redis_set_storage import RedisSetStorage

        return RedisSetStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
