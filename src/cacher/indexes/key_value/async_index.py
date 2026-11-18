"""Asynchronous key-value index."""

from collections.abc import Hashable, Mapping, Sequence
from typing import Self

from cacher.indexes.key_value.base import KeyValueBase
from cacher.storage.key_value.async_storage import AsyncKeyValueStorage


class AsyncKeyValueIndex[ClientType, IdType: Hashable, ModelType, StorageType](
    KeyValueBase[ClientType, IdType, ModelType, StorageType]
):
    """Async key-value index: model binding, storage key, and the storage that persists it.

    Reads deserialize and writes serialize. The identifier is stored as ``str(id)``.
    """

    storage: AsyncKeyValueStorage[ClientType, str, StorageType]

    async def get(self, client: ClientType, id: IdType) -> ModelType | None:
        """Return the cached model, or ``None`` when the id is missing."""
        raw = await self.storage.get(client, self.key, str(id))
        if raw is None:
            return None
        return self.serializer.deserialize(raw)

    async def set(
        self, client: ClientType, id: IdType, value: ModelType, *, ttl: int | None = None
    ) -> None:
        """Store ``value`` under ``id``."""
        await self.storage.set(client, self.key, str(id), self.serializer.serialize(value), ttl=ttl)

    async def delete(self, client: ClientType, id: IdType) -> None:
        """Remove ``id``. A missing id is not an error."""
        await self.storage.delete(client, self.key, str(id))

    async def mdelete(self, client: ClientType, ids: Sequence[IdType]) -> None:
        """Remove every id. Missing ids are not an error."""
        if not ids:
            return
        await self.storage.mdelete(client, self.key, [str(id) for id in ids])

    async def exists(self, client: ClientType, id: IdType) -> bool:
        """Return whether ``id`` is present."""
        return await self.storage.exists(client, self.key, str(id))

    async def mget(self, client: ClientType, ids: Sequence[IdType]) -> list[ModelType | None]:
        """Return models in input order. Missing ids are ``None``."""
        if not ids:
            return []
        raw_values = await self.storage.mget(client, self.key, [str(id) for id in ids])
        present = [raw for raw in raw_values if raw is not None]
        decoded = iter(self.serializer.mdeserialize(present))
        return [None if raw is None else next(decoded) for raw in raw_values]

    async def mset(
        self, client: ClientType, items: Mapping[IdType, ModelType], *, ttl: int | None = None
    ) -> None:
        """Store every item. ``ttl`` applies to each id."""
        if not items:
            return
        fields = [str(id) for id in items]
        values = self.serializer.mserialize(list(items.values()))
        mapping = dict(zip(fields, values, strict=True))
        await self.storage.mset(client, self.key, mapping, ttl=ttl)

    async def swap(self, client: ClientType) -> Self:
        """Rename this index aside and return an unregistered index for that data."""
        return self.detach(await self.storage.swap(client, self.key))

    async def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        await self.storage.drop(client, self.key)
