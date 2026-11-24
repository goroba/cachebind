"""Asynchronous trie index."""

from collections.abc import Hashable, Sequence
from contextlib import asynccontextmanager
from typing import Self

from cachebind.indexes._merge import async_merge_context
from cachebind.indexes._update import async_update_context
from cachebind.indexes._replace import async_replace_context, async_snapshot_context
from cachebind.indexes._serializer import resolve_serializer
from cachebind.indexes.tries.base import TrieBase
from cachebind.storage.tries._values import check_limit
from cachebind.storage.tries.async_storage import AsyncTrieStorage


class AsyncTrieIndex[ClientType, MemberType, StorageType: Hashable](
    TrieBase[ClientType, MemberType, StorageType]
):
    """Async trie index: member binding, storage key, and the storage that persists it.

    The suggestion string and the score are stored as given. The member is the payload:
    writes serialize it, and ``search`` deserializes the payloads in rank order.
    """

    storage: AsyncTrieStorage[ClientType, StorageType]

    async def add(
        self,
        client: ClientType,
        string: str,
        member: MemberType,
        score: float,
        *,
        increment: bool = False,
        **kwargs,
    ) -> str:
        """Add ``string`` with ``score`` and ``member`` as its payload.

        A string that is already present gets the new score and payload.
        ``increment=True`` adds ``score`` to the stored score instead of replacing it.
        """
        serializer = resolve_serializer(self.serializer, kwargs)
        await self.storage.add(
            client,
            self.key,
            string,
            score,
            serializer.serialize(member),
            increment=increment,
        )
        return self.breadcrumbs.encode(self.key, "")

    async def madd(
        self,
        client: ClientType,
        entries: Sequence[tuple[str, MemberType, float]],
        *,
        increment: bool = False,
        **kwargs,
    ) -> list[str]:
        """Add every suggestion. A repeated string keeps the last score and payload."""
        if not entries:
            return []
        serializer = resolve_serializer(self.serializer, kwargs)
        serialized = serializer.mserialize([member for _string, member, _score in entries])
        stored = [
            (string, score, payload)
            for (string, _member, score), payload in zip(entries, serialized, strict=True)
        ]
        await self.storage.madd(client, self.key, stored, increment=increment)
        crumb = self.breadcrumbs.encode(self.key, "")
        return [crumb] * len(entries)

    async def remove(self, client: ClientType, string: str) -> None:
        """Remove the suggestion ``string``. A missing string is not an error."""
        await self.storage.remove(client, self.key, string)

    async def evict(self, client: ClientType, identifier: str) -> None:
        """Not supported: trie tags do not identify one entry."""
        raise NotImplementedError("evict is not supported for trie indexes")

    async def mremove(self, client: ClientType, strings: Sequence[str]) -> None:
        """Remove every suggestion string. Missing strings are not an error."""
        if not strings:
            return
        await self.storage.mremove(client, self.key, strings)

    async def search(
        self,
        client: ClientType,
        prefix: str,
        *,
        fuzzy: bool = False,
        limit: int = 10,
        **kwargs,
    ) -> list[MemberType]:
        """Return members whose suggestion string matches ``prefix``, in rank order.

        ``limit`` is the maximum number of members. ``fuzzy`` allows a one-edit prefix.
        Members are deserialized from the stored payloads.
        """
        check_limit(limit)
        serializer = resolve_serializer(self.serializer, kwargs)
        raw = await self.storage.search(client, self.key, prefix, fuzzy=fuzzy, limit=limit)
        return serializer.mdeserialize(raw)

    async def length(self, client: ClientType) -> int:
        """Return the number of suggestion strings in the trie."""
        return await self.storage.length(client, self.key)

    @asynccontextmanager
    async def snapshot(self, client: ClientType):
        """Yield an unregistered index for the data that was live on enter; drop it on success."""
        async with async_snapshot_context(self, client) as detached:
            yield detached

    @asynccontextmanager
    async def replace(self, client: ClientType):
        """Yield a detached staging index; publish it on success or drop it on failure."""
        async with async_replace_context(self, client) as staging:
            yield staging

    @asynccontextmanager
    async def merge(self, client: ClientType):
        """Yield a detached staging index; merge it into live on success or drop it on failure."""
        async with async_merge_context(self, client) as staging:
            yield staging

    @asynccontextmanager
    async def update(self, client: ClientType):
        """Yield a staging copy of live data; replace live on success or drop staging on failure."""
        async with async_update_context(self, client) as staging:
            yield staging

    async def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        await self.storage.drop(client, self.key)
