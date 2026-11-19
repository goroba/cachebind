"""Storage.

Protocols do not require Redis. Importing a Redis storage class requires the ``redis`` extra.
"""

import importlib

from cachebind.storage.key_value import AsyncKeyValueStorage, KeyValueStorage
from cachebind.storage.ordered_sets import AsyncOrderedSetStorage, OrderedSetStorage
from cachebind.storage.sets import AsyncSetStorage, SetStorage

__all__ = [
    "AsyncKeyValueStorage",
    "AsyncOrderedSetStorage",
    "AsyncRedisHashStorage",
    "AsyncRedisOrderedSetStorage",
    "AsyncRedisSetStorage",
    "AsyncRedisStringStorage",
    "AsyncSetStorage",
    "KeyValueStorage",
    "OrderedSetStorage",
    "RedisHashStorage",
    "RedisOrderedSetStorage",
    "RedisSetStorage",
    "RedisStringStorage",
    "SetStorage",
]

_KEY_VALUE = {
    "AsyncRedisHashStorage",
    "AsyncRedisStringStorage",
    "RedisHashStorage",
    "RedisStringStorage",
}
_SETS = {
    "AsyncRedisSetStorage",
    "RedisSetStorage",
}
_ORDERED_SETS = {
    "AsyncRedisOrderedSetStorage",
    "RedisOrderedSetStorage",
}


def __getattr__(name: str) -> type:
    if name in _KEY_VALUE:
        module = importlib.import_module("cachebind.storage.key_value")
        return getattr(module, name)
    if name in _SETS:
        module = importlib.import_module("cachebind.storage.sets")
        return getattr(module, name)
    if name in _ORDERED_SETS:
        module = importlib.import_module("cachebind.storage.ordered_sets")
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
