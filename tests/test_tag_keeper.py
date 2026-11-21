import asyncio

import pytest

from cachebind import (
    AsyncSetTagKeeper,
    ColonBreadcrumbs,
    IntSerializer,
    SetTagKeeper,
    build_async_key_value_index,
    build_async_trie_index,
    build_key_value_index,
    build_trie_index,
)
from cachebind.storage.sets.async_storage import AsyncSetStorage
from cachebind.storage.sets.storage import SetStorage
from cachebind.storage.tries.async_storage import AsyncTrieStorage
from cachebind.storage.tries.storage import TrieStorage
from test_index_tags import AsyncMemoryHash, Memory, MemoryStorage


class KeeperSetStorage(SetStorage[Memory, str]):
    def __init__(self) -> None:
        self.members: dict[str, set[str]] = {}

    def add(self, client: Memory, name: str, member: str) -> None:
        self.members.setdefault(name, set()).add(member)

    def madd(self, client: Memory, name: str, members: list[str]) -> None:
        for member in members:
            self.add(client, name, member)

    def remove(self, client: Memory, name: str, member: str) -> None:
        self.members.get(name, set()).discard(member)

    def mremove(self, client: Memory, name: str, members: list[str]) -> None:
        for member in members:
            self.remove(client, name, member)

    def contains(self, client: Memory, name: str, member: str) -> bool:
        return member in self.members.get(name, set())

    def swap(self, client: Memory, name: str) -> str:
        return name

    def drop(self, client: Memory, name: str) -> None:
        self.members.pop(name, None)

    def iter(self, client: Memory, name: str):
        return iter(self.members.get(name, set()))


class AsyncKeeperSetStorage(AsyncSetStorage[Memory, str]):
    def __init__(self) -> None:
        self.members: dict[str, set[str]] = {}

    async def add(self, client: Memory, name: str, member: str) -> None:
        self.members.setdefault(name, set()).add(member)

    async def madd(self, client: Memory, name: str, members: list[str]) -> None:
        for member in members:
            await self.add(client, name, member)

    async def remove(self, client: Memory, name: str, member: str) -> None:
        self.members.get(name, set()).discard(member)

    async def mremove(self, client: Memory, name: str, members: list[str]) -> None:
        for member in members:
            await self.remove(client, name, member)

    async def contains(self, client: Memory, name: str, member: str) -> bool:
        return member in self.members.get(name, set())

    async def swap(self, client: Memory, name: str) -> str:
        return name

    async def drop(self, client: Memory, name: str) -> None:
        self.members.pop(name, None)

    def iter(self, client: Memory, name: str):
        async def _iter():
            for member in self.members.get(name, set()):
                yield member

        return _iter()


def test_tag_keeper_add_madd_evict() -> None:
    kv_storage = MemoryStorage()
    users = build_key_value_index(
        "keeper_users",
        id_type=int,
        model_type=int,
        serializer=IntSerializer(),
        storage=kv_storage,
        breadcrumbs=ColonBreadcrumbs(),
    )
    set_storage = KeeperSetStorage()
    keeper = SetTagKeeper(storage=set_storage, name="binding")

    client = Memory()
    tag = "checkout"
    set_key = "tag_keeper:binding:checkout"

    crumb1 = users.set(client, 1, 10)
    crumb2 = users.set(client, 2, 20)
    keeper.add(client, tag, crumb1)
    keeper.madd(client, tag, [crumb2])

    assert set_storage.members[set_key] == {crumb1, crumb2}
    assert users.get(client, 1) == 10
    assert users.get(client, 2) == 20

    keeper.evict(client, tag)

    assert users.get(client, 1) is None
    assert users.get(client, 2) is None
    assert set_key not in set_storage.members


def test_tag_keeper_default_name() -> None:
    set_storage = KeeperSetStorage()
    keeper = SetTagKeeper(storage=set_storage)
    assert keeper.name == "default"
    client = Memory()
    keeper.add(client, "x", "users:1")
    assert "tag_keeper:default:x" in set_storage.members


def test_tag_keeper_skips_empty_breadcrumbs() -> None:
    set_storage = KeeperSetStorage()
    keeper = SetTagKeeper(storage=set_storage, name="skip")
    client = Memory()
    tag = "t"
    set_key = "tag_keeper:skip:t"

    keeper.add(client, tag, "")
    keeper.madd(client, tag, ["", ""])
    assert set_key not in set_storage.members


def test_tag_keeper_missing_index_on_evict() -> None:
    set_storage = KeeperSetStorage()
    keeper = SetTagKeeper(storage=set_storage, name="missing")
    crumb = ColonBreadcrumbs().encode("no_such_index", "1")
    set_storage.add(Memory(), "tag_keeper:missing:batch", crumb)
    with pytest.raises(KeyError, match="no_such_index"):
        keeper.evict(Memory(), "batch")


def test_tag_keeper_trie_evict_raises() -> None:
    class TagTrieStorage(TrieStorage[Memory, str]):
        def add(
            self,
            client: Memory,
            name: str,
            string: str,
            score: float,
            payload: str,
            *,
            increment: bool = False,
        ) -> None:
            pass

        def madd(
            self,
            client: Memory,
            name: str,
            entries: list[tuple[str, float, str]],
            *,
            increment: bool = False,
        ) -> None:
            pass

        def remove(self, client: Memory, name: str, string: str) -> None:
            pass

        def mremove(self, client: Memory, name: str, strings: list[str]) -> None:
            pass

        def search(
            self,
            client: Memory,
            name: str,
            prefix: str,
            *,
            fuzzy: bool = False,
            limit: int = 10,
        ) -> list[str]:
            return []

        def length(self, client: Memory, name: str) -> int:
            return 0

        def swap(self, client: Memory, name: str) -> str:
            return name

        def drop(self, client: Memory, name: str) -> None:
            pass

    build_trie_index(
        "keeper_trie",
        member_type=int,
        serializer=IntSerializer(),
        storage=TagTrieStorage(),
    )
    set_storage = KeeperSetStorage()
    keeper = SetTagKeeper(storage=set_storage, name="trie_binding")
    crumb = ColonBreadcrumbs().encode("keeper_trie", "")
    set_storage.add(Memory(), "tag_keeper:trie_binding:batch", crumb)
    with pytest.raises(NotImplementedError, match="evict is not supported for trie"):
        keeper.evict(Memory(), "batch")


def test_async_tag_keeper_add_madd_evict() -> None:
    async def scenario() -> None:
        kv_storage = AsyncMemoryHash()
        users = build_async_key_value_index(
            "async_keeper_users",
            id_type=int,
            model_type=int,
            serializer=IntSerializer(),
            storage=kv_storage,
            breadcrumbs=ColonBreadcrumbs(),
        )
        set_storage = AsyncKeeperSetStorage()
        keeper = AsyncSetTagKeeper(storage=set_storage, name="async_binding")
        client = Memory()
        tag = "batch"
        set_key = "tag_keeper:async_binding:batch"

        crumb1 = await users.set(client, 3, 30)
        crumb2 = await users.set(client, 4, 40)
        await keeper.add(client, tag, crumb1)
        await keeper.madd(client, tag, [crumb2])

        assert set_storage.members[set_key] == {crumb1, crumb2}
        assert await users.get(client, 3) == 30

        await keeper.evict(client, tag)

        assert await users.get(client, 3) is None
        assert await users.get(client, 4) is None
        assert set_key not in set_storage.members

    asyncio.run(scenario())