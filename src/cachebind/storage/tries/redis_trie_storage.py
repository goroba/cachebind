"""Synchronous Redis trie storage. ``name`` is one suggestion dictionary."""

from collections.abc import Sequence

from cachebind.storage._redis import Redis, replace_key, swap_key
from cachebind.storage.tries._reply import payloads_from_suggestions
from cachebind.storage.tries._values import length_value, sugadd_command, sugget_command
from cachebind.storage.tries.storage import TrieStorage


class RedisTrieStorage(TrieStorage[Redis, str]):
    """Synchronous Redis Search trie. ``name`` is the suggestion-dictionary key.

    Rank uses the stored score. A shorter remainder after the prefix ranks higher
    than a longer suggestion with the same score. ``search`` returns payloads in that order.
    """

    def add(
        self,
        client: Redis,
        name: str,
        string: str,
        score: float,
        payload: str,
        *,
        increment: bool = False,
    ) -> None:
        client.execute_command(
            *sugadd_command(name, string, score, payload, increment=increment)
        )

    def madd(
        self,
        client: Redis,
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
        pipe.execute()

    def remove(self, client: Redis, name: str, string: str) -> None:
        client.execute_command("FT.SUGDEL", name, string)

    def mremove(self, client: Redis, name: str, strings: Sequence[str]) -> None:
        if not strings:
            return
        pipe = client.pipeline(transaction=False)
        for string in strings:
            pipe.execute_command("FT.SUGDEL", name, string)
        pipe.execute()

    def search(
        self,
        client: Redis,
        name: str,
        prefix: str,
        *,
        fuzzy: bool = False,
        limit: int = 10,
    ) -> list[str]:
        raw = client.execute_command(*sugget_command(name, prefix, fuzzy=fuzzy, limit=limit))
        return payloads_from_suggestions(raw)

    def length(self, client: Redis, name: str) -> int:
        return length_value(client.execute_command("FT.SUGLEN", name))

    def swap(self, client: Redis, name: str) -> str:
        return swap_key(client, name)

    def replace(self, client: Redis, source: str, dest: str) -> None:
        replace_key(client, source, dest)

    def drop(self, client: Redis, name: str) -> None:
        client.delete(name)
