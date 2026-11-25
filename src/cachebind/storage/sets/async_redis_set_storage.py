"""Asynchronous Redis set storage."""

from collections.abc import AsyncIterator, Sequence

from cachebind.backends.redis import (
    SCAN_COUNT,
    AsyncRedis,
    async_copy_set,
    async_merge_set,
    async_replace_key,
    async_swap_key,
    required_text,
    scan_done,
)
from cachebind.storage.sets.async_storage import AsyncSetStorage


class AsyncRedisSetStorage(AsyncSetStorage[AsyncRedis, str]):
    """Asynchronous Redis sets. ``name`` is the Redis key."""

    async def add(self, client: AsyncRedis, name: str, member: str) -> None:
        await client.sadd(name, member)

    async def madd(self, client: AsyncRedis, name: str, members: Sequence[str]) -> None:
        if not members:
            return
        await client.sadd(name, *members)

    async def remove(self, client: AsyncRedis, name: str, member: str) -> None:
        await client.srem(name, member)

    async def mremove(self, client: AsyncRedis, name: str, members: Sequence[str]) -> None:
        if not members:
            return
        await client.srem(name, *members)

    async def contains(self, client: AsyncRedis, name: str, member: str) -> bool:
        return bool(await client.sismember(name, member))

    async def snapshot(self, client: AsyncRedis, name: str) -> str:
        return await async_swap_key(client, name)

    async def replace(self, client: AsyncRedis, source: str, dest: str) -> None:
        await async_replace_key(client, source, dest)

    async def copy(self, client: AsyncRedis, source: str, dest: str) -> None:
        await async_copy_set(client, source, dest)

    async def merge(self, client: AsyncRedis, source: str, dest: str) -> None:
        await async_merge_set(client, source, dest)

    async def drop(self, client: AsyncRedis, name: str) -> None:
        await client.delete(name)

    async def iter(
        self, client: AsyncRedis, name: str, *, count: int = SCAN_COUNT
    ) -> AsyncIterator[str]:
        cursor: object = 0
        while True:
            cursor, raw = await client.sscan(name, cursor=cursor, count=count)
            if not isinstance(raw, list):
                raise TypeError(f"unexpected Redis set scan type: {type(raw).__name__}")
            for member in raw:
                yield required_text(member)
            if scan_done(cursor):
                return
