import asyncio
from collections.abc import Sequence

import fakeredis
import pytest
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from cachebind import (
    AsyncOrderedSetIndex,
    IntSerializer,
    OrderedSetIndex,
    build_async_key_value_index,
    build_async_ordered_set_index,
    build_async_set_index,
    build_key_value_index,
    build_ordered_set_index,
    build_set_index,
    get_registry,
)
from cachebind.serializers.datetime_serializer import DatetimeSerializer
from cachebind.storage.key_value.async_redis_string_storage import AsyncRedisStringStorage
from cachebind.storage.key_value.redis_string_storage import RedisStringStorage
from cachebind.storage.ordered_sets.async_redis_ordered_set_storage import AsyncRedisOrderedSetStorage
from cachebind.storage.ordered_sets.async_storage import AsyncOrderedSetStorage
from cachebind.storage.ordered_sets.redis_ordered_set_storage import RedisOrderedSetStorage
from cachebind.storage.ordered_sets.storage import OrderedSetStorage
from cachebind.storage.sets.async_redis_set_storage import AsyncRedisSetStorage
from cachebind.storage.sets.redis_set_storage import RedisSetStorage


class Spy:
    pass


class SpyOrderedSet(OrderedSetStorage[Spy, str]):
    def __init__(self) -> None:
        self.called = False

    def madd(self, client: Spy, name: str, members: Sequence[tuple[str, float]]) -> None:
        self.called = True

    def mremove(self, client: Spy, name: str, members: Sequence[str]) -> None:
        self.called = True

    def range(self, client: Spy, name: str, start: int, stop: int) -> list[str]:
        self.called = True
        return []

    def range_with_scores(
        self, client: Spy, name: str, start: int, stop: int
    ) -> list[tuple[str, float]]:
        self.called = True
        return []

    def rev_range(self, client: Spy, name: str, start: int, stop: int) -> list[str]:
        self.called = True
        return []

    def rev_range_with_scores(
        self, client: Spy, name: str, start: int, stop: int
    ) -> list[tuple[str, float]]:
        self.called = True
        return []


class AsyncSpy:
    pass


class AsyncSpyOrderedSet(AsyncOrderedSetStorage[AsyncSpy, str]):
    def __init__(self) -> None:
        self.called = False

    async def madd(
        self, client: AsyncSpy, name: str, members: Sequence[tuple[str, float]]
    ) -> None:
        self.called = True

    async def mremove(self, client: AsyncSpy, name: str, members: Sequence[str]) -> None:
        self.called = True

    async def range(self, client: AsyncSpy, name: str, start: int, stop: int) -> list[str]:
        self.called = True
        return []

    async def range_with_scores(
        self, client: AsyncSpy, name: str, start: int, stop: int
    ) -> list[tuple[str, float]]:
        self.called = True
        return []

    async def rev_range(self, client: AsyncSpy, name: str, start: int, stop: int) -> list[str]:
        self.called = True
        return []

    async def rev_range_with_scores(
        self, client: AsyncSpy, name: str, start: int, stop: int
    ) -> list[tuple[str, float]]:
        self.called = True
        return []


class BytesOrderedSet(OrderedSetStorage[Spy, bytes]):
    pass


def test_ordered_set_builders_are_public() -> None:
    import cachebind

    assert cachebind.build_ordered_set_index is build_ordered_set_index
    assert cachebind.build_async_ordered_set_index is build_async_ordered_set_index


def test_sync_ordered_set_index_round_trip() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisOrderedSetStorage()
    index = build_ordered_set_index(
        "user_scores",
        member_type=int,
        serializer=IntSerializer(),
        storage=storage,
    )
    assert index is get_registry(Redis).get("user_scores")
    assert index.client_type is Redis
    assert isinstance(index, OrderedSetIndex)
    assert index.member is int
    assert index.key == "user_scores"
    assert index.storage is storage
    assert isinstance(index.serializer, IntSerializer)

    assert index.contains(client, 1) is False
    assert index.score(client, 1) is None
    assert index.rank(client, 1) is None
    assert index.rev_rank(client, 1) is None
    index.remove(client, 1)

    index.add(client, 1, 10.0)
    index.add(client, 1, 30.0)
    assert index.contains(client, 1) is True
    assert index.score(client, 1) == 30.0
    assert client.zscore("user_scores", "1") == 30.0

    index.madd(client, [(2, 10.0), (2, 20.0), (3, 40.0)])
    assert index.score(client, 2) == 20.0
    assert index.rank(client, 2) == 0
    assert index.rank(client, 1) == 1
    assert index.rank(client, 3) == 2
    assert index.range(client, 0, 1) == [2, 1]
    assert index.range(client, 0, 2) == [2, 1, 3]
    assert index.range_with_scores(client, 0, 2) == [(2, 20.0), (1, 30.0), (3, 40.0)]
    assert index.range(client, 0, -1) == [2, 1, 3]
    assert index.range(client, 2, 0) == []
    assert index.range_with_scores(client, -1, -3) == []
    assert index.rev_rank(client, 3) == 0
    assert index.rev_rank(client, 1) == 1
    assert index.rev_rank(client, 2) == 2
    assert index.rev_range(client, 0, 2) == [3, 1, 2]
    assert index.rev_range_with_scores(client, 0, 2) == [(3, 40.0), (1, 30.0), (2, 20.0)]
    assert index.rev_range(client, 2, 0) == []
    assert index.rev_range_with_scores(client, -1, -3) == []

    index.mremove(client, [2, 3])
    assert index.contains(client, 2) is False
    assert index.score(client, 2) is None
    assert index.rank(client, 2) is None
    assert index.rev_rank(client, 2) is None
    assert index.contains(client, 1) is True
    index.remove(client, 1)
    assert index.contains(client, 1) is False
    assert index.range(client, 0, -1) == []


def test_async_ordered_set_index_round_trip() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        try:
            storage = AsyncRedisOrderedSetStorage()
            index = build_async_ordered_set_index(
                "async_user_scores",
                member_type=int,
                serializer=IntSerializer(),
                storage=storage,
            )
            assert index is get_registry(AsyncRedis).get("async_user_scores")
            assert index.client_type is AsyncRedis
            assert isinstance(index, AsyncOrderedSetIndex)
            assert index.member is int
            assert index.storage is storage

            assert await index.contains(client, 1) is False
            assert await index.score(client, 1) is None
            assert await index.rank(client, 1) is None
            assert await index.rev_rank(client, 1) is None
            await index.remove(client, 1)

            await index.add(client, 1, 10.0)
            await index.add(client, 1, 30.0)
            assert await index.contains(client, 1) is True
            assert await index.score(client, 1) == 30.0
            assert await client.zscore("async_user_scores", "1") == 30.0

            await index.madd(client, [(2, 10.0), (2, 20.0), (3, 40.0)])
            assert await index.score(client, 2) == 20.0
            assert await index.rank(client, 2) == 0
            assert await index.rank(client, 1) == 1
            assert await index.rank(client, 3) == 2
            assert await index.range(client, 0, 1) == [2, 1]
            assert await index.range(client, 0, 2) == [2, 1, 3]
            assert await index.range_with_scores(client, 0, 2) == [
                (2, 20.0),
                (1, 30.0),
                (3, 40.0),
            ]
            assert await index.range(client, 0, -1) == [2, 1, 3]
            assert await index.range(client, 2, 0) == []
            assert await index.range_with_scores(client, -1, -3) == []
            assert await index.rev_rank(client, 3) == 0
            assert await index.rev_rank(client, 1) == 1
            assert await index.rev_rank(client, 2) == 2
            assert await index.rev_range(client, 0, 2) == [3, 1, 2]
            assert await index.rev_range_with_scores(client, 0, 2) == [
                (3, 40.0),
                (1, 30.0),
                (2, 20.0),
            ]
            assert await index.rev_range(client, 2, 0) == []
            assert await index.rev_range_with_scores(client, -1, -3) == []

            await index.mremove(client, [2, 3])
            assert await index.contains(client, 2) is False
            assert await index.score(client, 2) is None
            assert await index.rank(client, 2) is None
            assert await index.rev_rank(client, 2) is None
            assert await index.contains(client, 1) is True
            await index.remove(client, 1)
            assert await index.contains(client, 1) is False
            assert await index.range(client, 0, -1) == []
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_duplicate_ordered_set_key() -> None:
    first = build_ordered_set_index(
        "ordered_duplicate",
        member_type=int,
        serializer=IntSerializer(),
        storage=RedisOrderedSetStorage(),
    )
    with pytest.raises(ValueError):
        build_ordered_set_index(
            "ordered_duplicate",
            member_type=int,
            serializer=IntSerializer(),
            storage=RedisOrderedSetStorage(),
        )
    assert get_registry(Redis).get("ordered_duplicate") is first


def test_redis_and_async_redis_can_share_an_ordered_set_key() -> None:
    sync = build_ordered_set_index(
        "ordered_sync_async",
        member_type=int,
        serializer=IntSerializer(),
        storage=RedisOrderedSetStorage(),
    )
    async_index = build_async_ordered_set_index(
        "ordered_sync_async",
        member_type=int,
        serializer=IntSerializer(),
        storage=AsyncRedisOrderedSetStorage(),
    )
    assert get_registry(Redis).get("ordered_sync_async") is sync
    assert get_registry(AsyncRedis).get("ordered_sync_async") is async_index


def test_same_client_set_and_ordered_set_indexes_share_a_registry() -> None:
    existing = build_set_index(
        "ordered_shared_set",
        member_type=int,
        serializer=IntSerializer(),
        storage=RedisSetStorage(),
    )
    with pytest.raises(ValueError):
        build_ordered_set_index(
            "ordered_shared_set",
            member_type=int,
            serializer=IntSerializer(),
            storage=RedisOrderedSetStorage(),
        )
    assert get_registry(Redis).get("ordered_shared_set") is existing


def test_same_client_key_value_and_ordered_set_indexes_share_a_registry() -> None:
    existing = build_key_value_index(
        "ordered_shared_users",
        id_type=int,
        model_type=int,
        serializer=IntSerializer(),
        storage=RedisStringStorage(),
    )
    with pytest.raises(ValueError):
        build_ordered_set_index(
            "ordered_shared_users",
            member_type=int,
            serializer=IntSerializer(),
            storage=RedisOrderedSetStorage(),
        )
    assert get_registry(Redis).get("ordered_shared_users") is existing


def test_same_async_client_set_and_ordered_set_indexes_share_a_registry() -> None:
    existing = build_async_set_index(
        "async_ordered_shared_set",
        member_type=int,
        serializer=IntSerializer(),
        storage=AsyncRedisSetStorage(),
    )
    with pytest.raises(ValueError):
        build_async_ordered_set_index(
            "async_ordered_shared_set",
            member_type=int,
            serializer=IntSerializer(),
            storage=AsyncRedisOrderedSetStorage(),
        )
    assert get_registry(AsyncRedis).get("async_ordered_shared_set") is existing


def test_same_async_client_key_value_and_ordered_set_indexes_share_a_registry() -> None:
    existing = build_async_key_value_index(
        "async_ordered_shared_users",
        id_type=int,
        model_type=int,
        serializer=IntSerializer(),
        storage=AsyncRedisStringStorage(),
    )
    with pytest.raises(ValueError):
        build_async_ordered_set_index(
            "async_ordered_shared_users",
            member_type=int,
            serializer=IntSerializer(),
            storage=AsyncRedisOrderedSetStorage(),
        )
    assert get_registry(AsyncRedis).get("async_ordered_shared_users") is existing


def test_rejected_ordered_set_indexes_do_not_register() -> None:
    cases: tuple[tuple[str, object], ...] = (
        (
            "ordered_member_mismatch",
            lambda: build_ordered_set_index(
                "ordered_member_mismatch",
                member_type=int,
                serializer=DatetimeSerializer(),
                storage=RedisOrderedSetStorage(),
            ),
        ),
        (
            "ordered_storage_mismatch",
            lambda: build_ordered_set_index(
                "ordered_storage_mismatch",
                member_type=int,
                serializer=IntSerializer(),
                storage=BytesOrderedSet(),
            ),
        ),
        (
            "ordered_sync_storage",
            lambda: build_async_ordered_set_index(
                "ordered_sync_storage",
                member_type=int,
                serializer=IntSerializer(),
                storage=SpyOrderedSet(),
            ),
        ),
    )
    for key, build in cases:
        with pytest.raises(TypeError):
            build()
        for client in (Redis, AsyncRedis, Spy):
            try:
                registry = get_registry(client)
            except KeyError:
                continue
            assert key not in registry


def test_empty_ordered_set_batches_do_not_call_storage() -> None:
    storage = SpyOrderedSet()
    index = build_ordered_set_index(
        "ordered_empty_batches",
        member_type=int,
        serializer=IntSerializer(),
        storage=storage,
    )
    client = Spy()
    index.madd(client, [])
    index.mremove(client, [])
    index.range(client, 2, 0)
    index.range_with_scores(client, -1, -3)
    index.rev_range(client, 2, 0)
    index.rev_range_with_scores(client, -1, -3)
    assert storage.called is False


def test_async_empty_ordered_set_batches_do_not_call_storage() -> None:
    storage = AsyncSpyOrderedSet()
    index = build_async_ordered_set_index(
        "async_ordered_empty_batches",
        member_type=int,
        serializer=IntSerializer(),
        storage=storage,
    )
    client = AsyncSpy()

    async def scenario() -> None:
        await index.madd(client, [])
        await index.mremove(client, [])
        await index.range(client, 2, 0)
        await index.range_with_scores(client, -1, -3)
        await index.rev_range(client, 2, 0)
        await index.rev_range_with_scores(client, -1, -3)

    asyncio.run(scenario())
    assert storage.called is False


def test_ordered_set_index_swap_detaches_data() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    index = build_ordered_set_index(
        "swap_leaderboard",
        member_type=int,
        serializer=IntSerializer(),
        storage=RedisOrderedSetStorage(),
    )
    index.add(client, 2, 2.0)
    index.add(client, 1, 1.0)
    snapshot = index.swap(client)
    registry = get_registry(Redis)
    assert registry.get("swap_leaderboard") is index
    assert snapshot is not index
    assert snapshot.key.startswith("swap_leaderboard:swap:")
    assert snapshot.key not in registry
    assert index.score(client, 1) is None
    assert snapshot.score(client, 1) == 1.0
    assert list(snapshot.iter(client)) == [(1, 1.0), (2, 2.0)]
    index.add(client, 3, 3.0)
    assert index.score(client, 3) == 3.0
    assert snapshot.score(client, 3) is None
    assert list(snapshot.iter(client)) == [(1, 1.0), (2, 2.0)]
    snapshot.drop(client)
    assert registry.get("swap_leaderboard") is index
    assert index.score(client, 3) == 3.0
    assert snapshot.score(client, 1) is None

    missing = build_ordered_set_index(
        "swap_leaderboard_missing",
        member_type=int,
        serializer=IntSerializer(),
        storage=RedisOrderedSetStorage(),
    )
    empty = missing.swap(client)
    assert registry.get("swap_leaderboard_missing") is missing
    assert empty.key not in registry
    assert missing.score(client, 1) is None
    assert empty.score(client, 1) is None
    assert list(missing.iter(client)) == []
    assert list(empty.iter(client)) == []
    missing.drop(client)
    empty.drop(client)


def test_async_ordered_set_index_swap_detaches_data() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        index = build_async_ordered_set_index(
            "async_swap_leaderboard",
            member_type=int,
            serializer=IntSerializer(),
            storage=AsyncRedisOrderedSetStorage(),
        )
        try:
            await index.add(client, 2, 2.0)
            await index.add(client, 1, 1.0)
            snapshot = await index.swap(client)
            registry = get_registry(AsyncRedis)
            assert registry.get("async_swap_leaderboard") is index
            assert snapshot is not index
            assert snapshot.key not in registry
            assert await index.score(client, 1) is None
            assert await snapshot.score(client, 1) == 1.0
            assert [item async for item in snapshot.iter(client)] == [(1, 1.0), (2, 2.0)]
            await index.add(client, 3, 3.0)
            assert await index.score(client, 3) == 3.0
            assert await snapshot.score(client, 3) is None
            assert [item async for item in snapshot.iter(client)] == [(1, 1.0), (2, 2.0)]
            await snapshot.drop(client)
            assert registry.get("async_swap_leaderboard") is index
            assert await index.score(client, 3) == 3.0
            assert await snapshot.score(client, 1) is None

            missing = build_async_ordered_set_index(
                "async_swap_leaderboard_missing",
                member_type=int,
                serializer=IntSerializer(),
                storage=AsyncRedisOrderedSetStorage(),
            )
            empty = await missing.swap(client)
            assert registry.get("async_swap_leaderboard_missing") is missing
            assert await missing.score(client, 1) is None
            assert await empty.score(client, 1) is None
            assert [item async for item in missing.iter(client)] == []
            assert [item async for item in empty.iter(client)] == []
            await missing.drop(client)
            await empty.drop(client)
        finally:
            await client.aclose()

    asyncio.run(scenario())
