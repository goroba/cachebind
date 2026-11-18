"""Synchronous key-value storage."""

from collections.abc import Hashable, Mapping, Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class KeyValueStorage[ClientType, FieldType: Hashable, StorageType](Protocol):
    """Synchronous key-value storage.

    ``client`` is the storage client for that call.
    ``name`` is the storage name. ``field`` identifies one stored value.
    ``ttl`` is a whole number of seconds. ``None`` means the write does not expire.
    ``mset`` applies one TTL to every field.
    A storage that cannot treat ``name`` as one key raises ``NotImplementedError`` from ``swap``.
    """

    def get(self, client: ClientType, name: str, field: FieldType) -> StorageType | None:
        """Return the stored value, or ``None`` when the field is missing."""
        ...

    def set(
        self,
        client: ClientType,
        name: str,
        field: FieldType,
        value: StorageType,
        *,
        ttl: int | None = None,
    ) -> None:
        """Store ``value`` under ``field``."""
        ...

    def delete(self, client: ClientType, name: str, field: FieldType) -> None:
        """Remove ``field``. A missing field is not an error."""
        ...

    def mdelete(self, client: ClientType, name: str, fields: Sequence[FieldType]) -> None:
        """Remove every field. Missing fields are not an error."""
        ...

    def exists(self, client: ClientType, name: str, field: FieldType) -> bool:
        """Return whether ``field`` is present."""
        ...

    def mget(
        self, client: ClientType, name: str, fields: Sequence[FieldType]
    ) -> list[StorageType | None]:
        """Return values in input order. Missing fields are ``None``."""
        ...

    def mset(
        self,
        client: ClientType,
        name: str,
        items: Mapping[FieldType, StorageType],
        *,
        ttl: int | None = None,
    ) -> None:
        """Store every item. ``ttl`` applies to each field."""
        ...

    def swap(self, client: ClientType, name: str) -> str:
        """Rename ``name`` aside and return the new name. A missing name still returns one."""
        ...
