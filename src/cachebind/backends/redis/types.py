"""Redis client types. Requires the ``redis`` extra."""

try:
    from redis import Redis
    from redis.asyncio import Redis as AsyncRedis
    from redis.exceptions import ResponseError
except ImportError as exc:
    raise ImportError(
        "Redis support is not installed. Install it with: pip install 'cachebind[redis]'"
    ) from exc

SCAN_COUNT = 100

__all__ = ["AsyncRedis", "Redis", "ResponseError", "SCAN_COUNT"]