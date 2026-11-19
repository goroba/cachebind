import asyncio

import fakeredis
import pytest

from cachebind.storage import AsyncRedisTrieStorage, RedisTrieStorage
from cachebind.storage.tries.async_storage import AsyncTrieStorage
from cachebind.storage.tries.storage import TrieStorage


class Scripted:
    def __init__(self, replies: list[object] | None = None) -> None:
        self.replies = list(replies or [])
        self.commands: list[tuple[object, ...]] = []
        self.pipelines: list[bool] = []

    def execute_command(self, *args: object) -> object:
        self.commands.append(args)
        return self.replies.pop(0)

    def pipeline(self, transaction: bool = True) -> "ScriptedPipeline":
        self.pipelines.append(transaction)
        return ScriptedPipeline(self)


class ScriptedPipeline:
    def __init__(self, client: Scripted) -> None:
        self.client = client
        self.queued: list[tuple[object, ...]] = []

    def execute_command(self, *args: object) -> None:
        self.queued.append(args)

    def execute(self) -> list[object]:
        return [self.client.execute_command(*args) for args in self.queued]


class AsyncScripted:
    def __init__(self, replies: list[object] | None = None) -> None:
        self.replies = list(replies or [])
        self.commands: list[tuple[object, ...]] = []
        self.pipelines: list[bool] = []

    async def execute_command(self, *args: object) -> object:
        self.commands.append(args)
        return self.replies.pop(0)

    def pipeline(self, transaction: bool = True) -> "AsyncScriptedPipeline":
        self.pipelines.append(transaction)
        return AsyncScriptedPipeline(self)


class AsyncScriptedPipeline:
    def __init__(self, client: AsyncScripted) -> None:
        self.client = client
        self.queued: list[tuple[object, ...]] = []

    def execute_command(self, *args: object) -> None:
        self.queued.append(args)

    async def execute(self) -> list[object]:
        replies: list[object] = []
        for args in self.queued:
            replies.append(await self.client.execute_command(*args))
        return replies


class Quiet:
    def __init__(self) -> None:
        self.called = False

    def execute_command(self, *args: object) -> object:
        self.called = True
        return []

    def pipeline(self, transaction: bool = True) -> object:
        self.called = True
        raise AssertionError(transaction)


def test_sync_trie_storage_commands() -> None:
    client = Scripted(
        replies=[
            1,
            1,
            1,
            1,
            ["Paris", "1", b"Prague", b"2"],
            ["Paris", "1"],
            2,
            0,
            0,
            0,
        ]
    )
    storage = RedisTrieStorage()
    assert isinstance(storage, TrieStorage)

    storage.add(client, "cities", "Paris", 900.0, "1")
    storage.add(client, "cities", "Prague", 5.0, "2", increment=True)
    storage.madd(client, "cities", [("Padua", 200.0, "3"), ("Padua", 220.0, "3")])
    assert storage.search(client, "cities", "P") == ["1", "2"]
    assert storage.search(client, "cities", "P", fuzzy=True, limit=3) == ["1"]
    assert storage.length(client, "cities") == 2
    storage.remove(client, "cities", "Lyon")
    storage.mremove(client, "cities", ["Padua", "Lisbon"])

    assert client.pipelines == [False, False]
    assert client.commands == [
        ("FT.SUGADD", "cities", "Paris", 900.0, "PAYLOAD", "1"),
        ("FT.SUGADD", "cities", "Prague", 5.0, "INCR", "PAYLOAD", "2"),
        ("FT.SUGADD", "cities", "Padua", 200.0, "PAYLOAD", "3"),
        ("FT.SUGADD", "cities", "Padua", 220.0, "PAYLOAD", "3"),
        ("FT.SUGGET", "cities", "P", "MAX", 10, "WITHPAYLOADS"),
        ("FT.SUGGET", "cities", "P", "MAX", 3, "WITHPAYLOADS", "FUZZY"),
        ("FT.SUGLEN", "cities"),
        ("FT.SUGDEL", "cities", "Lyon"),
        ("FT.SUGDEL", "cities", "Padua"),
        ("FT.SUGDEL", "cities", "Lisbon"),
    ]


def test_sync_trie_storage_rejects_a_bad_reply_or_limit() -> None:
    storage = RedisTrieStorage()
    empty = Scripted(replies=[None])
    assert storage.search(empty, "cities", "P") == []

    missing = Scripted(replies=[["Paris", None]])
    with pytest.raises(ValueError, match="no payload"):
        storage.search(missing, "cities", "P")

    odd = Scripted(replies=[["Paris", "1", "Prague"]])
    with pytest.raises(TypeError, match="reply length"):
        storage.search(odd, "cities", "P")

    wrong = Scripted(replies=["nope"])
    with pytest.raises(TypeError, match="suggestion type"):
        storage.search(wrong, "cities", "P")

    length = Scripted(replies=["2"])
    with pytest.raises(TypeError, match="suggestion length"):
        storage.length(length, "cities")

    quiet = Quiet()
    with pytest.raises(ValueError, match="trie limit"):
        storage.search(quiet, "cities", "P", limit=0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="trie limit"):
        storage.search(quiet, "cities", "P", limit=True)  # type: ignore[arg-type]
    assert quiet.called is False


def test_sync_trie_storage_empty_batches_do_not_call_redis() -> None:
    quiet = Quiet()
    storage = RedisTrieStorage()
    storage.madd(quiet, "cities", [])  # type: ignore[arg-type]
    storage.mremove(quiet, "cities", [])  # type: ignore[arg-type]
    assert quiet.called is False


def test_sync_trie_storage_swap_renames_the_key() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    client.set("trie_swap", "x")
    storage = RedisTrieStorage()
    renamed = storage.swap(client, "trie_swap")
    assert renamed.startswith("trie_swap:swap:")
    assert client.get("trie_swap") is None
    assert client.get(renamed) == "x"
    storage.drop(client, renamed)
    assert client.get(renamed) is None

    missing = storage.swap(client, "trie_swap_missing")
    assert missing.startswith("trie_swap_missing:swap:")
    storage.drop(client, "trie_swap_missing")


def test_async_trie_storage_commands() -> None:
    async def scenario() -> None:
        client = AsyncScripted(replies=[1, ["Paris", "1"], 1, 0, 1, 0])
        storage = AsyncRedisTrieStorage()
        assert isinstance(storage, AsyncTrieStorage)
        await storage.add(client, "cities", "Paris", 900.0, "1", increment=True)
        assert await storage.search(client, "cities", "Pa", limit=1) == ["1"]
        assert await storage.length(client, "cities") == 1
        await storage.remove(client, "cities", "Paris")
        await storage.madd(client, "cities", [("Lyon", 400.0, "4")])
        await storage.mremove(client, "cities", ["Lyon"])
        assert client.pipelines == [False, False]
        assert client.commands == [
            ("FT.SUGADD", "cities", "Paris", 900.0, "INCR", "PAYLOAD", "1"),
            ("FT.SUGGET", "cities", "Pa", "MAX", 1, "WITHPAYLOADS"),
            ("FT.SUGLEN", "cities"),
            ("FT.SUGDEL", "cities", "Paris"),
            ("FT.SUGADD", "cities", "Lyon", 400.0, "PAYLOAD", "4"),
            ("FT.SUGDEL", "cities", "Lyon"),
        ]

    asyncio.run(scenario())


def test_async_trie_storage_empty_batches_do_not_call_redis() -> None:
    quiet = Quiet()
    storage = AsyncRedisTrieStorage()

    async def scenario() -> None:
        await storage.madd(quiet, "cities", [])  # type: ignore[arg-type]
        await storage.mremove(quiet, "cities", [])  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="trie limit"):
            await storage.search(quiet, "cities", "P", limit=0)  # type: ignore[arg-type]

    asyncio.run(scenario())
    assert quiet.called is False


def test_async_trie_storage_swap_renames_the_key() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        storage = AsyncRedisTrieStorage()
        try:
            await client.set("async_trie_swap", "x")
            renamed = await storage.swap(client, "async_trie_swap")
            assert renamed.startswith("async_trie_swap:swap:")
            assert await client.get("async_trie_swap") is None
            assert await client.get(renamed) == "x"
            await storage.drop(client, renamed)
            assert await client.get(renamed) is None
            missing = await storage.swap(client, "async_trie_swap_missing")
            assert missing.startswith("async_trie_swap_missing:swap:")
            await storage.drop(client, "async_trie_swap_missing")
        finally:
            await client.aclose()

    asyncio.run(scenario())
