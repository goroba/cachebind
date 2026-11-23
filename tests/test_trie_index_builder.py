import asyncio
from collections.abc import Sequence
from uuid import uuid4

import pytest
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from cachebind import (
    AsyncDroppableIndex,
    AsyncReplaceableIndex,
    AsyncSnapshotableIndex,
    AsyncTrieIndex,
    DroppableIndex,
    IntSerializer,
    IterableIndex,
    ReplaceableIndex,
    SnapshotableIndex,
    TrieIndex,
    build_async_ordered_set_index,
    build_async_trie_index,
    build_ordered_set_index,
    build_trie_index,
    get_registry,
)
from cachebind.serializers.datetime_serializer import DatetimeSerializer
from cachebind.serializers.serializer import Serializer
from cachebind.storage.ordered_sets.async_redis_ordered_set_storage import (
    AsyncRedisOrderedSetStorage,
)
from cachebind.storage.ordered_sets.redis_ordered_set_storage import RedisOrderedSetStorage
from cachebind.storage.tries.async_storage import AsyncTrieStorage
from cachebind.storage.tries.redis_trie_storage import RedisTrieStorage
from cachebind.storage.tries.storage import TrieStorage
from test_redis_trie_storage import Scripted


class Spy:
    pass


class AsyncSpy:
    pass


class TrieData:
    def __init__(self) -> None:
        self.data: dict[str, dict[str, tuple[float, str]]] = {}
        self.calls: list[str] = []
        self.last_fuzzy: bool | None = None
        self.last_limit: int | None = None

    def add(
        self,
        name: str,
        string: str,
        score: float,
        payload: str,
        *,
        increment: bool = False,
    ) -> None:
        self.calls.append("add")
        bucket = self.data.setdefault(name, {})
        if increment and string in bucket:
            score = bucket[string][0] + score
        bucket[string] = (score, payload)

    def madd(
        self,
        name: str,
        entries: Sequence[tuple[str, float, str]],
        *,
        increment: bool = False,
    ) -> None:
        self.calls.append("madd")
        for string, score, payload in entries:
            bucket = self.data.setdefault(name, {})
            if increment and string in bucket:
                score = bucket[string][0] + score
            bucket[string] = (score, payload)

    def remove(self, name: str, string: str) -> None:
        self.calls.append("remove")
        self.data.get(name, {}).pop(string, None)

    def mremove(self, name: str, strings: Sequence[str]) -> None:
        self.calls.append("mremove")
        bucket = self.data.get(name, {})
        for string in strings:
            bucket.pop(string, None)

    def search(self, name: str, prefix: str, *, fuzzy: bool, limit: int) -> list[str]:
        self.calls.append("search")
        self.last_fuzzy = fuzzy
        self.last_limit = limit
        bucket = self.data.get(name, {})
        ranked = sorted(
            (
                (string, score, payload)
                for string, (score, payload) in bucket.items()
                if string.startswith(prefix)
            ),
            key=lambda item: (-item[1], item[0]),
        )
        return [payload for _string, _score, payload in ranked[:limit]]

    def length(self, name: str) -> int:
        self.calls.append("length")
        return len(self.data.get(name, {}))

    def snapshot(self, name: str) -> str:
        self.calls.append("snapshot")
        renamed = f"{name}:swap:{uuid4().hex}"
        self.data[renamed] = self.data.pop(name, {})
        return renamed

    def drop(self, name: str) -> None:
        self.calls.append("drop")
        self.data.pop(name, None)

    def replace(self, source: str, dest: str) -> None:
        self.calls.append("replace")
        if source == dest:
            raise ValueError("source and dest must differ")
        self.data[dest] = self.data.pop(source, {})


class MemoryTrie(TrieStorage[Spy, str]):
    def __init__(self, data: TrieData | None = None) -> None:
        self.data = data if data is not None else TrieData()

    def add(
        self,
        client: Spy,
        name: str,
        string: str,
        score: float,
        payload: str,
        *,
        increment: bool = False,
    ) -> None:
        self.data.add(name, string, score, payload, increment=increment)

    def madd(
        self,
        client: Spy,
        name: str,
        entries: Sequence[tuple[str, float, str]],
        *,
        increment: bool = False,
    ) -> None:
        self.data.madd(name, entries, increment=increment)

    def remove(self, client: Spy, name: str, string: str) -> None:
        self.data.remove(name, string)

    def mremove(self, client: Spy, name: str, strings: Sequence[str]) -> None:
        self.data.mremove(name, strings)

    def search(
        self,
        client: Spy,
        name: str,
        prefix: str,
        *,
        fuzzy: bool = False,
        limit: int = 10,
    ) -> list[str]:
        return self.data.search(name, prefix, fuzzy=fuzzy, limit=limit)

    def length(self, client: Spy, name: str) -> int:
        return self.data.length(name)

    def snapshot(self, client: Spy, name: str) -> str:
        return self.data.snapshot(name)

    def replace(self, client: Spy, source: str, dest: str) -> None:
        self.data.replace(source, dest)

    def drop(self, client: Spy, name: str) -> None:
        self.data.drop(name)


class AsyncMemoryTrie(AsyncTrieStorage[AsyncSpy, str]):
    def __init__(self, data: TrieData | None = None) -> None:
        self.data = data if data is not None else TrieData()

    async def add(
        self,
        client: AsyncSpy,
        name: str,
        string: str,
        score: float,
        payload: str,
        *,
        increment: bool = False,
    ) -> None:
        self.data.add(name, string, score, payload, increment=increment)

    async def madd(
        self,
        client: AsyncSpy,
        name: str,
        entries: Sequence[tuple[str, float, str]],
        *,
        increment: bool = False,
    ) -> None:
        self.data.madd(name, entries, increment=increment)

    async def remove(self, client: AsyncSpy, name: str, string: str) -> None:
        self.data.remove(name, string)

    async def mremove(self, client: AsyncSpy, name: str, strings: Sequence[str]) -> None:
        self.data.mremove(name, strings)

    async def search(
        self,
        client: AsyncSpy,
        name: str,
        prefix: str,
        *,
        fuzzy: bool = False,
        limit: int = 10,
    ) -> list[str]:
        return self.data.search(name, prefix, fuzzy=fuzzy, limit=limit)

    async def length(self, client: AsyncSpy, name: str) -> int:
        return self.data.length(name)

    async def snapshot(self, client: AsyncSpy, name: str) -> str:
        return self.data.snapshot(name)

    async def replace(self, client: AsyncSpy, source: str, dest: str) -> None:
        self.data.replace(source, dest)

    async def drop(self, client: AsyncSpy, name: str) -> None:
        self.data.drop(name)


class CountingSerializer(Serializer[int, str]):
    def __init__(self) -> None:
        self.batches = 0

    def serialize(self, value: int) -> str:
        return str(value)

    def deserialize(self, value: str) -> int:
        raise AssertionError(value)

    def mserialize(self, values: Sequence[int]) -> list[str]:
        return [str(value) for value in values]

    def mdeserialize(self, values: Sequence[str]) -> list[int]:
        self.batches += 1
        return [int(value) for value in values]


class BytesTrie(TrieStorage[Spy, bytes]):
    pass


def test_trie_builders_are_public() -> None:
    import cachebind

    assert cachebind.build_trie_index is build_trie_index
    assert cachebind.build_async_trie_index is build_async_trie_index


def test_trie_search_uses_serializer_kwarg() -> None:
    storage = MemoryTrie()
    default = CountingSerializer()
    override = CountingSerializer()
    index = build_trie_index(
        "trie_serializer_kwarg",
        member_type=int,
        serializer=default,
        storage=storage,
    )
    client = Spy()
    index.add(client, "Paris", 1, 900.0)
    assert index.search(client, "P", serializer=override) == [1]
    assert override.batches == 1
    assert default.batches == 0


def test_sync_trie_index_round_trip() -> None:
    storage = MemoryTrie()
    serializer = CountingSerializer()
    index = build_trie_index(
        "trie_cities",
        member_type=int,
        serializer=serializer,
        storage=storage,
    )
    assert index is get_registry(Spy).get("trie_cities")
    assert isinstance(index, TrieIndex)
    assert index.member is int
    assert index.key == "trie_cities"
    assert index.storage is storage
    assert index.serializer is serializer

    client = Spy()
    assert index.length(client) == 0
    index.remove(client, "Paris")
    index.add(client, "Paris", 1, 900.0)
    index.add(client, "Paris", 1, 910.0)
    index.add(client, "Prague", 2, 700.0)
    index.add(client, "Lyon", 4, 400.0)
    index.madd(client, [("Padua", 3, 200.0), ("Lisbon", 5, 300.0), ("Padua", 3, 250.0)])
    index.add(client, "Lyon", 4, 25.0, increment=True)

    assert index.length(client) == 5
    assert index.search(client, "P") == [1, 2, 3]
    assert index.search(client, "Pa", limit=1) == [1]
    assert index.search(client, "L") == [4, 5]
    assert serializer.batches == 3
    assert storage.data.last_fuzzy is False
    assert storage.data.last_limit == 10

    index.search(client, "P", fuzzy=True, limit=2)
    assert storage.data.last_fuzzy is True
    assert storage.data.last_limit == 2

    index.mremove(client, ["Lyon", "Missing"])
    assert index.search(client, "L") == [5]
    index.remove(client, "Lisbon")
    assert index.length(client) == 3


def test_async_trie_index_round_trip() -> None:
    async def scenario() -> None:
        storage = AsyncMemoryTrie()
        serializer = CountingSerializer()
        index = build_async_trie_index(
            "async_trie_cities",
            member_type=int,
            serializer=serializer,
            storage=storage,
        )
        assert index is get_registry(AsyncSpy).get("async_trie_cities")
        assert isinstance(index, AsyncTrieIndex)
        client = AsyncSpy()
        assert await index.length(client) == 0
        await index.add(client, "Paris", 1, 900.0)
        await index.madd(client, [("Prague", 2, 700.0), ("Padua", 3, 200.0)])
        assert await index.search(client, "P") == [1, 2, 3]
        assert serializer.batches == 1
        await index.remove(client, "Padua")
        assert await index.length(client) == 2

    asyncio.run(scenario())


def test_trie_search_deserializes_redis_payloads() -> None:
    client = Scripted(replies=[1, ["Paris", "1", "Prague", "2"]])
    serializer = CountingSerializer()
    index = build_trie_index(
        "trie_redis_payloads",
        member_type=int,
        serializer=serializer,
        storage=RedisTrieStorage(),
    )
    assert index.client_type is Redis
    index.add(client, "Paris", 1, 900.0)  # type: ignore[arg-type]
    assert index.search(client, "P") == [1, 2]  # type: ignore[arg-type]
    assert serializer.batches == 1
    assert client.commands == [
        ("FT.SUGADD", "trie_redis_payloads", "Paris", 900.0, "PAYLOAD", "1"),
        ("FT.SUGGET", "trie_redis_payloads", "P", "MAX", 10, "WITHPAYLOADS"),
    ]


def test_duplicate_trie_key() -> None:
    build_trie_index(
        "trie_once",
        member_type=int,
        serializer=IntSerializer(),
        storage=MemoryTrie(),
    )
    with pytest.raises(ValueError):
        build_trie_index(
            "trie_once",
            member_type=int,
            serializer=IntSerializer(),
            storage=MemoryTrie(),
        )


def test_redis_and_async_redis_can_share_a_trie_key() -> None:
    from cachebind.storage.tries.async_redis_trie_storage import AsyncRedisTrieStorage
    from cachebind.storage.tries.redis_trie_storage import RedisTrieStorage

    sync = build_trie_index(
        "shared_trie_key",
        member_type=int,
        serializer=IntSerializer(),
        storage=RedisTrieStorage(),
    )
    async_index = build_async_trie_index(
        "shared_trie_key",
        member_type=int,
        serializer=IntSerializer(),
        storage=AsyncRedisTrieStorage(),
    )
    assert get_registry(Redis).get("shared_trie_key") is sync
    assert get_registry(AsyncRedis).get("shared_trie_key") is async_index


def test_same_client_ordered_set_and_trie_indexes_share_a_registry() -> None:
    from cachebind.storage.tries.redis_trie_storage import RedisTrieStorage

    trie = build_trie_index(
        "registry_trie",
        member_type=int,
        serializer=IntSerializer(),
        storage=RedisTrieStorage(),
    )
    ordered = build_ordered_set_index(
        "registry_trie_ordered",
        member_type=int,
        serializer=IntSerializer(),
        storage=RedisOrderedSetStorage(),
    )
    registry = get_registry(Redis)
    assert registry.get("registry_trie") is trie
    assert registry.get("registry_trie_ordered") is ordered


def test_same_async_client_ordered_set_and_trie_indexes_share_a_registry() -> None:
    from cachebind.storage.tries.async_redis_trie_storage import AsyncRedisTrieStorage

    trie = build_async_trie_index(
        "async_registry_trie",
        member_type=int,
        serializer=IntSerializer(),
        storage=AsyncRedisTrieStorage(),
    )
    ordered = build_async_ordered_set_index(
        "async_registry_trie_ordered",
        member_type=int,
        serializer=IntSerializer(),
        storage=AsyncRedisOrderedSetStorage(),
    )
    registry = get_registry(AsyncRedis)
    assert registry.get("async_registry_trie") is trie
    assert registry.get("async_registry_trie_ordered") is ordered


def test_rejected_trie_indexes_do_not_register() -> None:
    cases: tuple[tuple[str, object], ...] = (
        (
            "trie_member_mismatch",
            lambda: build_trie_index(
                "trie_member_mismatch",
                member_type=int,
                serializer=DatetimeSerializer(),
                storage=MemoryTrie(),
            ),
        ),
        (
            "trie_storage_mismatch",
            lambda: build_trie_index(
                "trie_storage_mismatch",
                member_type=int,
                serializer=IntSerializer(),
                storage=BytesTrie(),
            ),
        ),
        (
            "trie_sync_storage",
            lambda: build_async_trie_index(
                "trie_sync_storage",
                member_type=int,
                serializer=IntSerializer(),
                storage=MemoryTrie(),
            ),
        ),
    )
    for key, build in cases:
        with pytest.raises(TypeError):
            build()
        for client in (Redis, AsyncRedis, Spy, AsyncSpy):
            try:
                registry = get_registry(client)
            except KeyError:
                continue
            assert key not in registry


def test_empty_trie_batches_do_not_call_storage() -> None:
    storage = MemoryTrie()
    index = build_trie_index(
        "trie_empty_batches",
        member_type=int,
        serializer=IntSerializer(),
        storage=storage,
    )
    client = Spy()
    index.madd(client, [])
    index.mremove(client, [])
    with pytest.raises(ValueError, match="trie limit"):
        index.search(client, "P", limit=0)
    assert storage.data.calls == []


def test_async_empty_trie_batches_do_not_call_storage() -> None:
    storage = AsyncMemoryTrie()
    index = build_async_trie_index(
        "async_trie_empty_batches",
        member_type=int,
        serializer=IntSerializer(),
        storage=storage,
    )

    async def scenario() -> None:
        await index.madd(AsyncSpy(), [])
        await index.mremove(AsyncSpy(), [])
        with pytest.raises(ValueError, match="trie limit"):
            await index.search(AsyncSpy(), "P", limit=True)  # type: ignore[arg-type]

    asyncio.run(scenario())
    assert storage.data.calls == []


def test_trie_index_snapshot_detaches_data() -> None:
    client = Spy()
    index = build_trie_index(
        "swap_cities",
        member_type=int,
        serializer=IntSerializer(),
        storage=MemoryTrie(),
    )
    assert isinstance(index, SnapshotableIndex)
    assert isinstance(index, DroppableIndex)
    assert not isinstance(index, IterableIndex)
    index.add(client, "Paris", 1, 900.0)
    index.add(client, "Lyon", 4, 400.0)
    with index.snapshot(client) as snapshot:
        registry = get_registry(Spy)
        assert registry.get("swap_cities") is index
        assert snapshot is not index
        assert snapshot.key.startswith("swap_cities:swap:")
        assert snapshot.key not in registry
        assert index.length(client) == 0
        assert snapshot.search(client, "P") == [1]
        index.add(client, "Prague", 2, 700.0)
        assert snapshot.search(client, "P") == [1]
        assert index.search(client, "P") == [2]
    assert registry.get("swap_cities") is index
    assert snapshot.length(client) == 0
    assert index.search(client, "P") == [2]

    missing = build_trie_index(
        "swap_cities_missing",
        member_type=int,
        serializer=IntSerializer(),
        storage=MemoryTrie(),
    )
    with missing.snapshot(client) as empty:
        assert empty.key not in registry
        assert missing.length(client) == 0
        assert empty.length(client) == 0
    missing.drop(client)


def test_async_trie_index_snapshot_detaches_data() -> None:
    async def scenario() -> None:
        client = AsyncSpy()
        index = build_async_trie_index(
            "async_swap_cities",
            member_type=int,
            serializer=IntSerializer(),
            storage=AsyncMemoryTrie(),
        )
        assert isinstance(index, AsyncSnapshotableIndex)
        assert isinstance(index, AsyncDroppableIndex)
        assert not isinstance(index, IterableIndex)
        await index.add(client, "Paris", 1, 900.0)
        async with index.snapshot(client) as snapshot:
            registry = get_registry(AsyncSpy)
            assert registry.get("async_swap_cities") is index
            assert snapshot.key not in registry
            assert await index.length(client) == 0
            assert await snapshot.search(client, "P") == [1]
        assert await snapshot.length(client) == 0
        assert registry.get("async_swap_cities") is index

    asyncio.run(scenario())


def test_trie_index_replace_publishes_staging() -> None:
    client = Spy()
    index = build_trie_index(
        "replace_cities",
        member_type=int,
        serializer=IntSerializer(),
        storage=MemoryTrie(),
    )
    assert isinstance(index, ReplaceableIndex)
    index.add(client, "Old", 99, 99.0)
    with index.replace(client) as staging:
        assert index.length(client) == 1
        staging.add(client, "Paris", 1, 900.0)
    assert get_registry(Spy).get("replace_cities") is index
    assert index.search(client, "P") == [1]
    assert index.length(client) == 1


def test_trie_index_replace_failure_preserves_live() -> None:
    client = Spy()
    index = build_trie_index(
        "replace_cities_fail",
        member_type=int,
        serializer=IntSerializer(),
        storage=MemoryTrie(),
    )
    index.add(client, "Old", 99, 99.0)
    with pytest.raises(RuntimeError):
        with index.replace(client) as staging:
            staging.add(client, "Paris", 1, 900.0)
            raise RuntimeError
    assert index.length(client) == 1


def test_async_trie_index_replace_publishes_staging() -> None:
    async def scenario() -> None:
        client = AsyncSpy()
        index = build_async_trie_index(
            "async_replace_cities",
            member_type=int,
            serializer=IntSerializer(),
            storage=AsyncMemoryTrie(),
        )
        assert isinstance(index, AsyncReplaceableIndex)
        await index.add(client, "Old", 99, 99.0)
        async with index.replace(client) as staging:
            await staging.add(client, "Paris", 1, 900.0)
        assert await index.search(client, "P") == [1]

    asyncio.run(scenario())
