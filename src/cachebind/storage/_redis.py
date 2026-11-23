"""Redis client import and value decoding. Requires the ``redis`` extra."""

from uuid import uuid4

try:
    from redis import Redis
    from redis.asyncio import Redis as AsyncRedis
    from redis.exceptions import ResponseError
except ImportError as exc:
    raise ImportError(
        "Redis support is not installed. Install it with: pip install 'cachebind[redis]'"
    ) from exc


SCAN_COUNT = 100


def decode(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8")
    raise TypeError(f"unexpected Redis value type: {type(value).__name__}")


def required_text(value: object) -> str:
    """Return ``value`` as text. ``None`` is an error."""
    decoded = decode(value)
    if decoded is None:
        raise TypeError(f"unexpected Redis value type: {type(value).__name__}")
    return decoded


def scan_done(cursor: object) -> bool:
    """Return whether a Redis scan cursor marks the end of the walk."""
    if isinstance(cursor, bytes):
        cursor = cursor.decode("utf-8")
    if isinstance(cursor, str):
        return int(cursor) == 0
    if isinstance(cursor, int) and not isinstance(cursor, bool):
        return cursor == 0
    raise TypeError(f"unexpected Redis scan cursor type: {type(cursor).__name__}")


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


__all__ = [
    "AsyncRedis",
    "Redis",
    "SCAN_COUNT",
    "async_replace_key",
    "async_swap_key",
    "decode",
    "required_text",
    "scan_done",
    "replace_key",
    "swap_key",
]
