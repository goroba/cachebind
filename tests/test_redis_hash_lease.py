import asyncio

import fakeredis

from cachebind.backends.redis.lease import lease_key
from cachebind.storage import AsyncRedisHashStorage, RedisHashStorage

_NAME = "users"
_FIELD = "1"


def test_sync_acquire_release_and_skip_when_present() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisHashStorage()
    token = "tok-a"

    assert storage.try_acquire_lease(
        client, _NAME, _FIELD, token=token, lease_ttl=10
    ) is True
    assert client.get(lease_key(_NAME, _FIELD)) == token
    assert (
        storage.try_acquire_lease(
            client, _NAME, _FIELD, token="tok-b", lease_ttl=10
        )
        is False
    )

    storage.set(client, _NAME, _FIELD, "payload")
    assert (
        storage.try_acquire_lease(
            client, _NAME, "2", token="tok-c", lease_ttl=10
        )
        is True
    )
    assert (
        storage.try_acquire_lease(
            client, _NAME, _FIELD, token="tok-d", lease_ttl=10
        )
        is False
    )

    storage.release_lease(client, _NAME, "2", token="tok-c")
    assert client.get(lease_key(_NAME, "2")) is None
    storage.release_lease(client, _NAME, "2", token="wrong")
    storage.release_lease(client, _NAME, _FIELD, token=token)


def test_async_acquire_release() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        storage = AsyncRedisHashStorage()
        assert await storage.try_acquire_lease(
            client, _NAME, _FIELD, token="t1", lease_ttl=5
        )
        await storage.release_lease(client, _NAME, _FIELD, token="t1")
        assert await client.get(lease_key(_NAME, _FIELD)) is None

    asyncio.run(scenario())


def test_string_storage_lease_key() -> None:
    from cachebind.storage import RedisStringStorage

    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisStringStorage()
    assert storage.try_acquire_lease(
        client, _NAME, "a", token="t", lease_ttl=10
    )
    assert client.get(lease_key(_NAME, "a")) == "t"
    storage.set(client, _NAME, "a", "1")
    assert storage.try_acquire_lease(
        client, _NAME, "a", token="t2", lease_ttl=10
    ) is False
    storage.release_lease(client, _NAME, "a", token="t")