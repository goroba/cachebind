"""Fill-lease helpers for leasable key-value indexes."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING

from cachebind.indexes._serializer import resolve_serializer
from cachebind.storage.leaseable import AsyncLeasableKeyValueStorage, LeasableKeyValueStorage

if TYPE_CHECKING:
    from cachebind.indexes.key_value.base import KeyValueBase


def _assert_leasable_sync(index: KeyValueBase[object, object, object, object]) -> None:
    if not isinstance(index.storage, LeasableKeyValueStorage):
        raise NotImplementedError(
            f"{type(index.storage).__name__} cannot lease-get a single-field index"
        )


def _assert_leasable_async(index: KeyValueBase[object, object, object, object]) -> None:
    if not isinstance(index.storage, AsyncLeasableKeyValueStorage):
        raise NotImplementedError(
            f"{type(index.storage).__name__} cannot lease-get a single-field index"
        )


@contextmanager
def _held_fill_lease(
    storage: LeasableKeyValueStorage[object],
    client: object,
    name: str,
    field: str,
    *,
    lease_ttl: int,
):
    from uuid import uuid4

    token = uuid4().hex
    acquired = storage.try_acquire_lease(
        client, name, field, token=token, lease_ttl=lease_ttl
    )
    try:
        yield acquired
    finally:
        if acquired:
            storage.release_lease(client, name, field, token=token)


@asynccontextmanager
async def _async_held_fill_lease(
    storage: AsyncLeasableKeyValueStorage[object],
    client: object,
    name: str,
    field: str,
    *,
    lease_ttl: int,
):
    from uuid import uuid4

    token = uuid4().hex
    acquired = await storage.try_acquire_lease(
        client, name, field, token=token, lease_ttl=lease_ttl
    )
    try:
        yield acquired
    finally:
        if acquired:
            await storage.release_lease(client, name, field, token=token)


def lease_get_body[ClientType, IdType, ModelType, StorageType](
    index: KeyValueBase[ClientType, IdType, ModelType, StorageType],
    client: ClientType,
    id: IdType,
    callback: Callable[[], ModelType],
    *,
    lease_ttl: int,
    ttl: int | None,
    kwargs: dict,
) -> ModelType | None:
    _assert_leasable_sync(index)
    storage = index.storage
    assert isinstance(storage, LeasableKeyValueStorage)
    field = str(id)
    serializer = resolve_serializer(index.serializer, kwargs)
    raw = storage.get(client, index.key, field)
    if raw is not None:
        return serializer.deserialize(raw)

    with _held_fill_lease(storage, client, index.key, field, lease_ttl=lease_ttl) as acquired:
        if not acquired:
            return None
        raw = storage.get(client, index.key, field)
        if raw is not None:
            return serializer.deserialize(raw)
        value = callback()
        index.set(client, id, value, ttl=ttl, **kwargs)
        return value


async def async_lease_get_body[ClientType, IdType, ModelType, StorageType](
    index: KeyValueBase[ClientType, IdType, ModelType, StorageType],
    client: ClientType,
    id: IdType,
    callback: Callable[[], Awaitable[ModelType]],
    *,
    lease_ttl: int,
    ttl: int | None,
    kwargs: dict,
) -> ModelType | None:
    _assert_leasable_async(index)
    storage = index.storage
    assert isinstance(storage, AsyncLeasableKeyValueStorage)
    field = str(id)
    serializer = resolve_serializer(index.serializer, kwargs)
    raw = await storage.get(client, index.key, field)
    if raw is not None:
        return serializer.deserialize(raw)

    async with _async_held_fill_lease(
        storage, client, index.key, field, lease_ttl=lease_ttl
    ) as acquired:
        if not acquired:
            return None
        raw = await storage.get(client, index.key, field)
        if raw is not None:
            return serializer.deserialize(raw)
        value = await callback()
        await index.set(client, id, value, ttl=ttl, **kwargs)
        return value