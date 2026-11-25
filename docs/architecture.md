# Architecture

Cachebind is organized in layers. Dependencies point downward only.

## Layers

| Layer | Package | Role |
|-------|---------|------|
| L0 | `cachebind` | Public exports |
| L1 | `indexes`, `serializers`, `tagging` | Domain APIs (no Redis driver) |
| L2 | `storage` | Storage protocols and backend adapters (`RedisHashStorage`, …) |
| L3 | `backends.redis` | Redis client, wire decode, key ops, copy/merge for all types |
| L4 | `redis` (PyPI) | Driver |

## Redis backend (`cachebind.backends.redis`)

All Redis-specific logic for every supported data structure lives here:

- `types.py` — `Redis` / `AsyncRedis`, `SCAN_COUNT`
- `pipeline.py` — non-transactional pipeline flush helpers
- `decode.py` — generic value decoding
- `ordered_set.py` — ZSET reply parsing
- `trie.py` — suggestion-dictionary commands and replies
- `keys.py` — rename, copy, snapshot swap
- `copy_merge.py` — hash, set, ordered set, trie copy and merge

Storage adapters import from `backends.redis` only. There are no private `_*` helper modules under `storage/` for Redis wire format or copy/merge.

## Adding another backend

Introduce `cachebind.backends.<name>/` with the same responsibilities as `backends.redis`, and wire new storage adapter classes under `storage/` that call into it. Keep `indexes` and protocols free of backend imports.