"""Synchronous Redis hash storage."""

from collections.abc import Iterator, Mapping, Sequence

from cachebind.backends.redis import (
    SCAN_COUNT,
    Redis,
    copy_hash,
    decode,
    merge_hash,
    release_lease,
    replace_key,
    required_text,
    scan_done,
    swap_key,
    try_acquire_lease as redis_try_acquire_lease,
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

    def copy(self, client: Redis, source: str, dest: str) -> None:
        copy_hash(client, source, dest)

    def merge(self, client: Redis, source: str, dest: str) -> None:
        merge_hash(client, source, dest)

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
