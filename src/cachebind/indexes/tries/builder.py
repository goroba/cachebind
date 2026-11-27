"""Build a registered trie index from its parts and check that those parts agree."""

from collections.abc import Hashable
from typing import Any, cast

from cachebind.indexes._builder import (
    check_key,
    check_storage_type,
    check_value_type,
    generic_args,
    index_class,
    instance_class,
    serializer_class,
    serializer_types,
    storage_client_type,
)
from cachebind.indexes.tries.async_index import AsyncTrieIndex
from cachebind.indexes.tries.index import TrieIndex
from cachebind.serializers.serializer import Serializer
from cachebind.tagging import NoopBreadcrumbs
from cachebind.storage.tries.async_storage import AsyncTrieStorage
from cachebind.storage.tries.storage import TrieStorage


def build_trie_index[
    ClientType,
    MemberType,
    StorageType: Hashable,
    Storage: TrieStorage[ClientType, StorageType],
](
    key: str,
    *,
    member_type: type[MemberType],
    serializer: Serializer[MemberType, StorageType],
    storage: Storage,
) -> TrieIndex[ClientType, MemberType, StorageType]:
    """Register a sync trie index whose member, serializer, and storage types agree.

    ``serializer`` and ``storage`` are instances. The returned index is registered
    and ready to use. Pass the storage client to each index method.
    """
    return cast(
        TrieIndex[ClientType, MemberType, StorageType],
        _build(
            key,
            member_type=member_type,
            serializer=serializer,
            storage=storage,
            base=TrieIndex,
            interface=TrieStorage,
            other=AsyncTrieStorage,
        ),
    )


def build_async_trie_index[
    ClientType,
    MemberType,
    StorageType: Hashable,
    Storage: AsyncTrieStorage[ClientType, StorageType],
](
    key: str,
    *,
    member_type: type[MemberType],
    serializer: Serializer[MemberType, StorageType],
    storage: Storage,
) -> AsyncTrieIndex[ClientType, MemberType, StorageType]:
    """Register an async trie index whose member, serializer, and storage types agree.

    ``serializer`` and ``storage`` are instances. The returned index is registered
    and ready to use. Pass the storage client to each index method.
    """
    return cast(
        AsyncTrieIndex[ClientType, MemberType, StorageType],
        _build(
            key,
            member_type=member_type,
            serializer=serializer,
            storage=storage,
            base=AsyncTrieIndex,
            interface=AsyncTrieStorage,
            other=TrieStorage,
        ),
    )


def _build(
    key: str,
    *,
    member_type: Any,
    serializer: Any,
    storage: Any,
    base: type[TrieIndex[Any, Any, Any]] | type[AsyncTrieIndex[Any, Any, Any]],
    interface: type[TrieStorage[Any, Any]] | type[AsyncTrieStorage[Any, Any]],
    other: type[TrieStorage[Any, Any]] | type[AsyncTrieStorage[Any, Any]],
) -> Any:
    check_key(key)
    instance_class(key, serializer, label="serializer")
    value_type, serializer_storage = serializer_types(key, serializer_class(serializer))
    check_value_type(key, member_type, value_type, label="member type")
    storage_cls = instance_class(key, storage, label="storage")
    storage_type = _storage_type(key, storage_cls, interface, other)
    check_storage_type(key, serializer_storage, storage_type, storage_cls)
    client_type = storage_client_type(key, storage_cls, interface)
    return index_class(
        key,
        serializer_instance=serializer,
        storage=storage,
        base=base,
        module=__name__,
        attributes={
            "member": member_type,
            "client_type": client_type,
            "breadcrumbs": NoopBreadcrumbs(),
        },
    )


def _storage_type(
    key: str,
    storage: type,
    interface: type,
    other: type,
) -> Any:
    args = generic_args(storage, interface)
    if args is None or len(args) != 2:
        if generic_args(storage, other) is not None:
            if interface is TrieStorage:
                raise TypeError(
                    f"index {key!r}: {storage.__name__} is asynchronous; "
                    "build_trie_index requires TrieStorage"
                )
            raise TypeError(
                f"index {key!r}: {storage.__name__} is synchronous; "
                "build_async_trie_index requires AsyncTrieStorage"
            )
        raise TypeError(
            f"index {key!r}: {storage.__name__} does not declare "
            f"{interface.__name__}[ClientType, PayloadType]"
        )
    return args[1]
