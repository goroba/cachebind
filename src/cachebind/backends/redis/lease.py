"""Per-field fill-lease keys for Redis key-value storages."""

from cachebind.backends.redis.types import AsyncRedis, Redis

def lease_key(name: str, field: str) -> str:
    return f"{name}:lease:{field}"


def try_acquire_lease(
    client: Redis,
    *,
    field_present: bool,
    name: str,
    field: str,
    token: str,
    lease_ttl: int,
) -> bool:
    """Acquire the lease when the field has no stored value."""
    if field_present:
        return False
    return bool(client.set(lease_key(name, field), token, nx=True, ex=lease_ttl))


async def async_try_acquire_lease(
    client: AsyncRedis,
    *,
    field_present: bool,
    name: str,
    field: str,
    token: str,
    lease_ttl: int,
) -> bool:
    if field_present:
        return False
    return bool(await client.set(lease_key(name, field), token, nx=True, ex=lease_ttl))


def release_lease(client: Redis, name: str, field: str, *, token: str) -> None:
    key = lease_key(name, field)
    if client.get(key) == token:
        client.delete(key)


async def async_release_lease(
    client: AsyncRedis, name: str, field: str, *, token: str
) -> None:
    key = lease_key(name, field)
    if await client.get(key) == token:
        await client.delete(key)


__all__ = [
    "async_release_lease",
    "async_try_acquire_lease",
    "lease_key",
    "release_lease",
    "try_acquire_lease",
]