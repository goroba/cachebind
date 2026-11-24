"""Asynchronous Redis trie storage. ``name`` is one suggestion dictionary."""

from collections.abc import Sequence

from cachebind.storage._redis import AsyncRedis, async_replace_key, async_swap_key
from cachebind.storage.tries._reply import payloads_from_suggestions
from cachebind.storage.tries._values import length_value, sugadd_command, sugget_command
from cachebind.storage.tries.async_storage import AsyncTrieStorage


class AsyncRedisTrieStorage(AsyncTrieStorage[AsyncRedis, str]):
    """Asynchronous Redis Search trie. ``name`` is the suggestion-dictionary key.

    Rank uses the stored score. A shorter remainder after the prefix ranks higher
    than a longer suggestion with the same score. ``search`` returns payloads in that order.
    """

    async def add(
        self,
        client: AsyncRedis,
        name: str,
        string: str,
        score: float,
        payload: str,
        *,
        increment: bool = False,
    ) -> None:
        await client.execute_command(
            *sugadd_command(name, string, score, payload, increment=increment)
        )

    async def madd(
        self,
        client: AsyncRedis,
        name: str,
        entries: Sequence[tuple[str, float, str]],
        *,
        increment: bool = False,
    ) -> None:
        if not entries:
            return
        pipe = client.pipeline(transaction=False)
        for string, score, payload in entries:
            pipe.execute_command(
                *sugadd_command(name, string, score, payload, increment=increment)
            )
        await pipe.execute()

    async def remove(self, client: AsyncRedis, name: str, string: str) -> None:
        await client.execute_command("FT.SUGDEL", name, string)

    async def mremove(self, client: AsyncRedis, name: str, strings: Sequence[str]) -> None:
        if not strings:
            return
        pipe = client.pipeline(transaction=False)
        for string in strings:
            pipe.execute_command("FT.SUGDEL", name, string)
        await pipe.execute()

    async def search(
        self,
        client: AsyncRedis,
        name: str,
        prefix: str,
        *,
        fuzzy: bool = False,
        limit: int = 10,
    ) -> list[str]:
        raw = await client.execute_command(
            *sugget_command(name, prefix, fuzzy=fuzzy, limit=limit)
        )
        return payloads_from_suggestions(raw)

    async def length(self, client: AsyncRedis, name: str) -> int:
        return length_value(await client.execute_command("FT.SUGLEN", name))

    async def snapshot(self, client: AsyncRedis, name: str) -> str:
        return await async_swap_key(client, name)

    async def replace(self, client: AsyncRedis, source: str, dest: str) -> None:
        await async_replace_key(client, source, dest)

    async def merge(self, client: AsyncRedis, source: str, dest: str) -> None:
        raise NotImplementedError(f"{type(self).__name__} cannot merge a suggestion dictionary")

    async def drop(self, client: AsyncRedis, name: str) -> None:
        await client.delete(name)
