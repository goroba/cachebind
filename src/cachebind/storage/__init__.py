"""Storage.

Protocols do not require Redis. Importing a Redis storage class requires the ``redis`` extra.
"""

import importlib

from cachebind.storage.copyable import AsyncCopyableStorage, CopyableStorage
from cachebind.storage.droppable import AsyncDroppableStorage, DroppableStorage
from cachebind.storage.iterable import AsyncIterableStorage, IterableStorage
from cachebind.storage.leaseable import AsyncLeasableKeyValueStorage, LeasableKeyValueStorage
from cachebind.storage.key_value import AsyncKeyValueStorage, KeyValueStorage
from cachebind.storage.ordered_sets import AsyncOrderedSetStorage, OrderedSetStorage
from cachebind.storage.mergeable import AsyncMergeableStorage, MergeableStorage
from cachebind.storage.replaceable import AsyncReplaceableStorage, ReplaceableStorage
from cachebind.storage.sets import AsyncSetStorage, SetStorage
from cachebind.storage.snapshotable import AsyncSnapshotableStorage, SnapshotableStorage
from cachebind.storage.tries import AsyncTrieStorage, TrieStorage

__all__ = [
    "AsyncCopyableStorage",
    "AsyncDroppableStorage",
    "AsyncIterableStorage",
    "AsyncKeyValueStorage",
    "AsyncLeasableKeyValueStorage",
    "AsyncOrderedSetStorage",
    "AsyncMergeableStorage",
    "AsyncReplaceableStorage",
    "AsyncRedisHashStorage",
    "AsyncRedisOrderedSetStorage",
    "AsyncRedisSetStorage",
    "AsyncRedisStringStorage",
    "AsyncRedisTrieStorage",
    "AsyncSetStorage",
    "AsyncSnapshotableStorage",
    "AsyncTrieStorage",
    "CopyableStorage",
    "DroppableStorage",
    "IterableStorage",
    "KeyValueStorage",
    "LeasableKeyValueStorage",
    "OrderedSetStorage",
    "MergeableStorage",
    "ReplaceableStorage",
    "RedisHashStorage",
    "RedisOrderedSetStorage",
    "RedisSetStorage",
    "RedisStringStorage",
    "RedisTrieStorage",
    "SetStorage",
    "SnapshotableStorage",
    "TrieStorage",
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
_TRIES = {
    "AsyncRedisTrieStorage",
    "RedisTrieStorage",
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
    if name in _TRIES:
        module = importlib.import_module("cachebind.storage.tries")
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
