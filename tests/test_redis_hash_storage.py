import asyncio
from collections.abc import Sequence

import fakeredis

from cachebind.storage.key_value.async_redis_hash_storage import AsyncRedisHashStorage
from cachebind.storage.key_value.async_storage import AsyncKeyValueStorage
from cachebind.storage import (
    AsyncDroppableStorage,
    AsyncIterableStorage,
    AsyncReplaceableStorage,
    AsyncSnapshotableStorage,
    DroppableStorage,
    IterableStorage,
    ReplaceableStorage,
    SnapshotableStorage,
)
from cachebind.storage.key_value.redis_hash_storage import RedisHashStorage
from cachebind.storage.key_value.storage import KeyValueStorage


class _HashSpy:
    def __init__(self) -> None:
        self.hmget_called = False
        self.hset_called = False
        self.hdel_called = False

    def hmget(self, name: str, keys: Sequence[str]) -> list[str | None]:
        self.hmget_called = True
        return [None for _ in keys]

    def hset(
        self,
        name: str,
        key: str | None = None,
        value: str | None = None,
        mapping: dict[str, str] | None = None,
    ) -> int:
        self.hset_called = True
        return 0

    def hdel(self, name: str, *keys: str) -> int:
        self.hdel_called = True
        return 0


def test_sync_hash_storage_round_trip() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisHashStorage()
    assert isinstance(storage, KeyValueStorage)
    assert isinstance(storage, SnapshotableStorage)
    assert isinstance(storage, ReplaceableStorage)
    assert isinstance(storage, DroppableStorage)
    assert isinstance(storage, IterableStorage)

    assert storage.get(client, "users", "1") is None
    assert storage.exists(client, "users", "1") is False
    storage.delete(client, "users", "1")

    storage.set(client, "users", "1", "10", ttl=30)
    assert storage.get(client, "users", "1") == "10"
    assert storage.exists(client, "users", "1") is True
    assert 0 < client.httl("users", "1")[0] <= 30

    storage.mset(client, "users", {"2": "20", "3": "30"})
    assert storage.mget(client, "users", ["2", "1", "2", "9"]) == ["20", "10", "20", None]
    assert client.httl("users", "2")[0] == -1

    storage.mset(client, "users", {"2": "21", "4": "40"}, ttl=5)
    assert storage.get(client, "users", "2") == "21"
    assert 0 < client.httl("users", "2")[0] <= 5
    assert 0 < client.httl("users", "4")[0] <= 5
    assert client.httl("users", "1")[0] > 5

    storage.delete(client, "users", "1")
    assert storage.get(client, "users", "1") is None
    assert storage.exists(client, "users", "1") is False

    storage.mdelete(client, "users", ["2", "missing"])
    assert storage.get(client, "users", "2") is None
    assert storage.exists(client, "users", "2") is False
    assert storage.get(client, "users", "4") == "40"


def test_sync_hash_storage_empty_batches_do_not_call_redis() -> None:
    spy = _HashSpy()
    storage = RedisHashStorage()

    assert storage.mget(spy, "users", []) == []  # type: ignore[arg-type]
    storage.mset(spy, "users", {})  # type: ignore[arg-type]
    storage.mdelete(spy, "users", [])  # type: ignore[arg-type]
    assert spy.hmget_called is False
    assert spy.hset_called is False
    assert spy.hdel_called is False


def test_sync_hash_storage_decodes_bytes() -> None:
    client = fakeredis.FakeRedis(decode_responses=False)
    storage = RedisHashStorage()

    storage.set(client, "users", "1", "10")
    assert client.hget("users", "1") == b"10"
    assert storage.get(client, "users", "1") == "10"
    assert storage.mget(client, "users", ["1", "2"]) == ["10", None]


def test_async_hash_storage_round_trip() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        storage = AsyncRedisHashStorage()
        assert isinstance(storage, AsyncKeyValueStorage)
        assert isinstance(storage, AsyncSnapshotableStorage)
        assert isinstance(storage, AsyncIterableStorage)
        try:
            assert await storage.get(client, "users", "1") is None
            assert await storage.exists(client, "users", "1") is False
            await storage.delete(client, "users", "1")

            await storage.set(client, "users", "1", "10", ttl=30)
            assert await storage.get(client, "users", "1") == "10"
            assert await storage.exists(client, "users", "1") is True
            assert 0 < (await client.httl("users", "1"))[0] <= 30

            await storage.mset(client, "users", {"2": "20", "3": "30"})
            assert await storage.mget(client, "users", ["2", "1", "2", "9"]) == [
                "20",
                "10",
                "20",
                None,
            ]
            assert (await client.httl("users", "2"))[0] == -1

            await storage.mset(client, "users", {"2": "21", "4": "40"}, ttl=5)
            assert await storage.get(client, "users", "2") == "21"
            assert 0 < (await client.httl("users", "2"))[0] <= 5
            assert 0 < (await client.httl("users", "4"))[0] <= 5
            assert (await client.httl("users", "1"))[0] > 5

            await storage.delete(client, "users", "1")
            assert await storage.get(client, "users", "1") is None
            assert await storage.exists(client, "users", "1") is False

            await storage.mdelete(client, "users", ["2", "missing"])
            assert await storage.get(client, "users", "2") is None
            assert await storage.exists(client, "users", "2") is False
            assert await storage.get(client, "users", "4") == "40"
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_async_hash_storage_empty_batches_do_not_call_redis() -> None:
    spy = _HashSpy()
    storage = AsyncRedisHashStorage()

    async def scenario() -> None:
        assert await storage.mget(spy, "users", []) == []  # type: ignore[arg-type]
        await storage.mset(spy, "users", {})  # type: ignore[arg-type]
        await storage.mdelete(spy, "users", [])  # type: ignore[arg-type]

    asyncio.run(scenario())
    assert spy.hmget_called is False
    assert spy.hset_called is False
    assert spy.hdel_called is False


def test_async_hash_storage_decodes_bytes() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=False)
        storage = AsyncRedisHashStorage()
        try:
            await storage.set(client, "users", "1", "10")
            assert await client.hget("users", "1") == b"10"
            assert await storage.get(client, "users", "1") == "10"
            assert await storage.mget(client, "users", ["1", "2"]) == ["10", None]
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_sync_hash_storage_iter_pages_every_field() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisHashStorage()
    storage.mset(client, "scan_users", {"1": "a", "2": "b", "3": "c"})
    assert set(storage.iter(client, "scan_users", count=2)) == {("1", "a"), ("2", "b"), ("3", "c")}
    assert list(storage.iter(client, "scan_missing")) == []


def test_async_hash_storage_iter_pages_every_field() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        storage = AsyncRedisHashStorage()
        try:
            await storage.mset(client, "async_scan_users", {"1": "a", "2": "b", "3": "c"})
            found = {item async for item in storage.iter(client, "async_scan_users", count=2)}
            assert found == {("1", "a"), ("2", "b"), ("3", "c")}
            assert [item async for item in storage.iter(client, "async_scan_missing")] == []
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_sync_hash_storage_copy_clones_absent_dest() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisHashStorage()
    storage.mset(client, "source", {"1": "a", "2": "b", "3": "c"})

    storage.copy(client, "source", "dest")
    assert set(storage.iter(client, "dest", count=2)) == {("1", "a"), ("2", "b"), ("3", "c")}


def test_sync_hash_storage_copy_overlays_existing_dest() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisHashStorage()
    storage.mset(client, "source", {"1": "new", "2": "b"})
    storage.mset(client, "dest", {"1": "old", "9": "keep"})

    storage.copy(client, "source", "dest")
    assert storage.mget(client, "dest", ["1", "2", "9"]) == ["new", "b", "keep"]


def test_sync_hash_storage_merge_overwrites_dest_fields() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisHashStorage()
    storage.mset(client, "source", {"1": "staging", "2": "b"})
    storage.mset(client, "dest", {"1": "live", "3": "c"})

    storage.merge(client, "source", "dest")
    assert storage.mget(client, "dest", ["1", "2", "3"]) == ["staging", "b", "c"]


def test_sync_hash_storage_copy_missing_source_leaves_dest() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisHashStorage()
    storage.mset(client, "dest", {"1": "keep"})

    storage.copy(client, "missing", "dest")
    assert storage.get(client, "dest", "1") == "keep"


def test_async_hash_storage_copy_and_merge() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        storage = AsyncRedisHashStorage()
        try:
            await storage.mset(client, "source", {"1": "a", "2": "b", "3": "c"})
            await storage.copy(client, "source", "dest")
            found = {item async for item in storage.iter(client, "dest", count=2)}
            assert found == {("1", "a"), ("2", "b"), ("3", "c")}

            await storage.mset(client, "staging", {"2": "new"})
            await storage.merge(client, "staging", "dest")
            assert await storage.mget(client, "dest", ["1", "2", "3"]) == ["a", "new", "c"]

            await storage.copy(client, "missing", "dest")
            assert await storage.mget(client, "dest", ["1", "2", "3"]) == ["a", "new", "c"]
        finally:
            await client.aclose()

    asyncio.run(scenario())
