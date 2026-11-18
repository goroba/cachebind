"""Redis client import and value decoding. Requires the ``redis`` extra."""

from uuid import uuid4

try:
    from redis import Redis
    from redis.asyncio import Redis as AsyncRedis
    from redis.exceptions import ResponseError
except ImportError as exc:
    raise ImportError(
        "Redis support is not installed. Install it with: pip install 'cacher[redis]'"
    ) from exc


def decode(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8")
    raise TypeError(f"unexpected Redis value type: {type(value).__name__}")


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


__all__ = ["AsyncRedis", "Redis", "async_swap_key", "decode", "swap_key"]
