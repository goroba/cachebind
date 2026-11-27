import asyncio
from collections.abc import Mapping, Sequence

import fakeredis
import pytest

from cachebind import (
    AsyncLeasableKeyValueIndex,
    IntSerializer,
    KeyValueIndex,
    LeasableKeyValueIndex,
    build_async_key_value_index,
    build_key_value_index,
)
from cachebind.backends.redis.lease import lease_key
from cachebind.storage import AsyncRedisHashStorage, RedisHashStorage
from cachebind.storage.key_value.storage import KeyValueStorage
from cachebind.storage.leaseable import AsyncLeasableKeyValueStorage, LeasableKeyValueStorage


class LeasableMemoryStorage(
    KeyValueStorage[object, str, str],
    LeasableKeyValueStorage[object],
):
    def __init__(self) -> None:
        self.data: dict[tuple[str, str], str] = {}
        self.leases: dict[tuple[str, str], str] = {}

    def get(self, client: object, name: str, field: str) -> str | None:
        return self.data.get((name, field))

    def set(
        self, client: object, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        self.data[(name, field)] = value

    def delete(self, client: object, name: str, field: str) -> None:
        self.data.pop((name, field), None)

    def mdelete(self, client: object, name: str, fields: Sequence[str]) -> None:
        for field in fields:
            self.delete(client, name, field)

    def exists(self, client: object, name: str, field: str) -> bool:
        return (name, field) in self.data

    def mget(self, client: object, name: str, fields: Sequence[str]) -> list[str | None]:
        return [self.get(client, name, field) for field in fields]

    def mset(
        self, client: object, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        for field, value in items.items():
            self.set(client, name, field, value, ttl=ttl)

    def try_acquire_lease(
        self,
        client: object,
        name: str,
        field: str,
        *,
        token: str,
        lease_ttl: int,
    ) -> bool:
        del lease_ttl
        if self.exists(client, name, field):
            return False
        slot = (name, field)
        if slot in self.leases:
            return False
        self.leases[slot] = token
        return True

    def release_lease(
        self, client: object, name: str, field: str, *, token: str
    ) -> None:
        del client
        slot = (name, field)
        if self.leases.get(slot) == token:
            del self.leases[slot]


def test_sync_lease_get_hit_miss_loser_and_exception() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisHashStorage()
    index = build_key_value_index(
        "users_lease_sync",
        id_type=int,
        model_type=int,
        serializer=IntSerializer(),
        storage=storage,
    )
    assert isinstance(index, LeasableKeyValueIndex)

    index.set(client, 1, 100)
    calls = 0

    def callback() -> int:
        nonlocal calls
        calls += 1
        return 999

    assert index.lease_get(client, 1, callback, lease_ttl=30) == 100
    assert calls == 0

    calls = 0
    assert index.lease_get(client, 2, lambda: 42, lease_ttl=30, ttl=60) == 42
    assert calls == 0
    assert index.get(client, 2) == 42
    assert client.get(lease_key("users_lease_sync", "2")) is None

    client.set(lease_key("users_lease_sync", "3"), "held", nx=True, ex=30)
    assert index.lease_get(client, 3, lambda: 3, lease_ttl=30) is None

    def explode() -> int:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        index.lease_get(client, 4, explode, lease_ttl=30)
    assert client.get(lease_key("users_lease_sync", "4")) is None


def test_async_lease_get_fills_cache() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        index = build_async_key_value_index(
            "users_async_lease",
            id_type=int,
            model_type=int,
            serializer=IntSerializer(),
            storage=AsyncRedisHashStorage(),
        )
        assert isinstance(index, AsyncLeasableKeyValueIndex)

        async def load() -> int:
            await asyncio.sleep(0)
            return 7

        value = await index.lease_get(client, 9, load, lease_ttl=20, ttl=10)
        assert value == 7
        assert await index.get(client, 9) == 7

    asyncio.run(scenario())


def test_memory_storage_lease_get() -> None:
    mem_storage = LeasableMemoryStorage()
    assert isinstance(mem_storage, LeasableKeyValueStorage)

    class MemClient:
        pass

    class MemIndex(KeyValueIndex):
        identifier = int
        model = int
        serializer = IntSerializer()
        key = "mem"
        client_type = MemClient
        storage = mem_storage

    index = MemIndex()
    client = MemClient()
    assert index.lease_get(client, 1, lambda: 5, lease_ttl=10) == 5
    assert index.get(client, 1) == 5
    assert mem_storage.leases == {}