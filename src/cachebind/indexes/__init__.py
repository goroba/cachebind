"""Indexes bind a value to storage and register that binding by key."""

from cachebind.indexes.base import Index, get_registry
from cachebind.indexes.key_value import (
    AsyncKeyValueIndex,
    KeyValueBase,
    KeyValueIndex,
    build_async_key_value_index,
    build_key_value_index,
)
from cachebind.indexes.ordered_sets import (
    AsyncOrderedSetIndex,
    OrderedSetBase,
    OrderedSetIndex,
    build_async_ordered_set_index,
    build_ordered_set_index,
)
from cachebind.indexes.registry import IndexRegistry
from cachebind.indexes.sets import (
    AsyncSetIndex,
    SetBase,
    SetIndex,
    build_async_set_index,
    build_set_index,
)
from cachebind.indexes.tries import (
    AsyncTrieIndex,
    TrieBase,
    TrieIndex,
    build_async_trie_index,
    build_trie_index,
)

__all__ = [
    "AsyncKeyValueIndex",
    "AsyncOrderedSetIndex",
    "AsyncSetIndex",
    "AsyncTrieIndex",
    "Index",
    "IndexRegistry",
    "KeyValueBase",
    "KeyValueIndex",
    "OrderedSetBase",
    "OrderedSetIndex",
    "SetBase",
    "SetIndex",
    "TrieBase",
    "TrieIndex",
    "build_async_key_value_index",
    "build_async_ordered_set_index",
    "build_async_set_index",
    "build_async_trie_index",
    "build_key_value_index",
    "build_ordered_set_index",
    "build_set_index",
    "build_trie_index",
    "get_registry",
]
