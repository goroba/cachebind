"""Asynchronous Redis string storage."""

from collections.abc import AsyncIterator, Mapping, Sequence

from cachebind.storage._redis import AsyncRedis, decode
from cachebind.storage.key_value.async_storage import AsyncKeyValueStorage


def _redis_key(name: str, field: str) -> str:
    return f"{name}:{field}"


class AsyncRedisStringStorage(AsyncKeyValueStorage[AsyncRedis, str, str]):
    """Asynchronous Redis strings. The Redis key is ``name:field``."""

    async def get(self, client: AsyncRedis, name: str, field: str) -> str | None:
        return decode(await client.get(_redis_key(name, field)))

    async def set(
        self, client: AsyncRedis, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        key = _redis_key(name, field)
        if ttl is None:
            await client.set(key, value)
        else:
            await client.set(key, value, ex=ttl)

    async def delete(self, client: AsyncRedis, name: str, field: str) -> None:
        await client.delete(_redis_key(name, field))

    async def mdelete(self, client: AsyncRedis, name: str, fields: Sequence[str]) -> None:
        if not fields:
            return
        await client.delete(*(_redis_key(name, field) for field in fields))

    async def exists(self, client: AsyncRedis, name: str, field: str) -> bool:
        return bool(await client.exists(_redis_key(name, field)))

    async def mget(self, client: AsyncRedis, name: str, fields: Sequence[str]) -> list[str | None]:
        if not fields:
            return []
        raw = await client.mget([_redis_key(name, field) for field in fields])
        return [decode(item) for item in raw]

    async def mset(
        self, client: AsyncRedis, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        if not items:
            return
        mapping = {_redis_key(name, field): value for field, value in items.items()}
        if ttl is None:
            await client.mset(mapping)
            return
        pipe = client.pipeline(transaction=True)
        for key, value in mapping.items():
            pipe.set(key, value, ex=ttl)
        await pipe.execute()

    async def swap(self, client: AsyncRedis, name: str) -> str:
        raise NotImplementedError(
            f"{type(self).__name__} keeps one Redis key per field and cannot swap"
        )

    async def replace(self, client: AsyncRedis, source: str, dest: str) -> None:
        raise NotImplementedError(
            f"{type(self).__name__} keeps one Redis key per field and cannot replace"
        )

    async def drop(self, client: AsyncRedis, name: str) -> None:
        raise NotImplementedError(
            f"{type(self).__name__} keeps one Redis key per field and cannot drop"
        )

    def iter(self, client: AsyncRedis, name: str) -> AsyncIterator[tuple[str, str]]:
        raise NotImplementedError(
            f"{type(self).__name__} keeps one Redis key per field and cannot iter"
        )
