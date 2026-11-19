"""Synchronous trie index."""

from collections.abc import Hashable, Sequence
from typing import Self

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
    ) -> None:
        """Add ``string`` with ``score`` and ``member`` as its payload.

        A string that is already present gets the new score and payload.
        ``increment=True`` adds ``score`` to the stored score instead of replacing it.
        """
        self.storage.add(
            client,
            self.key,
            string,
            score,
            self.serializer.serialize(member),
            increment=increment,
        )

    def madd(
        self,
        client: ClientType,
        entries: Sequence[tuple[str, MemberType, float]],
        *,
        increment: bool = False,
    ) -> None:
        """Add every suggestion. A repeated string keeps the last score and payload."""
        if not entries:
            return
        serialized = self.serializer.mserialize([member for _string, member, _score in entries])
        stored = [
            (string, score, payload)
            for (string, _member, score), payload in zip(entries, serialized, strict=True)
        ]
        self.storage.madd(client, self.key, stored, increment=increment)

    def remove(self, client: ClientType, string: str) -> None:
        """Remove the suggestion ``string``. A missing string is not an error."""
        self.storage.remove(client, self.key, string)

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
    ) -> list[MemberType]:
        """Return members whose suggestion string matches ``prefix``, in rank order.

        ``limit`` is the maximum number of members. ``fuzzy`` allows a one-edit prefix.
        Members are deserialized from the stored payloads.
        """
        check_limit(limit)
        raw = self.storage.search(client, self.key, prefix, fuzzy=fuzzy, limit=limit)
        return self.serializer.mdeserialize(raw)

    def length(self, client: ClientType) -> int:
        """Return the number of suggestion strings in the trie."""
        return self.storage.length(client, self.key)

    def swap(self, client: ClientType) -> Self:
        """Rename this index aside and return an unregistered index for that data."""
        return self.detach(self.storage.swap(client, self.key))

    def drop(self, client: ClientType) -> None:
        """Delete the key this index is bound to. A missing key is not an error."""
        self.storage.drop(client, self.key)
