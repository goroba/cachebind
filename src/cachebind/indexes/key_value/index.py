"""Synchronous key-value index."""

from collections.abc import Hashable, Iterable, Iterator, Mapping, Sequence
from typing import Self

from cachebind.indexes._serializer import resolve_serializer
from cachebind.indexes.key_value.base import KeyValueBase
from cachebind.serializers.serializer import Serializer
from cachebind.storage.key_value.storage import KeyValueStorage

BATCH = 100


class KeyValueIndex[ClientType, IdType: Hashable, ModelType, StorageType](
    KeyValueBase[ClientType, IdType, ModelType, StorageType]
):
    """Sync key-value index: model binding, storage key, and the storage that persists it.

    Reads deserialize and writes serialize. The identifier is stored as ``str(id)``.
    """

    storage: KeyValueStorage[ClientType, str, StorageType]

    def get(
        self,
        client: ClientType,
        id: IdType,
        **kwargs,
    ) -> ModelType | None:
        """Return the cached model, or ``None`` when the id is missing."""
        serializer = resolve_serializer(self.serializer, kwargs)
        raw = self.storage.get(client, self.key, str(id))
        if raw is None:
            return None
        return serializer.deserialize(raw)

    def set(
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
        self.storage.set(client, self.key, field, serializer.serialize(value), ttl=ttl)
        return self.breadcrumbs.encode(self.key, field)

    def delete(self, client: ClientType, id: IdType) -> None:
        """Remove ``id``. A missing id is not an error."""
        self.storage.delete(client, self.key, str(id))

    def evict(self, client: ClientType, identifier: str) -> None:
        """Remove the entry for ``identifier``. A missing entry is not an error.

        ``identifier`` is the tag payload for one id (not the full encoded tag).
        """
        self.storage.delete(client, self.key, identifier)

    def mdelete(self, client: ClientType, ids: Sequence[IdType]) -> None:
        """Remove every id. Missing ids are not an error."""
        if not ids:
            return
        self.storage.mdelete(client, self.key, [str(id) for id in ids])

    def exists(self, client: ClientType, id: IdType) -> bool:
        """Return whether ``id`` is present."""
        return self.storage.exists(client, self.key, str(id))

    def mget(
        self,
        client: ClientType,
        ids: Sequence[IdType],
        **kwargs,
    ) -> list[ModelType | None]:
        """Return models in input order. Missing ids are ``None``."""
        if not ids:
            return []
        serializer = resolve_serializer(self.serializer, kwargs)
        raw_values = self.storage.mget(client, self.key, [str(id) for id in ids])
        present = [raw for raw in raw_values if raw is not None]
        decoded = iter(serializer.mdeserialize(present))
        return [None if raw is None else next(decoded) for raw in raw_values]

    def mset(
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
        self.storage.mset(client, self.key, mapping, ttl=ttl)
        return [self.breadcrumbs.encode(self.key, field) for field in fields]

    def snapshot(self, client: ClientType) -> Self:
        """Rename this index aside and return an unregistered index for that data."""
        return self.detach(self.storage.swap(client, self.key))

    def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        self.storage.drop(client, self.key)

    def iter(
        self,
        client: ClientType,
        **kwargs,
    ) -> Iterator[tuple[str, ModelType]]:
        """Yield each stored id and model under this index key."""
        serializer = resolve_serializer(self.serializer, kwargs)
        return pairs(self.storage.iter(client, self.key), serializer)


def pairs[StorageType, ValueType](
    raw: Iterable[tuple[str, StorageType]], serializer: Serializer[ValueType, StorageType]
) -> Iterator[tuple[str, ValueType]]:
    """Yield stored ids and deserialized values, one ``mdeserialize`` per batch."""
    batch: list[tuple[str, StorageType]] = []
    for item in raw:
        batch.append(item)
        if len(batch) == BATCH:
            yield from _pairs(batch, serializer)
            batch = []
    if batch:
        yield from _pairs(batch, serializer)


def _pairs[StorageType, ValueType](
    batch: list[tuple[str, StorageType]], serializer: Serializer[ValueType, StorageType]
) -> Iterator[tuple[str, ValueType]]:
    decoded = serializer.mdeserialize([value for _field, value in batch])
    return zip((field for field, _value in batch), decoded, strict=True)
