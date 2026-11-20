import asyncio
import inspect
from collections.abc import AsyncIterator, Iterator, Mapping, Sequence

import pytest

from cachebind import (
    IntSerializer,
    build_async_key_value_index,
    build_key_value_index,
    build_set_index,
    build_trie_index,
)
from cachebind.storage.key_value.async_storage import AsyncKeyValueStorage
from cachebind.storage.key_value.storage import KeyValueStorage
from cachebind.storage.sets.storage import SetStorage
from cachebind.storage.tries.storage import TrieStorage
from cachebind.tagging import ColonTagMaker


class Memory:
    pass


class MemoryStorage(KeyValueStorage[Memory, str, str]):
    def __init__(self) -> None:
        self.data: dict[tuple[str, str], str] = {}

    def get(self, client: Memory, name: str, field: str) -> str | None:
        return self.data.get((name, field))

    def set(
        self, client: Memory, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        self.data[(name, field)] = value

    def delete(self, client: Memory, name: str, field: str) -> None:
        self.data.pop((name, field), None)

    def mdelete(self, client: Memory, name: str, fields: Sequence[str]) -> None:
        for field in fields:
            self.data.pop((name, field), None)

    def exists(self, client: Memory, name: str, field: str) -> bool:
        return (name, field) in self.data

    def mget(self, client: Memory, name: str, fields: Sequence[str]) -> list[str | None]:
        return [self.data.get((name, field)) for field in fields]

    def mset(
        self, client: Memory, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        for field, value in items.items():
            self.data[(name, field)] = value

    def swap(self, client: Memory, name: str) -> str:
        return f"{name}:swap"

    def drop(self, client: Memory, name: str) -> None:
        return None

    def iter(self, client: Memory, name: str) -> Iterator[tuple[str, str]]:
        return iter(())


class AsyncMemoryHash(AsyncKeyValueStorage[Memory, str, str]):
    def __init__(self) -> None:
        self.data: dict[tuple[str, str], str] = {}

    async def get(self, client: Memory, name: str, field: str) -> str | None:
        return self.data.get((name, field))

    async def set(
        self, client: Memory, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        self.data[(name, field)] = value

    async def delete(self, client: Memory, name: str, field: str) -> None:
        self.data.pop((name, field), None)

    async def mdelete(self, client: Memory, name: str, fields: Sequence[str]) -> None:
        for field in fields:
            self.data.pop((name, field), None)

    async def exists(self, client: Memory, name: str, field: str) -> bool:
        return (name, field) in self.data

    async def mget(self, client: Memory, name: str, fields: Sequence[str]) -> list[str | None]:
        return [self.data.get((name, field)) for field in fields]

    async def mset(
        self, client: Memory, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        for field, value in items.items():
            self.data[(name, field)] = value

    async def swap(self, client: Memory, name: str) -> str:
        return f"{name}:swap"

    async def drop(self, client: Memory, name: str) -> None:
        return None

    async def iter(self, client: Memory, name: str) -> AsyncIterator[tuple[str, str]]:
        for item in ():
            yield item


def test_key_value_set_and_mset_tags() -> None:
    storage = MemoryStorage()
    index = build_key_value_index(
        "tag_users",
        id_type=int,
        model_type=int,
        serializer=IntSerializer(),
        storage=storage,
    )
    client = Memory()
    assert index.set(client, 1, 7) == ""
    assert index.mset(client, {2: 8, 3: 9}) == ["", ""]
    assert index.mset(client, {}) == []

    colon = build_key_value_index(
        "tag_colon",
        id_type=int,
        model_type=int,
        serializer=IntSerializer(),
        storage=MemoryStorage(),
        tag_maker=ColonTagMaker(),
    )
    assert colon.set(client, 1, 1) == "tag_colon:1"


def test_set_add_tags() -> None:
    class SetMemory:
        pass

    class TagSetStorage(SetStorage[SetMemory, str]):
        def __init__(self) -> None:
            self.members: dict[str, set[str]] = {}

        def add(self, client: object, name: str, member: str) -> None:
            self.members.setdefault(name, set()).add(member)

        def madd(self, client: object, name: str, members: list[str]) -> None:
            for member in members:
                self.add(client, name, member)

        def remove(self, client: object, name: str, member: str) -> None:
            self.members.get(name, set()).discard(member)

        def mremove(self, client: object, name: str, members: list[str]) -> None:
            for member in members:
                self.remove(client, name, member)

        def contains(self, client: object, name: str, member: str) -> bool:
            return member in self.members.get(name, set())

        def swap(self, client: object, name: str) -> str:
            return name

        def drop(self, client: object, name: str) -> None:
            self.members.pop(name, None)

        def iter(self, client: object, name: str):
            return iter(self.members.get(name, set()))

    index = build_set_index(
        "tag_set",
        member_type=int,
        serializer=IntSerializer(),
        storage=TagSetStorage(),
    )
    client = SetMemory()
    assert index.add(client, 4) == ""
    assert index.madd(client, [5, 6]) == ["", ""]
    assert index.madd(client, []) == []


def test_trie_tags_and_builder() -> None:
    sig = inspect.signature(build_trie_index)
    assert "tag_maker" not in sig.parameters

    class TagTrieStorage(TrieStorage[object, str]):
        def __init__(self) -> None:
            self.data: dict[str, list[tuple[str, float, str]]] = {}

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
            self.data.setdefault(name, []).append((string, score, payload))

        def madd(
            self,
            client: object,
            name: str,
            entries: list[tuple[str, float, str]],
            *,
            increment: bool = False,
        ) -> None:
            for entry in entries:
                self.add(client, name, entry[0], entry[1], entry[2])

        def remove(self, client: object, name: str, string: str) -> None:
            pass

        def mremove(self, client: object, name: str, strings: list[str]) -> None:
            pass

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

        def swap(self, client: object, name: str) -> str:
            return name

        def drop(self, client: object, name: str) -> None:
            self.data.pop(name, None)

    index = build_trie_index(
        "tag_trie",
        member_type=int,
        serializer=IntSerializer(),
        storage=TagTrieStorage(),
    )
    client = object()
    assert index.add(client, "Paris", 1, 1.0) == ""
    assert index.madd(client, [("Lyon", 2, 2.0)]) == [""]
    assert index.madd(client, []) == []


def test_builder_rejects_tag_maker_class() -> None:
    with pytest.raises(TypeError, match="tag_maker must be an instance"):
        build_key_value_index(
            "bad_tag",
            id_type=int,
            model_type=int,
            serializer=IntSerializer(),
            storage=MemoryStorage(),
            tag_maker=ColonTagMaker,  # type: ignore[arg-type]
        )


def test_async_key_value_set_tag() -> None:
    index = build_async_key_value_index(
        "async_tag_users",
        id_type=int,
        model_type=int,
        serializer=IntSerializer(),
        storage=AsyncMemoryHash(),
        tag_maker=ColonTagMaker(),
    )

    async def scenario() -> None:
        assert await index.set(Memory(), 9, 9) == "async_tag_users:9"

    asyncio.run(scenario())