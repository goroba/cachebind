"""Asynchronous key-value index."""

from collections.abc import AsyncIterable, AsyncIterator, Hashable, Iterator, Mapping, Sequence
from contextlib import asynccontextmanager
from typing import Self

from cachebind.indexes._merge import async_merge_context
from cachebind.indexes._update import async_update_context
from cachebind.indexes._replace import async_replace_context, async_snapshot_context
from cachebind.indexes._serializer import resolve_serializer
from cachebind.indexes.key_value.base import KeyValueBase
from cachebind.serializers.serializer import Serializer
from cachebind.storage.key_value.async_storage import AsyncKeyValueStorage

BATCH = 100


class AsyncKeyValueIndex[ClientType, IdType: Hashable, ModelType, StorageType](
    KeyValueBase[ClientType, IdType, ModelType, StorageType]
):
    """Async key-value index: model binding, storage key, and the storage that persists it.

    Reads deserialize and writes serialize. The identifier is stored as ``str(id)``.
    """

    storage: AsyncKeyValueStorage[ClientType, str, StorageType]

    async def get(
        self,
        client: ClientType,
        id: IdType,
        **kwargs,
    ) -> ModelType | None:
        """Return the cached model, or ``None`` when the id is missing."""
        serializer = resolve_serializer(self.serializer, kwargs)
        raw = await self.storage.get(client, self.key, str(id))
        if raw is None:
            return None
        return serializer.deserialize(raw)

    async def set(
        self,
        client: ClientType,
        id: IdType,
        value: ModelType,
        *,
        ttl: int | None = None,
        **kwargs,
    ) -> str:
        """Store ``value`` under ``id``. Returns the breadcrumb for ``id``."""
        serializer = resolve_serializer(self.serializer, kwargs)
        field = str(id)
        await self.storage.set(client, self.key, field, serializer.serialize(value), ttl=ttl)
        return self.breadcrumbs.encode(self.key, field)

    async def delete(self, client: ClientType, id: IdType) -> None:
        """Remove ``id``. A missing id is not an error."""
        await self.storage.delete(client, self.key, str(id))

    async def evict(self, client: ClientType, identifier: str) -> None:
        """Remove the entry for ``identifier``. A missing entry is not an error.

        ``identifier`` is the tag payload for one id (not the full encoded tag).
        """
        await self.storage.delete(client, self.key, identifier)

    async def mdelete(self, client: ClientType, ids: Sequence[IdType]) -> None:
        """Remove every id. Missing ids are not an error."""
        if not ids:
            return
        await self.storage.mdelete(client, self.key, [str(id) for id in ids])

    async def exists(self, client: ClientType, id: IdType) -> bool:
        """Return whether ``id`` is present."""
        return await self.storage.exists(client, self.key, str(id))

    async def mget(
        self,
        client: ClientType,
        ids: Sequence[IdType],
        **kwargs,
    ) -> list[ModelType | None]:
        """Return models in input order. Missing ids are ``None``."""
        if not ids:
            return []
        serializer = resolve_serializer(self.serializer, kwargs)
        raw_values = await self.storage.mget(client, self.key, [str(id) for id in ids])
        present = [raw for raw in raw_values if raw is not None]
        decoded = iter(serializer.mdeserialize(present))
        return [None if raw is None else next(decoded) for raw in raw_values]

    async def mset(
        self,
        client: ClientType,
        items: Mapping[IdType, ModelType],
        *,
        ttl: int | None = None,
        **kwargs,
    ) -> list[str]:
        """Store every item. ``ttl`` applies to each id. Returns one breadcrumb per item."""
        if not items:
            return []
        serializer = resolve_serializer(self.serializer, kwargs)
        fields = [str(id) for id in items]
        values = serializer.mserialize(list(items.values()))
        mapping = dict(zip(fields, values, strict=True))
        await self.storage.mset(client, self.key, mapping, ttl=ttl)
        return [self.breadcrumbs.encode(self.key, field) for field in fields]

    @asynccontextmanager
    async def snapshot(self, client: ClientType):
        """Yield an unregistered index for the data that was live on enter; drop it on success."""
        async with async_snapshot_context(self, client) as detached:
            yield detached

    @asynccontextmanager
    async def replace(self, client: ClientType):
        """Yield a detached staging index; publish it on success or drop it on failure."""
        async with async_replace_context(self, client) as staging:
            yield staging

    @asynccontextmanager
    async def merge(self, client: ClientType):
        """Yield a detached staging index; merge it into live on success or drop it on failure."""
        async with async_merge_context(self, client) as staging:
            yield staging

    @asynccontextmanager
    async def update(self, client: ClientType):
        """Yield a staging copy of live data; replace live on success or drop staging on failure."""
        async with async_update_context(self, client) as staging:
            yield staging

    async def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        await self.storage.drop(client, self.key)

    async def iter(
        self,
        client: ClientType,
        **kwargs,
    ) -> AsyncIterator[tuple[str, ModelType]]:
        """Yield each stored id and model under this index key."""
        serializer = resolve_serializer(self.serializer, kwargs)
        async for pair in async_pairs(self.storage.iter(client, self.key), serializer):
            yield pair


async def async_pairs[StorageType, ValueType](
    raw: AsyncIterable[tuple[str, StorageType]], serializer: Serializer[ValueType, StorageType]
) -> AsyncIterator[tuple[str, ValueType]]:
    """Yield stored ids and deserialized values, one ``mdeserialize`` per batch."""
    batch: list[tuple[str, StorageType]] = []
    async for item in raw:
        batch.append(item)
        if len(batch) == BATCH:
            for decoded in _pairs(batch, serializer):
                yield decoded
            batch = []
    if batch:
        for decoded in _pairs(batch, serializer):
            yield decoded


def _pairs[StorageType, ValueType](
    batch: list[tuple[str, StorageType]], serializer: Serializer[ValueType, StorageType]
) -> Iterator[tuple[str, ValueType]]:
    decoded = serializer.mdeserialize([value for _field, value in batch])
    return zip((field for field, _value in batch), decoded, strict=True)
