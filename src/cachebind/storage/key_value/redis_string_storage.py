"""Synchronous Redis string storage."""

from collections.abc import Iterator, Mapping, Sequence

from cachebind.storage._redis import Redis, decode
from cachebind.storage.key_value.storage import KeyValueStorage


def _redis_key(name: str, field: str) -> str:
    return f"{name}:{field}"


class RedisStringStorage(KeyValueStorage[Redis, str, str]):
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
