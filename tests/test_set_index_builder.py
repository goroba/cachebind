import asyncio
from collections.abc import Sequence

import fakeredis
import pytest
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from cachebind import (
    AsyncIterableIndex,
    AsyncSetIndex,
    AsyncSnapshotableIndex,
    DroppableIndex,
    IntSerializer,
    IterableIndex,
    SetIndex,
    SnapshotableIndex,
    build_async_key_value_index,
    build_async_set_index,
    build_key_value_index,
    build_set_index,
    get_registry,
)
from cachebind.serializers.datetime_serializer import DatetimeSerializer
from cachebind.storage.key_value.async_redis_string_storage import AsyncRedisStringStorage
from cachebind.storage.key_value.redis_string_storage import RedisStringStorage
from cachebind.storage.sets.async_redis_set_storage import AsyncRedisSetStorage
from cachebind.storage.sets.async_storage import AsyncSetStorage
from cachebind.storage.sets.redis_set_storage import RedisSetStorage
from cachebind.storage.sets.storage import SetStorage


class Spy:
    pass


class SpySet(SetStorage[Spy, str]):
    def __init__(self) -> None:
        self.called = False

    def madd(self, client: Spy, name: str, members: Sequence[str]) -> None:
        self.called = True

    def mremove(self, client: Spy, name: str, members: Sequence[str]) -> None:
        self.called = True


class AsyncSpy:
    pass


class AsyncSpySet(AsyncSetStorage[AsyncSpy, str]):
    def __init__(self) -> None:
        self.called = False

    async def madd(self, client: AsyncSpy, name: str, members: Sequence[str]) -> None:
        self.called = True

    async def mremove(self, client: AsyncSpy, name: str, members: Sequence[str]) -> None:
        self.called = True


class BytesSet(SetStorage[Spy, bytes]):
    pass


def test_set_builders_are_public() -> None:
    import cachebind

    assert cachebind.build_set_index is build_set_index
    assert cachebind.build_async_set_index is build_async_set_index


def test_sync_set_index_round_trip() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisSetStorage()
    index = build_set_index(
        "active_users",
        member_type=int,
        serializer=IntSerializer(),
        storage=storage,
    )
    assert index is get_registry(Redis).get("active_users")
    assert index.client_type is Redis
    assert isinstance(index, SetIndex)
    assert index.member is int
    assert index.key == "active_users"
    assert index.storage is storage
    assert isinstance(index.serializer, IntSerializer)

    assert index.contains(client, 1) is False
    index.remove(client, 1)
    index.add(client, 1)
    index.add(client, 1)
    assert index.contains(client, 1) is True
    assert client.sismember("active_users", "1") == 1

    index.madd(client, [3, 2])
    assert index.contains(client, 2) is True
    assert index.contains(client, 3) is True
    assert client.smembers("active_users") == {"1", "2", "3"}

    index.mremove(client, [1, 3])
    assert index.contains(client, 1) is False
    assert index.contains(client, 3) is False
    assert index.contains(client, 2) is True
    index.remove(client, 2)
    assert index.contains(client, 2) is False


def test_async_set_index_round_trip() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        try:
            storage = AsyncRedisSetStorage()
            index = build_async_set_index(
                "async_active_users",
                member_type=int,
                serializer=IntSerializer(),
                storage=storage,
            )
            assert index is get_registry(AsyncRedis).get("async_active_users")
            assert index.client_type is AsyncRedis
            assert isinstance(index, AsyncSetIndex)
            assert index.member is int
            assert index.storage is storage

            assert await index.contains(client, 1) is False
            await index.remove(client, 1)
            await index.add(client, 1)
            await index.add(client, 1)
            assert await index.contains(client, 1) is True
            assert await client.sismember("async_active_users", "1") == 1

            await index.madd(client, [3, 2])
            assert await index.contains(client, 2) is True
            assert await index.contains(client, 3) is True
            assert await client.smembers("async_active_users") == {"1", "2", "3"}

            await index.mremove(client, [1, 3])
            assert await index.contains(client, 1) is False
            assert await index.contains(client, 2) is True
            await index.remove(client, 2)
            assert await index.contains(client, 2) is False
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_duplicate_set_key() -> None:
    first = build_set_index(
        "set_duplicate",
        member_type=int,
        serializer=IntSerializer(),
        storage=RedisSetStorage(),
    )
    with pytest.raises(ValueError):
        build_set_index(
            "set_duplicate",
            member_type=int,
            serializer=IntSerializer(),
            storage=RedisSetStorage(),
        )
    assert get_registry(Redis).get("set_duplicate") is first


def test_redis_and_async_redis_can_share_an_index_key() -> None:
    sync = build_set_index(
        "set_sync_async",
        member_type=int,
        serializer=IntSerializer(),
        storage=RedisSetStorage(),
    )
    async_index = build_async_set_index(
        "set_sync_async",
        member_type=int,
        serializer=IntSerializer(),
        storage=AsyncRedisSetStorage(),
    )
    assert get_registry(Redis).get("set_sync_async") is sync
    assert get_registry(AsyncRedis).get("set_sync_async") is async_index


def test_same_client_key_value_and_set_indexes_share_a_registry() -> None:
    key_value = build_key_value_index(
        "shared_users",
        id_type=int,
        model_type=int,
        serializer=IntSerializer(),
        storage=RedisStringStorage(),
    )
    with pytest.raises(ValueError):
        build_set_index(
            "shared_users",
            member_type=int,
            serializer=IntSerializer(),
            storage=RedisSetStorage(),
        )
    assert get_registry(Redis).get("shared_users") is key_value


def test_same_async_client_key_value_and_set_indexes_share_a_registry() -> None:
    key_value = build_async_key_value_index(
        "async_shared_users",
        id_type=int,
        model_type=int,
        serializer=IntSerializer(),
        storage=AsyncRedisStringStorage(),
    )
    with pytest.raises(ValueError):
        build_async_set_index(
            "async_shared_users",
            member_type=int,
            serializer=IntSerializer(),
            storage=AsyncRedisSetStorage(),
        )
    assert get_registry(AsyncRedis).get("async_shared_users") is key_value


def test_rejected_set_indexes_do_not_register() -> None:
    cases: tuple[tuple[str, object], ...] = (
        (
            "set_member_mismatch",
            lambda: build_set_index(
                "set_member_mismatch",
                member_type=int,
                serializer=DatetimeSerializer(),
                storage=RedisSetStorage(),
            ),
        ),
        (
            "set_storage_mismatch",
            lambda: build_set_index(
                "set_storage_mismatch",
                member_type=int,
                serializer=IntSerializer(),
                storage=BytesSet(),
            ),
        ),
        (
            "set_sync_storage",
            lambda: build_async_set_index(
                "set_sync_storage",
                member_type=int,
                serializer=IntSerializer(),
                storage=SpySet(),
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


def test_empty_set_batches_do_not_call_storage() -> None:
    storage = SpySet()
    index = build_set_index(
        "set_empty_batches",
        member_type=int,
        serializer=IntSerializer(),
        storage=storage,
    )
    client = Spy()
    index.madd(client, [])
    index.mremove(client, [])
    assert storage.called is False


def test_async_empty_set_batches_do_not_call_storage() -> None:
    storage = AsyncSpySet()
    index = build_async_set_index(
        "async_set_empty_batches",
        member_type=int,
        serializer=IntSerializer(),
        storage=storage,
    )
    client = AsyncSpy()

    async def scenario() -> None:
        await index.madd(client, [])
        await index.mremove(client, [])

    asyncio.run(scenario())
    assert storage.called is False


def test_set_index_snapshot_detaches_data() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    index = build_set_index(
        "swap_active_users",
        member_type=int,
        serializer=IntSerializer(),
        storage=RedisSetStorage(),
    )
    assert isinstance(index, SnapshotableIndex)
    assert isinstance(index, DroppableIndex)
    assert isinstance(index, IterableIndex)
    index.add(client, 1)
    snapshot = index.snapshot(client)
    registry = get_registry(Redis)
    assert registry.get("swap_active_users") is index
    assert snapshot is not index
    assert snapshot.key.startswith("swap_active_users:swap:")
    assert snapshot.key not in registry
    assert index.contains(client, 1) is False
    assert snapshot.contains(client, 1) is True
    index.add(client, 2)
    assert index.contains(client, 2) is True
    assert snapshot.contains(client, 2) is False
    assert set(snapshot.iter(client)) == {1}
    snapshot.drop(client)
    assert registry.get("swap_active_users") is index
    assert index.contains(client, 2) is True
    assert snapshot.contains(client, 1) is False

    missing = build_set_index(
        "swap_active_missing",
        member_type=int,
        serializer=IntSerializer(),
        storage=RedisSetStorage(),
    )
    empty = missing.snapshot(client)
    assert registry.get("swap_active_missing") is missing
    assert empty.key not in registry
    assert missing.contains(client, 1) is False
    assert empty.contains(client, 1) is False
    assert list(missing.iter(client)) == []
    assert list(empty.iter(client)) == []
    missing.drop(client)
    empty.drop(client)


def test_async_set_index_snapshot_detaches_data() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        index = build_async_set_index(
            "async_swap_active_users",
            member_type=int,
            serializer=IntSerializer(),
            storage=AsyncRedisSetStorage(),
        )
        assert isinstance(index, AsyncSnapshotableIndex)
        try:
            await index.add(client, 1)
            snapshot = await index.snapshot(client)
            registry = get_registry(AsyncRedis)
            assert registry.get("async_swap_active_users") is index
            assert snapshot is not index
            assert snapshot.key not in registry
            assert await index.contains(client, 1) is False
            assert await snapshot.contains(client, 1) is True
            await index.add(client, 2)
            assert await index.contains(client, 2) is True
            assert await snapshot.contains(client, 2) is False
            assert {member async for member in snapshot.iter(client)} == {1}
            await snapshot.drop(client)
            assert registry.get("async_swap_active_users") is index
            assert await index.contains(client, 2) is True
            assert await snapshot.contains(client, 1) is False

            missing = build_async_set_index(
                "async_swap_active_missing",
                member_type=int,
                serializer=IntSerializer(),
                storage=AsyncRedisSetStorage(),
            )
            empty = await missing.snapshot(client)
            assert registry.get("async_swap_active_missing") is missing
            assert await missing.contains(client, 1) is False
            assert await empty.contains(client, 1) is False
            assert [member async for member in missing.iter(client)] == []
            assert [member async for member in empty.iter(client)] == []
            await missing.drop(client)
            await empty.drop(client)
        finally:
            await client.aclose()

    asyncio.run(scenario())
