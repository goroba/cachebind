"""Copy and merge Redis keys by data structure."""

from collections.abc import AsyncIterator, Iterator

from cachebind.backends.redis.pipeline import async_execute_if_queued, execute_if_queued
from cachebind.backends.redis.types import SCAN_COUNT, AsyncRedis, Redis
from cachebind.backends.redis.decode import required_text, scan_done
from cachebind.backends.redis.keys import async_copy_key, copy_key
from cachebind.backends.redis.ordered_set import pairs_from_range


def _require_distinct(source: str, dest: str) -> None:
    if source == dest:
        raise ValueError("source and dest must differ")


def _zset_windows(client: Redis, source: str, *, count: int) -> Iterator[list[tuple[str, float]]]:
    start = 0
    while True:
        window = pairs_from_range(
            client.zrange(source, start, start + count - 1, withscores=True)
        )
        if not window:
            return
        yield window
        if len(window) < count:
            return
        start += count


async def _async_zset_windows(
    client: AsyncRedis, source: str, *, count: int
) -> AsyncIterator[list[tuple[str, float]]]:
    start = 0
    while True:
        window = pairs_from_range(
            await client.zrange(source, start, start + count - 1, withscores=True)
        )
        if not window:
            return
        yield window
        if len(window) < count:
            return
        start += count


def merge_hash(client: Redis, source: str, dest: str, *, count: int = SCAN_COUNT) -> None:
    """Apply every field in ``source`` onto ``dest`` via batched pipeline writes."""
    pipe = client.pipeline(transaction=False)
    queued = False
    cursor: object = 0
    while True:
        cursor, raw = client.hscan(source, cursor=cursor, count=count)
        if not isinstance(raw, dict):
            raise TypeError(f"unexpected Redis hash scan type: {type(raw).__name__}")
        if raw:
            mapping = {required_text(field): required_text(value) for field, value in raw.items()}
            pipe.hset(dest, mapping=mapping)
            queued = True
        if scan_done(cursor):
            break
    execute_if_queued(pipe, queued)


async def async_merge_hash(
    client: AsyncRedis, source: str, dest: str, *, count: int = SCAN_COUNT
) -> None:
    """Apply every field in ``source`` onto ``dest`` via batched pipeline writes."""
    pipe = client.pipeline(transaction=False)
    queued = False
    cursor: object = 0
    while True:
        cursor, raw = await client.hscan(source, cursor=cursor, count=count)
        if not isinstance(raw, dict):
            raise TypeError(f"unexpected Redis hash scan type: {type(raw).__name__}")
        if raw:
            mapping = {required_text(field): required_text(value) for field, value in raw.items()}
            pipe.hset(dest, mapping=mapping)
            queued = True
        if scan_done(cursor):
            break
    await async_execute_if_queued(pipe, queued)


def copy_hash(client: Redis, source: str, dest: str, *, count: int = SCAN_COUNT) -> None:
    """Duplicate ``source`` onto ``dest``, using server COPY when ``dest`` is absent."""
    _require_distinct(source, dest)
    if not client.exists(dest):
        copy_key(client, source, dest)
        return
    merge_hash(client, source, dest, count=count)


async def async_copy_hash(
    client: AsyncRedis, source: str, dest: str, *, count: int = SCAN_COUNT
) -> None:
    """Duplicate ``source`` onto ``dest``, using server COPY when ``dest`` is absent."""
    _require_distinct(source, dest)
    if not await client.exists(dest):
        await async_copy_key(client, source, dest)
        return
    await async_merge_hash(client, source, dest, count=count)


def merge_zset(client: Redis, source: str, dest: str, *, count: int = SCAN_COUNT) -> None:
    """Apply every member in ``source`` onto ``dest`` via batched pipeline writes."""
    pipe = client.pipeline(transaction=False)
    queued = False
    for window in _zset_windows(client, source, count=count):
        pipe.zadd(dest, {member: score for member, score in window})
        queued = True
    execute_if_queued(pipe, queued)


async def async_merge_zset(
    client: AsyncRedis, source: str, dest: str, *, count: int = SCAN_COUNT
) -> None:
    """Apply every member in ``source`` onto ``dest`` via batched pipeline writes."""
    pipe = client.pipeline(transaction=False)
    queued = False
    async for window in _async_zset_windows(client, source, count=count):
        pipe.zadd(dest, {member: score for member, score in window})
        queued = True
    await async_execute_if_queued(pipe, queued)


def copy_zset(client: Redis, source: str, dest: str, *, count: int = SCAN_COUNT) -> None:
    """Duplicate ``source`` onto ``dest``, using server COPY when ``dest`` is absent."""
    _require_distinct(source, dest)
    if not client.exists(dest):
        copy_key(client, source, dest)
        return
    merge_zset(client, source, dest, count=count)


async def async_copy_zset(
    client: AsyncRedis, source: str, dest: str, *, count: int = SCAN_COUNT
) -> None:
    """Duplicate ``source`` onto ``dest``, using server COPY when ``dest`` is absent."""
    _require_distinct(source, dest)
    if not await client.exists(dest):
        await async_copy_key(client, source, dest)
        return
    await async_merge_zset(client, source, dest, count=count)


def zset_windows(client: Redis, source: str, *, count: int = SCAN_COUNT):
    """Yield ascending scored-member windows from ``source``."""
    yield from _zset_windows(client, source, count=count)


async def async_zset_windows(
    client: AsyncRedis, source: str, *, count: int = SCAN_COUNT
):
    """Yield ascending scored-member windows from ``source``."""
    async for window in _async_zset_windows(client, source, count=count):
        yield window


def copy_set(client: Redis, source: str, dest: str) -> None:
    """Duplicate ``source`` onto ``dest``, using server COPY when ``dest`` is absent."""
    _require_distinct(source, dest)
    if not client.exists(dest):
        copy_key(client, source, dest)
        return
    client.sunionstore(dest, source)


async def async_copy_set(client: AsyncRedis, source: str, dest: str) -> None:
    """Duplicate ``source`` onto ``dest``, using server COPY when ``dest`` is absent."""
    _require_distinct(source, dest)
    if not await client.exists(dest):
        await async_copy_key(client, source, dest)
        return
    await client.sunionstore(dest, source)


def merge_set(client: Redis, source: str, dest: str) -> None:
    """Union ``source`` into ``dest``."""
    _require_distinct(source, dest)
    client.sunionstore(dest, dest, source)


async def async_merge_set(client: AsyncRedis, source: str, dest: str) -> None:
    """Union ``source`` into ``dest``."""
    _require_distinct(source, dest)
    await client.sunionstore(dest, dest, source)


def copy_trie(client: Redis, source: str, dest: str) -> None:
    """Duplicate ``source`` onto ``dest``."""
    copy_key(client, source, dest)


async def async_copy_trie(client: AsyncRedis, source: str, dest: str) -> None:
    """Duplicate ``source`` onto ``dest``."""
    await async_copy_key(client, source, dest)