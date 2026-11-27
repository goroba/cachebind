# Cache Stampede/Thundering Herd: Coordinated Fill With Lease Get

This guide explains stampede and thundering-herd behavior on cache misses, then shows how `lease_get` coordinates a single origin load per id.

## What cache stampede and thundering herd mean

**Thundering herd** is the general pattern: many workers wait on or react to the same event at once (a lock is released, a barrier opens, a resource becomes ready). They wake or proceed together and contend for the same work or resource. The phrase comes from operating-system scheduling; distributed systems use it for any synchronized rush.

**Cache stampede** is the caching case: many readers **miss** on the same id (or many hot ids) at once and **each** runs the origin loader. The herd stampedes on the database or API behind the cache. Hits still help; one coordinated miss under load can duplicate work hundreds of times and spike latency.

Blog posts often use the two terms interchangeably. Here, **stampede** names the miss-triggered load spike; **thundering herd** names the broader uncoordinated rush. **Coordinated fill** means at most one origin load per id while the cache slot is empty. The sections below show typical triggers, then how `lease_get` implements that coordination.

## When it shows up

**Cold key.** The id was never cached, or the entry expired and was removed. The first burst of traffic after deploy or after TTL expiry all sees a miss.

**Mass expiry.** Many keys share the same TTL and expire together. Every request for those ids misses at once.

**Invalidation.** You delete or evict a popular entry. The next wave of readers all miss until someone refills the cache.

The usual pattern is cache-aside: `get` from cache, on miss load from the database, then `set`. That pattern is correct for a single request. Under load, every miss runs the loader independently. That is the stampede.

## What you want

For each id, at most one origin load should run while the cache is empty. Other callers should either read the value once it appears, back off and retry, or use another fallback. You do not need every worker to hit the database for the same user at the same moment.

## How `lease_get` helps

`lease_get` on a key-value index works like `get` when the value is present. On a miss it tries to take a short **fill lease** in Redis (a separate lease key per id). The caller that acquires the lease runs your **callback** once, stores the result with `set`, and **always** releases the lease in a `finally` block, including after errors.

Callers that miss but **do not** get the lease receive `None` and **do not** run the callback. They are not the filler for that id during that window.

- **`lease_ttl`** — how long the fill lease lives if not released (seconds). Protects against a crashed filler; separate from cache entry TTL.
- **`ttl`** — passed to `set` after a successful callback, same as a normal `set`.

Requirements: a key-value index with leasable storage (`AsyncRedisHashStorage`, `RedisHashStorage`, or the string storage twins). Sets, ordered sets, and tries do not support fill leases.

Sync code uses `KeyValueIndex.lease_get` with a synchronous callback and sync Redis storage the same way.

## Example

Build the index as usual. Use a callback that closes over the id you pass to `lease_get` (for example a `lambda`).

```python
from uuid import UUID

from pydantic import BaseModel
from redis.asyncio import Redis as AsyncRedis

from cachebind import build_async_key_value_index
from cachebind.serializers.pydantic_serializer import PydanticSerializer
from cachebind.storage import AsyncRedisHashStorage

class User(BaseModel):
    id: UUID
    name: str


users = build_async_key_value_index(
    "users",
    id_type=UUID,
    model_type=User,
    serializer=PydanticSerializer(User),
    storage=AsyncRedisHashStorage(),
)


async def load_user(user_id: UUID) -> User:
    ...  # database or API


async def cached_user(client: AsyncRedis, user_id: UUID) -> User | None:
    return await users.lease_get(
        client,
        user_id,
        lambda: load_user(user_id),
        lease_ttl=30,
        ttl=60,
    )
```

`client` is an async Redis client with `decode_responses=True`. `load_user` should be async so `lease_get` can `await` the callback result.

## When `lease_get` returns `None`

`None` means there was no cached value and another worker already holds the fill lease (or held it until you called). Your callback did not run.

Typical responses in application code:

- Call `get` again — the filler may have finished and written the cache.
- Retry `lease_get` after a short delay, with a small retry limit.
- Return a temporary error or stale fallback if your product allows it.

Cachebind does not block or poll inside `lease_get`; you choose retry policy above the index.

## Summary

| Situation | Without coordination | With `lease_get` |
|-----------|----------------------|------------------|
| Many misses on one id | Many origin loads | One callback runs; others get `None` |
| Cache hit | One Redis read | Same as `get` |
| Filler crashes mid-load | N/A | Lease expires via `lease_ttl`; another caller can try later |

For other patterns (tagged eviction, write-back flush), see the recipe links in the repository README.