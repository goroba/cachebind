"""Asynchronous Redis hash storage."""

from collections.abc import AsyncIterator, Mapping, Sequence

from cachebind.backends.redis import (
    SCAN_COUNT,
    AsyncRedis,
    async_copy_hash,
    async_merge_hash,
    async_replace_key,
    async_swap_key,
    decode,
    required_text,
    scan_done,
)
from cachebind.storage.key_value.async_storage import AsyncKeyValueStorage


class AsyncRedisHashStorage(AsyncKeyValueStorage[AsyncRedis, str, str]):
    """Asynchronous Redis hashes. One instance can serve any hash name."""

    async def get(self, client: AsyncRedis, name: str, field: str) -> str | None:
        return decode(await client.hget(name, field))

    async def set(
        self, client: AsyncRedis, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        await client.hset(name, field, value)
        if ttl is not None:
            await client.hexpire(name, ttl, field)

    async def delete(self, client: AsyncRedis, name: str, field: str) -> None:
        await client.hdel(name, field)

    async def mdelete(self, client: AsyncRedis, name: str, fields: Sequence[str]) -> None:
        if not fields:
            return
        await client.hdel(name, *fields)

    async def exists(self, client: AsyncRedis, name: str, field: str) -> bool:
        return bool(await client.hexists(name, field))

    async def mget(self, client: AsyncRedis, name: str, fields: Sequence[str]) -> list[str | None]:
        if not fields:
            return []
        raw_values = await client.hmget(name, list(fields))
        return [decode(raw) for raw in raw_values]

    async def mset(
        self, client: AsyncRedis, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        if not items:
            return
        mapping = dict(items)
        await client.hset(name, mapping=mapping)
        if ttl is not None:
            await client.hexpire(name, ttl, *mapping)

    async def snapshot(self, client: AsyncRedis, name: str) -> str:
        return await async_swap_key(client, name)

    async def replace(self, client: AsyncRedis, source: str, dest: str) -> None:
        await async_replace_key(client, source, dest)

    async def copy(self, client: AsyncRedis, source: str, dest: str) -> None:
        await async_copy_hash(client, source, dest)

    async def merge(self, client: AsyncRedis, source: str, dest: str) -> None:
        await async_merge_hash(client, source, dest)

    async def drop(self, client: AsyncRedis, name: str) -> None:
        await client.delete(name)

    async def iter(
        self, client: AsyncRedis, name: str, *, count: int = SCAN_COUNT
    ) -> AsyncIterator[tuple[str, str]]:
        cursor: object = 0
        while True:
            cursor, raw = await client.hscan(name, cursor=cursor, count=count)
            if not isinstance(raw, dict):
                raise TypeError(f"unexpected Redis hash scan type: {type(raw).__name__}")
            for field, value in raw.items():
                yield required_text(field), required_text(value)
            if scan_done(cursor):
                return
