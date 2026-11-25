"""Smoke test for backend layer import order."""


def test_import_backends_redis_before_storage_adapters() -> None:
    import cachebind.backends.redis as redis_backend
    from cachebind.storage.key_value.redis_hash_storage import RedisHashStorage

    assert redis_backend.SCAN_COUNT == 100
    assert RedisHashStorage is not None