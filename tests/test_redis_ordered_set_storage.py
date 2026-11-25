import asyncio

import fakeredis

from cachebind.storage import (
    AsyncIterableStorage,
    AsyncRedisOrderedSetStorage,
    IterableStorage,
    RedisOrderedSetStorage,
)
from cachebind.storage.ordered_sets.async_storage import AsyncOrderedSetStorage
from cachebind.storage.ordered_sets.storage import OrderedSetStorage


class _OrderedSetSpy:
    def __init__(self) -> None:
        self.called = False

    def zadd(self, name: str, mapping: dict[str, float]) -> int:
        self.called = True
        return 0

    def zrem(self, name: str, *members: str) -> int:
        self.called = True
        return 0

    def zrange(
        self, name: str, start: int, stop: int, withscores: bool = False
    ) -> list[object]:
        self.called = True
        return []

    def zrevrange(
        self, name: str, start: int, stop: int, withscores: bool = False
    ) -> list[object]:
        self.called = True
        return []


def test_sync_ordered_set_storage_round_trip() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisOrderedSetStorage()
    assert isinstance(storage, OrderedSetStorage)
    assert isinstance(storage, IterableStorage)

    assert storage.contains(client, "scores", "a") is False
    assert storage.score(client, "scores", "a") is None
    assert storage.rank(client, "scores", "a") is None
    assert storage.rev_rank(client, "scores", "a") is None
    storage.remove(client, "scores", "a")

    storage.add(client, "scores", "a", 1.0)
    storage.add(client, "scores", "a", 3.0)
    assert storage.contains(client, "scores", "a") is True
    assert storage.score(client, "scores", "a") == 3.0
    assert client.zscore("scores", "a") == 3.0

    storage.madd(client, "scores", [("b", 1.0), ("b", 2.0), ("c", 4.0)])
    assert storage.score(client, "scores", "b") == 2.0
    assert storage.rank(client, "scores", "b") == 0
    assert storage.rank(client, "scores", "a") == 1
    assert storage.rank(client, "scores", "c") == 2
    assert storage.range(client, "scores", 0, 1) == ["b", "a"]
    assert storage.range(client, "scores", 0, 2) == ["b", "a", "c"]
    assert storage.range_with_scores(client, "scores", 0, 2) == [
        ("b", 2.0),
        ("a", 3.0),
        ("c", 4.0),
    ]
    assert storage.range(client, "scores", 0, -1) == ["b", "a", "c"]
    assert storage.range(client, "scores", 2, 0) == []
    assert storage.range_with_scores(client, "scores", -1, -3) == []
    assert storage.rev_rank(client, "scores", "c") == 0
    assert storage.rev_rank(client, "scores", "a") == 1
    assert storage.rev_rank(client, "scores", "b") == 2
    assert storage.rev_range(client, "scores", 0, 2) == ["c", "a", "b"]
    assert storage.rev_range_with_scores(client, "scores", 0, 2) == [
        ("c", 4.0),
        ("a", 3.0),
        ("b", 2.0),
    ]
    assert storage.rev_range(client, "scores", 2, 0) == []
    assert storage.rev_range_with_scores(client, "scores", -1, -3) == []

    storage.mremove(client, "scores", ["b", "c"])
    assert storage.contains(client, "scores", "b") is False
    assert storage.score(client, "scores", "b") is None
    assert storage.rank(client, "scores", "b") is None
    assert storage.rev_rank(client, "scores", "b") is None
    assert storage.contains(client, "scores", "a") is True
    storage.remove(client, "scores", "a")
    assert storage.contains(client, "scores", "a") is False


def test_sync_ordered_set_storage_empty_batches_do_not_call_redis() -> None:
    spy = _OrderedSetSpy()
    storage = RedisOrderedSetStorage()

    storage.madd(spy, "scores", [])  # type: ignore[arg-type]
    storage.mremove(spy, "scores", [])  # type: ignore[arg-type]
    assert storage.range(spy, "scores", 2, 0) == []  # type: ignore[arg-type]
    assert storage.range_with_scores(spy, "scores", -1, -3) == []  # type: ignore[arg-type]
    assert storage.rev_range(spy, "scores", 2, 0) == []  # type: ignore[arg-type]
    assert storage.rev_range_with_scores(spy, "scores", -1, -3) == []  # type: ignore[arg-type]
    assert spy.called is False


def test_async_ordered_set_storage_round_trip() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        storage = AsyncRedisOrderedSetStorage()
        assert isinstance(storage, AsyncOrderedSetStorage)
        assert isinstance(storage, AsyncIterableStorage)
        try:
            assert await storage.contains(client, "scores", "a") is False
            assert await storage.score(client, "scores", "a") is None
            assert await storage.rank(client, "scores", "a") is None
            assert await storage.rev_rank(client, "scores", "a") is None
            await storage.remove(client, "scores", "a")

            await storage.add(client, "scores", "a", 1.0)
            await storage.add(client, "scores", "a", 3.0)
            assert await storage.contains(client, "scores", "a") is True
            assert await storage.score(client, "scores", "a") == 3.0
            assert await client.zscore("scores", "a") == 3.0

            await storage.madd(client, "scores", [("b", 1.0), ("b", 2.0), ("c", 4.0)])
            assert await storage.score(client, "scores", "b") == 2.0
            assert await storage.rank(client, "scores", "b") == 0
            assert await storage.rank(client, "scores", "a") == 1
            assert await storage.rank(client, "scores", "c") == 2
            assert await storage.range(client, "scores", 0, 1) == ["b", "a"]
            assert await storage.range(client, "scores", 0, 2) == ["b", "a", "c"]
            assert await storage.range_with_scores(client, "scores", 0, 2) == [
                ("b", 2.0),
                ("a", 3.0),
                ("c", 4.0),
            ]
            assert await storage.range(client, "scores", 0, -1) == ["b", "a", "c"]
            assert await storage.range(client, "scores", 2, 0) == []
            assert await storage.range_with_scores(client, "scores", -1, -3) == []
            assert await storage.rev_rank(client, "scores", "c") == 0
            assert await storage.rev_rank(client, "scores", "a") == 1
            assert await storage.rev_rank(client, "scores", "b") == 2
            assert await storage.rev_range(client, "scores", 0, 2) == ["c", "a", "b"]
            assert await storage.rev_range_with_scores(client, "scores", 0, 2) == [
                ("c", 4.0),
                ("a", 3.0),
                ("b", 2.0),
            ]
            assert await storage.rev_range(client, "scores", 2, 0) == []
            assert await storage.rev_range_with_scores(client, "scores", -1, -3) == []

            await storage.mremove(client, "scores", ["b", "c"])
            assert await storage.contains(client, "scores", "b") is False
            assert await storage.score(client, "scores", "b") is None
            assert await storage.rank(client, "scores", "b") is None
            assert await storage.rev_rank(client, "scores", "b") is None
            assert await storage.contains(client, "scores", "a") is True
            await storage.remove(client, "scores", "a")
            assert await storage.contains(client, "scores", "a") is False
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_async_ordered_set_storage_empty_batches_do_not_call_redis() -> None:
    spy = _OrderedSetSpy()
    storage = AsyncRedisOrderedSetStorage()

    async def scenario() -> None:
        await storage.madd(spy, "scores", [])  # type: ignore[arg-type]
        await storage.mremove(spy, "scores", [])  # type: ignore[arg-type]
        assert await storage.range(spy, "scores", 2, 0) == []  # type: ignore[arg-type]
        assert await storage.range_with_scores(spy, "scores", -1, -3) == []  # type: ignore[arg-type]
        assert await storage.rev_range(spy, "scores", 2, 0) == []  # type: ignore[arg-type]
        assert await storage.rev_range_with_scores(spy, "scores", -1, -3) == []  # type: ignore[arg-type]

    asyncio.run(scenario())
    assert spy.called is False


def test_sync_ordered_set_storage_iter_is_ascending() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisOrderedSetStorage()
    storage.madd(client, "scan_scores", [("2", 2.0), ("1", 1.0), ("3", 3.0)])
    assert list(storage.iter(client, "scan_scores", count=2)) == [
        ("1", 1.0),
        ("2", 2.0),
        ("3", 3.0),
    ]
    assert list(storage.iter(client, "scan_missing")) == []


def test_async_ordered_set_storage_iter_is_ascending() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        storage = AsyncRedisOrderedSetStorage()
        try:
            await storage.madd(client, "async_scan_scores", [("2", 2.0), ("1", 1.0), ("3", 3.0)])
            found = [item async for item in storage.iter(client, "async_scan_scores", count=2)]
            assert found == [("1", 1.0), ("2", 2.0), ("3", 3.0)]
            assert [item async for item in storage.iter(client, "async_scan_missing")] == []
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_sync_ordered_set_storage_copy_clones_absent_dest() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisOrderedSetStorage()
    storage.madd(client, "source", [("1", 1.0), ("2", 2.0), ("3", 3.0)])

    storage.copy(client, "source", "dest")
    assert storage.range_with_scores(client, "dest", 0, -1) == [
        ("1", 1.0),
        ("2", 2.0),
        ("3", 3.0),
    ]


def test_sync_ordered_set_storage_copy_overlays_existing_dest() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisOrderedSetStorage()
    storage.madd(client, "source", [("a", 5.0), ("b", 2.0)])
    storage.madd(client, "dest", [("a", 1.0), ("z", 9.0)])

    storage.copy(client, "source", "dest")
    assert storage.score(client, "dest", "a") == 5.0
    assert storage.score(client, "dest", "b") == 2.0
    assert storage.score(client, "dest", "z") == 9.0


def test_sync_ordered_set_storage_merge_overwrites_dest_members() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisOrderedSetStorage()
    storage.madd(client, "source", [("a", 5.0), ("b", 2.0)])
    storage.madd(client, "dest", [("a", 1.0), ("c", 3.0)])

    storage.merge(client, "source", "dest")
    assert storage.range_with_scores(client, "dest", 0, -1) == [
        ("b", 2.0),
        ("c", 3.0),
        ("a", 5.0),
    ]


def test_sync_ordered_set_storage_copy_missing_source_leaves_dest() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisOrderedSetStorage()
    storage.madd(client, "dest", [("a", 1.0)])

    storage.copy(client, "missing", "dest")
    assert storage.score(client, "dest", "a") == 1.0


def test_async_ordered_set_storage_copy_and_merge() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        storage = AsyncRedisOrderedSetStorage()
        try:
            await storage.madd(client, "source", [("1", 1.0), ("2", 2.0), ("3", 3.0)])
            await storage.copy(client, "source", "dest")
            assert await storage.range_with_scores(client, "dest", 0, -1) == [
                ("1", 1.0),
                ("2", 2.0),
                ("3", 3.0),
            ]

            await storage.madd(client, "staging", [("2", 9.0)])
            await storage.merge(client, "staging", "dest")
            assert await storage.score(client, "dest", "2") == 9.0

            await storage.copy(client, "missing", "dest")
            assert await storage.score(client, "dest", "1") == 1.0
        finally:
            await client.aclose()

    asyncio.run(scenario())
