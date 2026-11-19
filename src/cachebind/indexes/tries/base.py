"""Shared trie index attributes."""

from __future__ import annotations

from collections.abc import Hashable

from cachebind.indexes.base import Index
from cachebind.serializers.serializer import Serializer
from cachebind.storage.tries.async_storage import AsyncTrieStorage
from cachebind.storage.tries.storage import TrieStorage


class TrieBase[ClientType, MemberType, StorageType: Hashable](Index):
    """Member, serializer, storage key, and storage for a trie index.

    ``key`` is the trie name. ``storage`` stores suggestion strings, scores, and payloads.
    The serializer converts a member to that payload and back.
    Each call receives the storage client.
    """

    member: type[MemberType]
    serializer: Serializer[MemberType, StorageType]
    storage: TrieStorage[ClientType, StorageType] | AsyncTrieStorage[ClientType, StorageType]
