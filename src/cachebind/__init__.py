"""Cachebind."""

from importlib.metadata import PackageNotFoundError, version

from cachebind.indexes import (
    AsyncKeyValueIndex,
    AsyncOrderedSetIndex,
    AsyncSetIndex,
    Index,
    IndexRegistry,
    KeyValueBase,
    KeyValueIndex,
    OrderedSetBase,
    OrderedSetIndex,
    SetBase,
    SetIndex,
    build_async_key_value_index,
    build_async_ordered_set_index,
    build_async_set_index,
    build_key_value_index,
    build_ordered_set_index,
    build_set_index,
    get_registry,
)
from cachebind.serializers import (
    BoolSerializer,
    DataclassSerializer,
    DatetimeSerializer,
    DictSerializer,
    FloatSerializer,
    IntSerializer,
    Serializer,
    StrSerializer,
)
from cachebind.storage import (
    AsyncKeyValueStorage,
    AsyncOrderedSetStorage,
    AsyncSetStorage,
    KeyValueStorage,
    OrderedSetStorage,
    SetStorage,
)

try:
    __version__ = version("cachebind")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "AsyncKeyValueIndex",
    "AsyncKeyValueStorage",
    "AsyncOrderedSetIndex",
    "AsyncOrderedSetStorage",
    "AsyncSetIndex",
    "AsyncSetStorage",
    "BoolSerializer",
    "DataclassSerializer",
    "DatetimeSerializer",
    "DictSerializer",
    "FloatSerializer",
    "Index",
    "IndexRegistry",
    "IntSerializer",
    "KeyValueBase",
    "KeyValueIndex",
    "KeyValueStorage",
    "OrderedSetBase",
    "OrderedSetIndex",
    "OrderedSetStorage",
    "Serializer",
    "SetBase",
    "SetIndex",
    "SetStorage",
    "StrSerializer",
    "__version__",
    "build_async_key_value_index",
    "build_async_ordered_set_index",
    "build_async_set_index",
    "build_key_value_index",
    "build_ordered_set_index",
    "build_set_index",
    "get_registry",
]
