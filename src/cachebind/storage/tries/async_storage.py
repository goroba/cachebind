"""Asynchronous trie storage."""

from abc import ABC, abstractmethod
from collections.abc import Hashable, Sequence


class AsyncTrieStorage[ClientType, PayloadType: Hashable](ABC):
    """Asynchronous trie storage.

    ``client`` is the storage client for that call.
    ``name`` is the trie name. ``string`` is one suggestion in that trie.
    Each suggestion has one score and one payload. Adding a string that is already
    present replaces its score and payload, unless ``increment`` is true.
    ``increment`` adds the score to the stored score. Removing a missing string is not an error.
    ``search`` returns payloads in rank order. ``limit`` is the maximum number of payloads.
    ``fuzzy`` requests matches within one edit of ``prefix``.
    """

    @abstractmethod
    async def add(
        self,
        client: ClientType,
        name: str,
        string: str,
        score: float,
        payload: PayloadType,
        *,
        increment: bool = False,
    ) -> None:
        """Add ``string`` with ``score`` and ``payload``.

        A string that is already present gets the new score and payload.
        ``increment=True`` adds ``score`` to the stored score instead of replacing it.
        """
        ...

    @abstractmethod
    async def madd(
        self,
        client: ClientType,
        name: str,
        entries: Sequence[tuple[str, float, PayloadType]],
        *,
        increment: bool = False,
    ) -> None:
        """Add every suggestion. A repeated string keeps the last score and payload."""
        ...

    @abstractmethod
    async def remove(self, client: ClientType, name: str, string: str) -> None:
        """Remove ``string``. A missing string is not an error."""
        ...

    @abstractmethod
    async def mremove(self, client: ClientType, name: str, strings: Sequence[str]) -> None:
        """Remove every string. Missing strings are not an error."""
        ...

    @abstractmethod
    async def search(
        self,
        client: ClientType,
        name: str,
        prefix: str,
        *,
        fuzzy: bool = False,
        limit: int = 10,
    ) -> list[PayloadType]:
        """Return payloads for suggestions that match ``prefix``, in rank order."""
        ...

    @abstractmethod
    async def length(self, client: ClientType, name: str) -> int:
        """Return the number of suggestion strings in the trie."""
        ...