import asyncio
from collections.abc import AsyncIterator, Iterator, Mapping, Sequence

import pytest

from cachebind import (
    AsyncDroppableStorage,
    AsyncIterableStorage,
    AsyncKeyValueIndex,
    AsyncKeyValueStorage,
    AsyncOrderedSetStorage,
    AsyncCopyableStorage,
    AsyncMergeableStorage,
    AsyncReplaceableStorage,
    AsyncSetStorage,
    AsyncSnapshotableStorage,
    AsyncTrieStorage,
    DroppableStorage,
    IterableStorage,
    IntSerializer,
    KeyValueIndex,
    KeyValueStorage,
    OrderedSetStorage,
    CopyableStorage,
    MergeableStorage,
    ReplaceableStorage,
    SetStorage,
    SnapshotableStorage,
    TrieStorage,
    get_registry,
)


class UserClient:
    pass


class AsyncUserClient:
    pass


class UserStorage:
    def __init__(self) -> None:
        self.data: dict[tuple[str, str], str] = {}

    def get(self, client: UserClient, name: str, field: str) -> str | None:
        return self.data.get((name, field))

    def set(
        self, client: UserClient, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        self.data[(name, field)] = value


class AsyncUserStorage:
    def __init__(self) -> None:
        self.data: dict[tuple[str, str], str] = {}

    async def get(self, client: AsyncUserClient, name: str, field: str) -> str | None:
        return self.data.get((name, field))

    async def set(
        self,
        client: AsyncUserClient,
        name: str,
        field: str,
        value: str,
        *,
        ttl: int | None = None,
    ) -> None:
        self.data[(name, field)] = value


user_storage = UserStorage()
async_user_storage = AsyncUserStorage()


class UserIndex(KeyValueIndex):
    identifier = int
    model = int
    serializer = IntSerializer()
    key = "users"
    client_type = UserClient
    storage = user_storage


class AsyncUserIndex(AsyncKeyValueIndex):
    identifier = int
    model = int
    serializer = IntSerializer()
    key = "users"
    client_type = AsyncUserClient
    storage = async_user_storage


class IncompleteIndex:
    identifier = int
    model = int


def test_index_registry() -> None:
    index = get_registry(UserClient).get("users")
    async_index = get_registry(AsyncUserClient).get("users")
    assert isinstance(index, UserIndex)
    assert isinstance(async_index, AsyncUserIndex)
    assert isinstance(index, KeyValueIndex)
    assert isinstance(async_index, AsyncKeyValueIndex)
    assert index.storage is user_storage
    assert async_index.storage is async_user_storage
    assert not isinstance(IncompleteIndex(), KeyValueIndex)
    with pytest.raises(KeyError):
        get_registry(UserClient).get("missing")
    with pytest.raises(KeyError):
        get_registry(AsyncUserClient).get("missing")

    client = UserClient()
    assert index.get(client, 1) is None
    index.set(client, 1, 7)
    assert index.get(client, 1) == 7

    async def scenario() -> None:
        async_client = AsyncUserClient()
        assert await async_index.get(async_client, 1) is None
        await async_index.set(async_client, 1, 8)
        assert await async_index.get(async_client, 1) == 8

    asyncio.run(scenario())


class UnusedClient:
    pass


def test_get_registry() -> None:
    assert isinstance(get_registry(UserClient).get("users"), UserIndex)
    assert isinstance(get_registry(AsyncUserClient).get("users"), AsyncUserIndex)
    with pytest.raises(KeyError, match="no index 'missing' registered for UserClient"):
        get_registry(UserClient).get("missing")
    with pytest.raises(KeyError, match="no index 'missing' registered for AsyncUserClient"):
        get_registry(AsyncUserClient).get("missing")


def test_unknown_client_has_no_registry() -> None:
    with pytest.raises(KeyError, match="no indexes registered for UnusedClient"):
        get_registry(UnusedClient)


def test_duplicate_index_key() -> None:
    with pytest.raises(ValueError):
        class DuplicateUserIndex(KeyValueIndex):
            identifier = int
            model = int
            serializer = IntSerializer()
            key = "users"
            client_type = UserClient
            storage = UserStorage()
    with pytest.raises(ValueError):
        class DuplicateAsyncUserIndex(AsyncKeyValueIndex):
            identifier = int
            model = int
            serializer = IntSerializer()
            key = "users"
            client_type = AsyncUserClient
            storage = AsyncUserStorage()


class MemoryHash:
    def get(self, client: object, name: str, field: str) -> str | None:
        return None

    def set(
        self, client: object, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        return None

    def delete(self, client: object, name: str, field: str) -> None:
        return None

    def mdelete(self, client: object, name: str, fields: Sequence[str]) -> None:
        return None

    def exists(self, client: object, name: str, field: str) -> bool:
        return False

    def mget(self, client: object, name: str, fields: Sequence[str]) -> list[str | None]:
        return [None for _ in fields]

    def mset(
        self, client: object, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        return None

    def snapshot(self, client: object, name: str) -> str:
        return f"{name}:swap"

    def replace(self, client: object, source: str, dest: str) -> None:
        return None

    def merge(self, client: object, source: str, dest: str) -> None:
        return None

    def copy(self, client: object, source: str, dest: str) -> None:
        return None

    def drop(self, client: object, name: str) -> None:
        return None

    def iter(self, client: object, name: str) -> Iterator[object]:
        return iter(())


class AsyncMemoryHash:
    async def get(self, client: object, name: str, field: str) -> str | None:
        return None

    async def set(
        self, client: object, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        return None

    async def delete(self, client: object, name: str, field: str) -> None:
        return None

    async def mdelete(self, client: object, name: str, fields: Sequence[str]) -> None:
        return None

    async def exists(self, client: object, name: str, field: str) -> bool:
        return False

    async def mget(self, client: object, name: str, fields: Sequence[str]) -> list[str | None]:
        return [None for _ in fields]

    async def mset(
        self, client: object, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        return None

    async def snapshot(self, client: object, name: str) -> str:
        return f"{name}:swap"

    async def replace(self, client: object, source: str, dest: str) -> None:
        return None

    async def merge(self, client: object, source: str, dest: str) -> None:
        return None

    async def copy(self, client: object, source: str, dest: str) -> None:
        return None

    async def drop(self, client: object, name: str) -> None:
        return None

    async def iter(self, client: object, name: str) -> AsyncIterator[object]:
        for _item in ():
            yield _item


class MemorySet:
    def add(self, client: object, name: str, member: str) -> None:
        return None

    def madd(self, client: object, name: str, members: Sequence[str]) -> None:
        return None

    def remove(self, client: object, name: str, member: str) -> None:
        return None

    def mremove(self, client: object, name: str, members: Sequence[str]) -> None:
        return None

    def contains(self, client: object, name: str, member: str) -> bool:
        return False

    def snapshot(self, client: object, name: str) -> str:
        return f"{name}:swap"

    def replace(self, client: object, source: str, dest: str) -> None:
        return None

    def merge(self, client: object, source: str, dest: str) -> None:
        return None

    def copy(self, client: object, source: str, dest: str) -> None:
        return None

    def drop(self, client: object, name: str) -> None:
        return None

    def iter(self, client: object, name: str) -> Iterator[object]:
        return iter(())


class AsyncMemorySet:
    async def add(self, client: object, name: str, member: str) -> None:
        return None

    async def madd(self, client: object, name: str, members: Sequence[str]) -> None:
        return None

    async def remove(self, client: object, name: str, member: str) -> None:
        return None

    async def mremove(self, client: object, name: str, members: Sequence[str]) -> None:
        return None

    async def contains(self, client: object, name: str, member: str) -> bool:
        return False

    async def snapshot(self, client: object, name: str) -> str:
        return f"{name}:swap"

    async def replace(self, client: object, source: str, dest: str) -> None:
        return None

    async def merge(self, client: object, source: str, dest: str) -> None:
        return None

    async def copy(self, client: object, source: str, dest: str) -> None:
        return None

    async def drop(self, client: object, name: str) -> None:
        return None

    async def iter(self, client: object, name: str) -> AsyncIterator[object]:
        for _item in ():
            yield _item


class MemoryOrderedSet:
    def add(self, client: object, name: str, member: str, score: float) -> None:
        return None

    def madd(self, client: object, name: str, members: Sequence[tuple[str, float]]) -> None:
        return None

    def remove(self, client: object, name: str, member: str) -> None:
        return None

    def mremove(self, client: object, name: str, members: Sequence[str]) -> None:
        return None

    def contains(self, client: object, name: str, member: str) -> bool:
        return False

    def score(self, client: object, name: str, member: str) -> float | None:
        return None

    def rank(self, client: object, name: str, member: str) -> int | None:
        return None

    def range(self, client: object, name: str, start: int, stop: int) -> list[str]:
        return []

    def range_with_scores(
        self, client: object, name: str, start: int, stop: int
    ) -> list[tuple[str, float]]:
        return []

    def rev_rank(self, client: object, name: str, member: str) -> int | None:
        return None

    def rev_range(self, client: object, name: str, start: int, stop: int) -> list[str]:
        return []

    def rev_range_with_scores(
        self, client: object, name: str, start: int, stop: int
    ) -> list[tuple[str, float]]:
        return []

    def snapshot(self, client: object, name: str) -> str:
        return f"{name}:swap"

    def replace(self, client: object, source: str, dest: str) -> None:
        return None

    def merge(self, client: object, source: str, dest: str) -> None:
        return None

    def copy(self, client: object, source: str, dest: str) -> None:
        return None

    def drop(self, client: object, name: str) -> None:
        return None

    def iter(self, client: object, name: str) -> Iterator[object]:
        return iter(())


class AsyncMemoryOrderedSet:
    async def add(self, client: object, name: str, member: str, score: float) -> None:
        return None

    async def madd(
        self, client: object, name: str, members: Sequence[tuple[str, float]]
    ) -> None:
        return None

    async def remove(self, client: object, name: str, member: str) -> None:
        return None

    async def mremove(self, client: object, name: str, members: Sequence[str]) -> None:
        return None

    async def contains(self, client: object, name: str, member: str) -> bool:
        return False

    async def score(self, client: object, name: str, member: str) -> float | None:
        return None

    async def rank(self, client: object, name: str, member: str) -> int | None:
        return None

    async def range(self, client: object, name: str, start: int, stop: int) -> list[str]:
        return []

    async def range_with_scores(
        self, client: object, name: str, start: int, stop: int
    ) -> list[tuple[str, float]]:
        return []

    async def rev_rank(self, client: object, name: str, member: str) -> int | None:
        return None

    async def rev_range(self, client: object, name: str, start: int, stop: int) -> list[str]:
        return []

    async def rev_range_with_scores(
        self, client: object, name: str, start: int, stop: int
    ) -> list[tuple[str, float]]:
        return []

    async def snapshot(self, client: object, name: str) -> str:
        return f"{name}:swap"

    async def replace(self, client: object, source: str, dest: str) -> None:
        return None

    async def merge(self, client: object, source: str, dest: str) -> None:
        return None

    async def copy(self, client: object, source: str, dest: str) -> None:
        return None

    async def drop(self, client: object, name: str) -> None:
        return None

    async def iter(self, client: object, name: str) -> AsyncIterator[object]:
        for _item in ():
            yield _item


class MemoryTrie:
    def add(
        self,
        client: object,
        name: str,
        string: str,
        score: float,
        payload: str,
        *,
        increment: bool = False,
    ) -> None:
        return None

    def madd(
        self,
        client: object,
        name: str,
        entries: Sequence[tuple[str, float, str]],
        *,
        increment: bool = False,
    ) -> None:
        return None

    def remove(self, client: object, name: str, string: str) -> None:
        return None

    def mremove(self, client: object, name: str, strings: Sequence[str]) -> None:
        return None

    def search(
        self,
        client: object,
        name: str,
        prefix: str,
        *,
        fuzzy: bool = False,
        limit: int = 10,
    ) -> list[str]:
        return []

    def length(self, client: object, name: str) -> int:
        return 0

    def snapshot(self, client: object, name: str) -> str:
        return f"{name}:swap"

    def replace(self, client: object, source: str, dest: str) -> None:
        return None

    def merge(self, client: object, source: str, dest: str) -> None:
        raise NotImplementedError("MemoryTrie cannot merge a suggestion dictionary")

    def copy(self, client: object, source: str, dest: str) -> None:
        return None

    def drop(self, client: object, name: str) -> None:
        return None


class AsyncMemoryTrie:
    async def add(
        self,
        client: object,
        name: str,
        string: str,
        score: float,
        payload: str,
        *,
        increment: bool = False,
    ) -> None:
        return None

    async def madd(
        self,
        client: object,
        name: str,
        entries: Sequence[tuple[str, float, str]],
        *,
        increment: bool = False,
    ) -> None:
        return None

    async def remove(self, client: object, name: str, string: str) -> None:
        return None

    async def mremove(self, client: object, name: str, strings: Sequence[str]) -> None:
        return None

    async def search(
        self,
        client: object,
        name: str,
        prefix: str,
        *,
        fuzzy: bool = False,
        limit: int = 10,
    ) -> list[str]:
        return []

    async def length(self, client: object, name: str) -> int:
        return 0

    async def snapshot(self, client: object, name: str) -> str:
        return f"{name}:swap"

    async def replace(self, client: object, source: str, dest: str) -> None:
        return None

    async def merge(self, client: object, source: str, dest: str) -> None:
        raise NotImplementedError("AsyncMemoryTrie cannot merge a suggestion dictionary")

    async def copy(self, client: object, source: str, dest: str) -> None:
        return None

    async def drop(self, client: object, name: str) -> None:
        return None


class PartialKvStorage:
    def get(self, client: object, name: str, field: str) -> str | None:
        return None

    def set(
        self, client: object, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        return None

    def delete(self, client: object, name: str, field: str) -> None:
        return None

    def mdelete(self, client: object, name: str, fields: Sequence[str]) -> None:
        return None

    def exists(self, client: object, name: str, field: str) -> bool:
        return False

    def mget(self, client: object, name: str, fields: Sequence[str]) -> list[str | None]:
        return [None for _ in fields]

    def mset(
        self, client: object, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        return None


def test_storage_protocols() -> None:
    kv = MemoryHash()
    async_kv = AsyncMemoryHash()
    assert isinstance(kv, KeyValueStorage)
    assert isinstance(async_kv, AsyncKeyValueStorage)
    assert isinstance(kv, SnapshotableStorage)
    assert isinstance(kv, ReplaceableStorage)
    assert isinstance(kv, MergeableStorage)
    assert isinstance(kv, CopyableStorage)
    assert isinstance(kv, DroppableStorage)
    assert isinstance(kv, IterableStorage)
    assert isinstance(async_kv, AsyncSnapshotableStorage)
    assert isinstance(async_kv, AsyncReplaceableStorage)
    assert isinstance(async_kv, AsyncMergeableStorage)
    assert isinstance(async_kv, AsyncCopyableStorage)
    assert isinstance(async_kv, AsyncDroppableStorage)
    assert isinstance(async_kv, AsyncIterableStorage)

    partial = PartialKvStorage()
    assert isinstance(partial, KeyValueStorage)
    assert not isinstance(partial, SnapshotableStorage)
    assert not isinstance(partial, IterableStorage)

    set_storage = MemorySet()
    async_set = AsyncMemorySet()
    assert isinstance(set_storage, SetStorage)
    assert isinstance(async_set, AsyncSetStorage)
    assert isinstance(set_storage, SnapshotableStorage)
    assert isinstance(set_storage, IterableStorage)

    ordered = MemoryOrderedSet()
    async_ordered = AsyncMemoryOrderedSet()
    assert isinstance(ordered, OrderedSetStorage)
    assert isinstance(async_ordered, AsyncOrderedSetStorage)
    assert isinstance(ordered, SnapshotableStorage)

    trie = MemoryTrie()
    async_trie = AsyncMemoryTrie()
    assert isinstance(trie, TrieStorage)
    assert isinstance(async_trie, AsyncTrieStorage)
    assert isinstance(trie, SnapshotableStorage)
    assert not isinstance(trie, IterableStorage)


def test_public_api_omits_redis_storages() -> None:
    import cachebind

    for name in (
        "RedisStringStorage",
        "RedisHashStorage",
        "RedisSetStorage",
        "RedisOrderedSetStorage",
        "RedisTrieStorage",
        "AsyncRedisStringStorage",
        "AsyncRedisHashStorage",
        "AsyncRedisSetStorage",
        "AsyncRedisOrderedSetStorage",
        "AsyncRedisTrieStorage",
    ):
        assert name not in cachebind.__all__
        assert not hasattr(cachebind, name)
