"""Ordered-set storage.

``OrderedSetStorage`` and ``AsyncOrderedSetStorage`` do not require Redis.
Importing a Redis storage class requires the ``redis`` extra.
"""

from cacher.storage.ordered_sets.async_storage import AsyncOrderedSetStorage
from cacher.storage.ordered_sets.storage import OrderedSetStorage

__all__ = [
    "AsyncOrderedSetStorage",
    "AsyncRedisOrderedSetStorage",
    "OrderedSetStorage",
    "RedisOrderedSetStorage",
]


def __getattr__(name: str) -> type:
    if name == "AsyncRedisOrderedSetStorage":
        from cacher.storage.ordered_sets.async_redis_ordered_set_storage import (
            AsyncRedisOrderedSetStorage,
        )

        return AsyncRedisOrderedSetStorage
    if name == "RedisOrderedSetStorage":
        from cacher.storage.ordered_sets.redis_ordered_set_storage import RedisOrderedSetStorage

        return RedisOrderedSetStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
