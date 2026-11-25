"""Synchronous Redis set storage."""

from collections.abc import Iterator, Sequence

from cachebind.backends.redis import (
    SCAN_COUNT,
    Redis,
    replace_key,
    required_text,
    scan_done,
    swap_key,
)
from cachebind.storage.sets.storage import SetStorage


class RedisSetStorage(SetStorage[Redis, str]):
    """Synchronous Redis sets. ``name`` is the Redis key."""

    def add(self, client: Redis, name: str, member: str) -> None:
        client.sadd(name, member)

    def madd(self, client: Redis, name: str, members: Sequence[str]) -> None:
        if not members:
            return
        client.sadd(name, *members)

    def remove(self, client: Redis, name: str, member: str) -> None:
        client.srem(name, member)

    def mremove(self, client: Redis, name: str, members: Sequence[str]) -> None:
        if not members:
            return
        client.srem(name, *members)

    def contains(self, client: Redis, name: str, member: str) -> bool:
        return bool(client.sismember(name, member))

    def snapshot(self, client: Redis, name: str) -> str:
        return swap_key(client, name)

    def replace(self, client: Redis, source: str, dest: str) -> None:
        replace_key(client, source, dest)

    def copy(self, client: Redis, source: str, dest: str) -> None:
        if source == dest:
            raise ValueError("source and dest must differ")
        client.sunionstore(dest, source)

    def merge(self, client: Redis, source: str, dest: str) -> None:
        if source == dest:
            raise ValueError("source and dest must differ")
        client.sunionstore(dest, dest, source)

    def drop(self, client: Redis, name: str) -> None:
        client.delete(name)

    def iter(self, client: Redis, name: str, *, count: int = SCAN_COUNT) -> Iterator[str]:
        cursor: object = 0
        while True:
            cursor, raw = client.sscan(name, cursor=cursor, count=count)
            if not isinstance(raw, list):
                raise TypeError(f"unexpected Redis set scan type: {type(raw).__name__}")
            for member in raw:
                yield required_text(member)
            if scan_done(cursor):
                return
