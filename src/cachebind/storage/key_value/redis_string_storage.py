"""Synchronous Redis string storage."""

from collections.abc import Iterator, Mapping, Sequence

from cachebind.backends.redis import Redis, decode, release_lease, try_acquire_lease as redis_try_acquire_lease
from cachebind.storage.copyable import CopyableStorage
from cachebind.storage.droppable import DroppableStorage
from cachebind.storage.iterable import IterableStorage
from cachebind.storage.key_value.storage import KeyValueStorage
from cachebind.storage.leaseable import LeasableKeyValueStorage
from cachebind.storage.mergeable import MergeableStorage
from cachebind.storage.replaceable import ReplaceableStorage
from cachebind.storage.snapshotable import SnapshotableStorage


def _redis_key(name: str, field: str) -> str:
    return f"{name}:{field}"


class RedisStringStorage(
    KeyValueStorage[Redis, str, str],
    SnapshotableStorage[Redis],
    ReplaceableStorage[Redis],
    MergeableStorage[Redis],
    CopyableStorage[Redis],
    DroppableStorage[Redis],
    IterableStorage[Redis, tuple[str, str]],
    LeasableKeyValueStorage[Redis],
):
    """Synchronous Redis strings. The Redis key is ``name:field``."""

    def get(self, client: Redis, name: str, field: str) -> str | None:
        return decode(client.get(_redis_key(name, field)))

    def set(
        self, client: Redis, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        key = _redis_key(name, field)
        if ttl is None:
            client.set(key, value)
        else:
            client.set(key, value, ex=ttl)

    def delete(self, client: Redis, name: str, field: str) -> None:
        client.delete(_redis_key(name, field))

    def mdelete(self, client: Redis, name: str, fields: Sequence[str]) -> None:
        if not fields:
            return
        client.delete(*(_redis_key(name, field) for field in fields))

    def exists(self, client: Redis, name: str, field: str) -> bool:
        return bool(client.exists(_redis_key(name, field)))

    def try_acquire_lease(
        self,
        client: Redis,
        name: str,
        field: str,
        *,
        token: str,
        lease_ttl: int,
    ) -> bool:
        return redis_try_acquire_lease(
            client,
            field_present=self.exists(client, name, field),
            name=name,
            field=field,
            token=token,
            lease_ttl=lease_ttl,
        )

    def release_lease(
        self, client: Redis, name: str, field: str, *, token: str
    ) -> None:
        release_lease(client, name, field, token=token)

    def mget(self, client: Redis, name: str, fields: Sequence[str]) -> list[str | None]:
        if not fields:
            return []
        raw = client.mget([_redis_key(name, field) for field in fields])
        return [decode(item) for item in raw]

    def mset(
        self, client: Redis, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        if not items:
            return
        mapping = {_redis_key(name, field): value for field, value in items.items()}
        if ttl is None:
            client.mset(mapping)
            return
        pipe = client.pipeline(transaction=True)
        for key, value in mapping.items():
            pipe.set(key, value, ex=ttl)
        pipe.execute()

    def snapshot(self, client: Redis, name: str) -> str:
        raise NotImplementedError(
            f"{type(self).__name__} keeps one Redis key per field and cannot snapshot"
        )

    def replace(self, client: Redis, source: str, dest: str) -> None:
        raise NotImplementedError(
            f"{type(self).__name__} keeps one Redis key per field and cannot replace"
        )

    def merge(self, client: Redis, source: str, dest: str) -> None:
        raise NotImplementedError(
            f"{type(self).__name__} keeps one Redis key per field and cannot merge"
        )

    def copy(self, client: Redis, source: str, dest: str) -> None:
        raise NotImplementedError(
            f"{type(self).__name__} keeps one Redis key per field and cannot copy"
        )

    def drop(self, client: Redis, name: str) -> None:
        raise NotImplementedError(
            f"{type(self).__name__} keeps one Redis key per field and cannot drop"
        )

    def iter(self, client: Redis, name: str) -> Iterator[tuple[str, str]]:
        raise NotImplementedError(
            f"{type(self).__name__} keeps one Redis key per field and cannot iter"
        )
