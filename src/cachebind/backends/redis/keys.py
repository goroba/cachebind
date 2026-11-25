"""Redis key lifecycle operations."""

from uuid import uuid4

from cachebind.backends.redis.types import AsyncRedis, Redis, ResponseError


def swap_key(client: Redis, name: str) -> str:
    """Rename ``name`` aside and return the new name. A missing key still returns one."""
    snapshot_name = f"{name}:swap:{uuid4().hex}"
    try:
        client.rename(name, snapshot_name)
    except ResponseError as exc:
        if "no such key" in str(exc).lower():
            return snapshot_name
        raise
    return snapshot_name


async def async_swap_key(client: AsyncRedis, name: str) -> str:
    """Rename ``name`` aside and return the new name. A missing key still returns one."""
    snapshot_name = f"{name}:swap:{uuid4().hex}"
    try:
        await client.rename(name, snapshot_name)
    except ResponseError as exc:
        if "no such key" in str(exc).lower():
            return snapshot_name
        raise
    return snapshot_name


def replace_key(client: Redis, source: str, dest: str) -> None:
    """Rename ``source`` onto ``dest``. ``dest`` is overwritten atomically."""
    if source == dest:
        raise ValueError("source and dest must differ")
    client.rename(source, dest)


async def async_replace_key(client: AsyncRedis, source: str, dest: str) -> None:
    """Rename ``source`` onto ``dest``. ``dest`` is overwritten atomically."""
    if source == dest:
        raise ValueError("source and dest must differ")
    await client.rename(source, dest)


def copy_key(client: Redis, source: str, dest: str) -> None:
    """Duplicate ``source`` onto ``dest``. A missing ``source`` is a no-op."""
    if source == dest:
        raise ValueError("source and dest must differ")
    try:
        client.copy(source, dest)
    except ResponseError as exc:
        if "no such key" in str(exc).lower():
            return
        raise


async def async_copy_key(client: AsyncRedis, source: str, dest: str) -> None:
    """Duplicate ``source`` onto ``dest``. A missing ``source`` is a no-op."""
    if source == dest:
        raise ValueError("source and dest must differ")
    try:
        await client.copy(source, dest)
    except ResponseError as exc:
        if "no such key" in str(exc).lower():
            return
        raise


__all__ = [
    "async_copy_key",
    "async_replace_key",
    "async_swap_key",
    "copy_key",
    "replace_key",
    "swap_key",
]