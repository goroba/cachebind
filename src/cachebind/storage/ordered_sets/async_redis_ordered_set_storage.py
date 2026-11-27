"""Asynchronous Redis ordered-set storage."""

from collections.abc import AsyncIterator, Sequence

from cachebind.backends.redis import (
    SCAN_COUNT,
    AsyncRedis,
    async_copy_zset,
    async_merge_zset,
    async_replace_key,
    async_swap_key,
    async_zset_windows,
    empty_range,
    members_from_range,
    pairs_from_range,
    rank_value,
    score_value,
)
from cachebind.storage.copyable import AsyncCopyableStorage
from cachebind.storage.droppable import AsyncDroppableStorage
from cachebind.storage.iterable import AsyncIterableStorage
from cachebind.storage.mergeable import AsyncMergeableStorage
from cachebind.storage.ordered_sets.async_storage import AsyncOrderedSetStorage
from cachebind.storage.replaceable import AsyncReplaceableStorage
from cachebind.storage.snapshotable import AsyncSnapshotableStorage


class AsyncRedisOrderedSetStorage(
    AsyncOrderedSetStorage[AsyncRedis, str],
    AsyncSnapshotableStorage[AsyncRedis],
    AsyncReplaceableStorage[AsyncRedis],
    AsyncMergeableStorage[AsyncRedis],
    AsyncCopyableStorage[AsyncRedis],
    AsyncDroppableStorage[AsyncRedis],
    AsyncIterableStorage[AsyncRedis, tuple[str, float]],
):
    """Asynchronous Redis ordered sets. ``name`` is the Redis key."""

    async def add(self, client: AsyncRedis, name: str, member: str, score: float) -> None:
        await client.zadd(name, {member: score})

    async def madd(
        self, client: AsyncRedis, name: str, members: Sequence[tuple[str, float]]
    ) -> None:
        if not members:
            return
        await client.zadd(name, {member: score for member, score in members})

    async def remove(self, client: AsyncRedis, name: str, member: str) -> None:
        await client.zrem(name, member)

    async def mremove(self, client: AsyncRedis, name: str, members: Sequence[str]) -> None:
        if not members:
            return
        await client.zrem(name, *members)

    async def contains(self, client: AsyncRedis, name: str, member: str) -> bool:
        return (await client.zscore(name, member)) is not None

    async def score(self, client: AsyncRedis, name: str, member: str) -> float | None:
        return score_value(await client.zscore(name, member))

    async def rank(self, client: AsyncRedis, name: str, member: str) -> int | None:
        return rank_value(await client.zrank(name, member))

    async def range(self, client: AsyncRedis, name: str, start: int, stop: int) -> list[str]:
        if empty_range(start, stop):
            return []
        return members_from_range(await client.zrange(name, start, stop))

    async def range_with_scores(
        self, client: AsyncRedis, name: str, start: int, stop: int
    ) -> list[tuple[str, float]]:
        if empty_range(start, stop):
            return []
        return pairs_from_range(await client.zrange(name, start, stop, withscores=True))

    async def rev_rank(self, client: AsyncRedis, name: str, member: str) -> int | None:
        return rank_value(await client.zrevrank(name, member))

    async def rev_range(self, client: AsyncRedis, name: str, start: int, stop: int) -> list[str]:
        if empty_range(start, stop):
            return []
        return members_from_range(await client.zrevrange(name, start, stop))

    async def rev_range_with_scores(
        self, client: AsyncRedis, name: str, start: int, stop: int
    ) -> list[tuple[str, float]]:
        if empty_range(start, stop):
            return []
        return pairs_from_range(await client.zrevrange(name, start, stop, withscores=True))

    async def snapshot(self, client: AsyncRedis, name: str) -> str:
        return await async_swap_key(client, name)

    async def replace(self, client: AsyncRedis, source: str, dest: str) -> None:
        await async_replace_key(client, source, dest)

    async def copy(self, client: AsyncRedis, source: str, dest: str) -> None:
        await async_copy_zset(client, source, dest)

    async def merge(self, client: AsyncRedis, source: str, dest: str) -> None:
        await async_merge_zset(client, source, dest)

    async def drop(self, client: AsyncRedis, name: str) -> None:
        await client.delete(name)

    async def iter(
        self, client: AsyncRedis, name: str, *, count: int = SCAN_COUNT
    ) -> AsyncIterator[tuple[str, float]]:
        async for window in async_zset_windows(client, name, count=count):
            for member, score in window:
                yield member, score
