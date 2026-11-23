"""Synchronous trie index."""

from collections.abc import Hashable, Sequence
from contextlib import contextmanager
from typing import Self

from cachebind.indexes._replace import replace_context
from cachebind.indexes._serializer import resolve_serializer
from cachebind.indexes.tries.base import TrieBase
from cachebind.storage.tries._values import check_limit
from cachebind.storage.tries.storage import TrieStorage


class TrieIndex[ClientType, MemberType, StorageType: Hashable](
    TrieBase[ClientType, MemberType, StorageType]
):
    """Sync trie index: member binding, storage key, and the storage that persists it.

    The suggestion string and the score are stored as given. The member is the payload:
    writes serialize it, and ``search`` deserializes the payloads in rank order.
    """

    storage: TrieStorage[ClientType, StorageType]

    def add(
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
        self.storage.add(
            client,
            self.key,
            string,
            score,
            serializer.serialize(member),
            increment=increment,
        )
        return self.breadcrumbs.encode(self.key, "")

    def madd(
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
        self.storage.madd(client, self.key, stored, increment=increment)
        crumb = self.breadcrumbs.encode(self.key, "")
        return [crumb] * len(entries)

    def remove(self, client: ClientType, string: str) -> None:
        """Remove the suggestion ``string``. A missing string is not an error."""
        self.storage.remove(client, self.key, string)

    def evict(self, client: ClientType, identifier: str) -> None:
        """Not supported: trie tags do not identify one entry."""
        raise NotImplementedError("evict is not supported for trie indexes")

    def mremove(self, client: ClientType, strings: Sequence[str]) -> None:
        """Remove every suggestion string. Missing strings are not an error."""
        if not strings:
            return
        self.storage.mremove(client, self.key, strings)

    def search(
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
        raw = self.storage.search(client, self.key, prefix, fuzzy=fuzzy, limit=limit)
        return serializer.mdeserialize(raw)

    def length(self, client: ClientType) -> int:
        """Return the number of suggestion strings in the trie."""
        return self.storage.length(client, self.key)

    def snapshot(self, client: ClientType) -> Self:
        """Rename this index aside and return an unregistered index for that data."""
        return self.detach(self.storage.snapshot(client, self.key))

    @contextmanager
    def replace(self, client: ClientType):
        """Yield a detached staging index; publish it on success or drop it on failure."""
        with replace_context(self, client) as staging:
            yield staging

    def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        self.storage.drop(client, self.key)
