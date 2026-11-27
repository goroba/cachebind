"""Build a registered ordered-set index from its parts and check that those parts agree."""

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
from cachebind.indexes.ordered_sets.async_index import AsyncOrderedSetIndex
from cachebind.indexes.ordered_sets.index import OrderedSetIndex
from cachebind.serializers.serializer import Serializer
from cachebind.tagging import Breadcrumbs, ColonBreadcrumbs, NoopBreadcrumbs
from cachebind.storage.ordered_sets.async_storage import AsyncOrderedSetStorage
from cachebind.storage.ordered_sets.storage import OrderedSetStorage


def build_ordered_set_index[
    ClientType,
    MemberType,
    StorageType: Hashable,
    Storage: OrderedSetStorage[ClientType, StorageType],
](
    key: str,
    *,
    member_type: type[MemberType],
    serializer: Serializer[MemberType, StorageType],
    storage: Storage,
    breadcrumbs: Breadcrumbs | None = None,
) -> OrderedSetIndex[ClientType, MemberType, StorageType]:
    """Register a sync ordered-set index whose member, serializer, and storage types agree.

    ``serializer`` and ``storage`` are instances. The returned index is registered
    and ready to use. Pass the storage client to each index method.
    """
    return cast(
        OrderedSetIndex[ClientType, MemberType, StorageType],
        _build(
            key,
            member_type=member_type,
            serializer=serializer,
            storage=storage,
            breadcrumbs=breadcrumbs,
            base=OrderedSetIndex,
            interface=OrderedSetStorage,
            other=AsyncOrderedSetStorage,
        ),
    )


def build_async_ordered_set_index[
    ClientType,
    MemberType,
    StorageType: Hashable,
    Storage: AsyncOrderedSetStorage[ClientType, StorageType],
](
    key: str,
    *,
    member_type: type[MemberType],
    serializer: Serializer[MemberType, StorageType],
    storage: Storage,
    breadcrumbs: Breadcrumbs | None = None,
) -> AsyncOrderedSetIndex[ClientType, MemberType, StorageType]:
    """Register an async ordered-set index whose member, serializer, and storage types agree.

    ``serializer`` and ``storage`` are instances. The returned index is registered
    and ready to use. Pass the storage client to each index method.
    """
    return cast(
        AsyncOrderedSetIndex[ClientType, MemberType, StorageType],
        _build(
            key,
            member_type=member_type,
            serializer=serializer,
            storage=storage,
            breadcrumbs=breadcrumbs,
            base=AsyncOrderedSetIndex,
            interface=AsyncOrderedSetStorage,
            other=OrderedSetStorage,
        ),
    )


def _build(
    key: str,
    *,
    member_type: Any,
    serializer: Any,
    storage: Any,
    breadcrumbs: Breadcrumbs | None,
    base: type[OrderedSetIndex[Any, Any, Any]] | type[AsyncOrderedSetIndex[Any, Any, Any]],
    interface: type[OrderedSetStorage[Any, Any]] | type[AsyncOrderedSetStorage[Any, Any]],
    other: type[OrderedSetStorage[Any, Any]] | type[AsyncOrderedSetStorage[Any, Any]],
) -> Any:
    check_key(key)
    instance_class(key, serializer, label="serializer")
    value_type, serializer_storage = serializer_types(key, serializer_class(serializer))
    check_value_type(key, member_type, value_type, label="member type")
    storage_cls = instance_class(key, storage, label="storage")
    storage_type = _storage_type(key, storage_cls, interface, other)
    check_storage_type(key, serializer_storage, storage_type, storage_cls)
    client_type = storage_client_type(key, storage_cls, interface)
    if breadcrumbs is None:
        breadcrumbs = ColonBreadcrumbs()
    else:
        instance_class(key, breadcrumbs, label="breadcrumbs")
    return index_class(
        key,
        serializer_instance=serializer,
        storage=storage,
        base=base,
        module=__name__,
        attributes={"member": member_type, "client_type": client_type, "breadcrumbs": breadcrumbs},
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
            if interface is OrderedSetStorage:
                raise TypeError(
                    f"index {key!r}: {storage.__name__} is asynchronous; "
                    "build_ordered_set_index requires OrderedSetStorage"
                )
            raise TypeError(
                f"index {key!r}: {storage.__name__} is synchronous; "
                "build_async_ordered_set_index requires AsyncOrderedSetStorage"
            )
        raise TypeError(
            f"index {key!r}: {storage.__name__} does not declare "
            f"{interface.__name__}[ClientType, MemberType]"
        )
    return args[1]
