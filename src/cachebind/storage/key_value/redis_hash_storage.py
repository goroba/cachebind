"""Synchronous Redis hash storage."""

from collections.abc import Iterator, Mapping, Sequence

from cachebind.storage._redis import (
    SCAN_COUNT,
    Redis,
    decode,
    replace_key,
    required_text,
    scan_done,
    swap_key,
)
from cachebind.storage.key_value.storage import KeyValueStorage


class RedisHashStorage(KeyValueStorage[Redis, str, str]):
    """Synchronous Redis hashes. One instance can serve any hash name."""

    def get(self, client: Redis, name: str, field: str) -> str | None:
        return decode(client.hget(name, field))

    def set(
        self, client: Redis, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        client.hset(name, field, value)
        if ttl is not None:
            client.hexpire(name, ttl, field)

    def delete(self, client: Redis, name: str, field: str) -> None:
        client.hdel(name, field)

    def mdelete(self, client: Redis, name: str, fields: Sequence[str]) -> None:
        if not fields:
            return
        client.hdel(name, *fields)

    def exists(self, client: Redis, name: str, field: str) -> bool:
        return bool(client.hexists(name, field))

    def mget(self, client: Redis, name: str, fields: Sequence[str]) -> list[str | None]:
        if not fields:
            return []
        raw_values = client.hmget(name, list(fields))
        return [decode(raw) for raw in raw_values]

    def mset(
        self, client: Redis, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        if not items:
            return
        mapping = dict(items)
        client.hset(name, mapping=mapping)
        if ttl is not None:
            client.hexpire(name, ttl, *mapping)

    def snapshot(self, client: Redis, name: str) -> str:
        return swap_key(client, name)

    def replace(self, client: Redis, source: str, dest: str) -> None:
        replace_key(client, source, dest)

    def merge(self, client: Redis, source: str, dest: str) -> None:
        for field, value in self.iter(client, source):
            client.hset(dest, field, value)

    def drop(self, client: Redis, name: str) -> None:
        client.delete(name)

    def iter(
        self, client: Redis, name: str, *, count: int = SCAN_COUNT
    ) -> Iterator[tuple[str, str]]:
        cursor: object = 0
        while True:
            cursor, raw = client.hscan(name, cursor=cursor, count=count)
            if not isinstance(raw, dict):
                raise TypeError(f"unexpected Redis hash scan type: {type(raw).__name__}")
            for field, value in raw.items():
                yield required_text(field), required_text(value)
            if scan_done(cursor):
                return
