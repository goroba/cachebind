"""Asynchronous set-backed tag keeper."""

from cachebind.indexes._builder import storage_client_type
from cachebind.indexes.base import get_registry
from cachebind.indexes.evictable import AsyncEvictableIndex
from cachebind.storage.sets.async_storage import AsyncSetStorage
from cachebind.tagging.breadcrumbs.breadcrumbs import Breadcrumbs
from cachebind.tagging.breadcrumbs.colon_breadcrumbs import ColonBreadcrumbs
from cachebind.tagging.tag_keeper._keys import DEFAULT_TAG_KEEPER_NAME, tag_set_key
from cachebind.tagging.tag_keeper.tag_keeper import AsyncTagKeeper


class AsyncSetTagKeeper[ClientType](AsyncTagKeeper[ClientType]):
    """Collect breadcrumbs in sets ``tag_keeper:{name}:{tag}``; flush via registry eviction."""

    def __init__(
        self,
        *,
        storage: AsyncSetStorage[ClientType, str],
        name: str = DEFAULT_TAG_KEEPER_NAME,
        breadcrumbs: Breadcrumbs | None = None,
    ) -> None:
        self.name = name
        self._storage = storage
        self._client_type = storage_client_type("tag_keeper", type(storage), AsyncSetStorage)
        self._breadcrumbs = ColonBreadcrumbs() if breadcrumbs is None else breadcrumbs

    async def add(self, client: ClientType, tag: str, breadcrumb: str) -> None:
        if breadcrumb == "":
            return
        await self._storage.add(client, tag_set_key(self.name, tag), breadcrumb)

    async def madd(self, client: ClientType, tag: str, breadcrumbs: list[str]) -> None:
        members = [item for item in breadcrumbs if item != ""]
        if not members:
            return
        await self._storage.madd(client, tag_set_key(self.name, tag), members)

    async def evict(self, client: ClientType, tag: str) -> None:
        key = tag_set_key(self.name, tag)
        registry = get_registry(self._client_type)
        async for breadcrumb in self._storage.iter(client, key):
            index_name, identifier = self._breadcrumbs.decode(breadcrumb)
            index = registry.get(index_name)
            if not isinstance(index, AsyncEvictableIndex):
                raise TypeError(f"index {index_name!r} does not support eviction")
            await index.evict(client, identifier)
        await self._storage.drop(client, key)