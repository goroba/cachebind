# Tag-Based Caching

A user profile can live in a key-value cache. The same user can also appear on a leaderboard stored in an ordered set. When the user is deleted, both cache entries should disappear together.

A **tag keeper** records breadcrumbs from each cache write under one tag, such as `user:{id}`. One call to `evict` on that tag drops every bound entry, no matter which index wrote it.

This tutorial is self-contained: it uses Redis only, with stub data instead of a database. For loading users from Postgres while caching leaderboard rows, see [Leaderboard](leaderboard.md). The tagging steps below apply the same way on cache writes.

## Install

```bash
pip install "cachebind[redis,pydantic]"
```

Redis for a local run:

```bash
docker run --name cachebind-redis -p 6379:6379 -d redis:7
```

The snippets in this tutorial are one program, in this order.

## User model

The cached profile is a Pydantic model. The user id is a UUID.

```python
from uuid import UUID

from pydantic import BaseModel


class User(BaseModel):
    id: UUID
    name: str


ada = User(id=UUID("12345678-1234-5678-1234-567812345678"), name="Ada")
```

The leaderboard stores user ids as members with a float score. Use `UuidSerializer` so ordered-set members round-trip as canonical UUID text in Redis.

## Indexes and tag keeper

Build the indexes once. `set` and `add` return breadcrumbs by default (`ColonBreadcrumbs`), which the tag keeper can store.

The tag keeper uses **set** storage (`AsyncRedisSetStorage`), separate from the hash and ordered set used by the indexes. Each tag is one Redis set at `tag_keeper:{name}:{tag}`.

```python
from cachebind import (
    AsyncSetTagKeeper,
    UuidSerializer,
    build_async_key_value_index,
    build_async_ordered_set_index,
)
from cachebind.serializers.pydantic_serializer import PydanticSerializer
from cachebind.storage import (
    AsyncRedisHashStorage,
    AsyncRedisOrderedSetStorage,
    AsyncRedisSetStorage,
)

cached_users = build_async_key_value_index(
    "cached_users",
    id_type=UUID,
    model_type=User,
    serializer=PydanticSerializer(User),
    storage=AsyncRedisHashStorage(),
)

leaderboard = build_async_ordered_set_index(
    "leaderboard",
    member_type=UUID,
    serializer=UuidSerializer(),
    storage=AsyncRedisOrderedSetStorage(),
)

tag_keeper = AsyncSetTagKeeper(storage=AsyncRedisSetStorage())
```

`client` is an async Redis client created with `decode_responses=True`.

```python
from redis.asyncio import Redis as AsyncRedis

client = AsyncRedis(decode_responses=True)
```

## Tag helper

Use one tag string per user so every cache entry for that user shares the same label.

```python
def user_tag(user_id: UUID) -> str:
    return f"user:{user_id}"
```

## Cache writes

Profile loading and leaderboard updates happen in different parts of the app. Each cache write returns one breadcrumb. Register it under `user:{id}` with `tag_keeper.add`. The same tag string ties the two call sites together.

The user id must be the same in the key-value index and as the ordered-set member.

### Cache the user profile

When the profile is loaded (from the database or from stub data in this tutorial), store the model and add the breadcrumb to the tag.

```python
async def load_user_from_database(user_id: UUID) -> User:
    """Load a user row from the database."""
    return ada


async def show_user_profile(client: AsyncRedis, user_id: UUID) -> User:
    user = await load_user_from_database(user_id)
    breadcrumb = await cached_users.set(
        client, id=user.id, value=user, ttl=60
    )
    await tag_keeper.add(
        client, tag=user_tag(user.id), breadcrumb=breadcrumb
    )
    return user
```

### Cache the leaderboard row

When a score is recorded, add the member to the ordered set and register that breadcrumb under the same tag.

```python
async def record_leaderboard_score(
    client: AsyncRedis, user_id: UUID, score: float
) -> None:
    breadcrumb = await leaderboard.add(
        client, member=user_id, score=score
    )
    await tag_keeper.add(
        client, tag=user_tag(user_id), breadcrumb=breadcrumb
    )
```

If one code path performs several writes that should share a tag, use `tag_keeper.madd` with every breadcrumb from that path.

On a later profile or score update, call `set` or `add` again and `tag_keeper.add` the new breadcrumb under the same tag. Re-run `evict` on delete whenever the tag set should drop every current binding.

## Delete user

Delete the user in the database first. The tag keeper does not remove database rows. It only evicts cache entries referenced by breadcrumbs in the tag set.

```python
async def delete_user_from_database(user_id: UUID) -> None:
    """Remove the user row from the database."""


async def delete_user(client: AsyncRedis, user_id: UUID) -> None:
    await delete_user_from_database(user_id)
    await tag_keeper.evict(client, tag=user_tag(user_id))
```

`evict` walks the breadcrumbs in `tag_keeper:default:user:{id}`, decodes each `index:identifier` pair, calls `evict` on the registered index, then deletes the tag set.

Both cache entries are gone:

```python
async def main() -> None:
    client = AsyncRedis(decode_responses=True)

    await show_user_profile(client, ada.id)
    await record_leaderboard_score(client, ada.id, 1800.0)

    assert await cached_users.get(client, id=ada.id) is not None
    assert await leaderboard.contains(client, member=ada.id)

    await delete_user(client, ada.id)

    assert await cached_users.get(client, id=ada.id) is None
    assert not await leaderboard.contains(client, member=ada.id)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

## Notes

- **Breadcrumbs on writes.** Key-value, set, and ordered-set indexes default to `ColonBreadcrumbs`, so `set` and `add` return strings the tag keeper can store. Pass `breadcrumbs=NoopBreadcrumbs()` on build when you do not use a tag keeper.
- **Tag keeper is not an index.** It groups breadcrumbs in Redis sets. Eviction still goes through each index’s `evict` method.
- **Trie indexes** do not support `evict`, so do not bind trie breadcrumbs to a tag keeper unless you handle those entries another way.
- **Optional `name`** on `AsyncSetTagKeeper` separates tag namespaces when several applications share one Redis (`tag_keeper:{name}:{tag}`).
- **Database-backed leaderboards** can follow [Leaderboard](leaderboard.md) for `serialize` / `deserialize` on each call. Call `tag_keeper.add` or `tag_keeper.madd` whenever you populate the cache after a read or write.