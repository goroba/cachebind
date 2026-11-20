# cachebind

A Python library that names a cache binding — one storage key, a serializer, and a storage — and reads or writes Python values through it.

**What is it for?** Cachebind is a way to name a cache binding and use it from application code. An index holds one storage key, a serializer, and a storage. You build it once. Each call takes your storage client and reads or writes a Python value through that binding. Redis storages are included. Any storage that matches the protocol works the same way.

**What can an index store?** A key-value index stores one model per id. A set index stores members in one set. An ordered set index stores members with scores, lowest score first. A trie index stores suggestion strings with scores and keeps each member as the payload. `search` returns those members in rank order. Each has a sync builder and an async builder.

## Indexes

Build an index once with `build_async_key_value_index`, `build_async_set_index`, `build_async_ordered_set_index`, or `build_async_trie_index`. Pass a key, the value type, a serializer instance, and a storage instance. Optionally pass a `tag_maker` (default `NoopTagMaker`) on key-value, set, and ordered-set builders. Trie indexes always use `NoopTagMaker` and do not accept `tag_maker`. Then pass a storage client into every call.

`set` and `add` return one cache tag string. `mset` and `madd` return one tag per item. With `ColonTagMaker`, key-value tags use `str(id)` and set or ordered-set tags use the serialized member text. With the default `NoopTagMaker`, those writes return an empty tag.

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

ada = User(id=UUID("12345678-1234-5678-1234-567812345678"), name="Ada")

users = build_async_key_value_index(
    "users",
    id_type=UUID,
    model_type=User,
    serializer=PydanticSerializer(User),
    storage=AsyncRedisHashStorage(),
)

async def main() -> None:
    client = AsyncRedis(decode_responses=True)
    await users.set(client, ada.id, ada, ttl=60)
    value = await users.get(client, ada.id)
    await users.delete(client, ada.id)
```

`ttl` is a whole number of seconds on `set` and `mset`. Omit it, or pass `None`, and the write does not expire. `mset` applies that one TTL to every id. `delete` removes one id. `mdelete` removes every given id. A missing id is not an error.

Inside `main`, the same client works for a set index.

```python
from cachebind import IntSerializer, build_async_set_index
from cachebind.storage import AsyncRedisSetStorage

active = build_async_set_index(
    "active_users",
    member_type=int,
    serializer=IntSerializer(),
    storage=AsyncRedisSetStorage(),
)

    await active.add(client, 1)
    present = await active.contains(client, 1)
    await active.remove(client, 1)
```

`remove` drops one member. A missing member is not an error. Sets have no TTL.

An ordered set uses the same client. Each member has one score. Adding a member that is already present updates its score. `rank` is 0-based, from the lowest score. `range` includes both ends. Ordered sets have no TTL.

```python
from cachebind import IntSerializer, build_async_ordered_set_index
from cachebind.storage import AsyncRedisOrderedSetStorage

ranking = build_async_ordered_set_index(
    "user_scores",
    member_type=int,
    serializer=IntSerializer(),
    storage=AsyncRedisOrderedSetStorage(),
)

    await ranking.add(client, 1, 10.0)
    place = await ranking.rank(client, 1)
    top = await ranking.range(client, 0, 0)
    await ranking.remove(client, 1)
```

A trie uses the same client. The suggestion string is the text you complete. The member is stored as the payload. `search` deserializes those payloads in rank order. `limit` defaults to 10. A trie has no TTL.

```python
from cachebind import IntSerializer, build_async_trie_index
from cachebind.storage import AsyncRedisTrieStorage

cities = build_async_trie_index(
    "cities",
    member_type=int,
    serializer=IntSerializer(),
    storage=AsyncRedisTrieStorage(),
)

    await cities.add(client, "Paris", 1, 900.0)
    matches = await cities.search(client, "P")
    await cities.remove(client, "Paris")
```

`matches` is `[1]`. Redis 8 includes the suggestion commands this storage sends.

Sync indexes use `build_key_value_index`, `build_set_index`, `build_ordered_set_index`, and `build_trie_index` with the matching sync storage. Those calls are not awaited.

`get_registry` from `cachebind` returns that index: `get_registry(AsyncRedis).get("users")`.

## Install

```bash
pip install cachebind
pip install "cachebind[redis]"
pip install "cachebind[pydantic]"
pip install "cachebind[redis,pydantic]"
```

From a checkout, the same extras are:

```bash
pip install -e ".[dev]"
pip install -e ".[redis]"
pip install -e ".[redis,pydantic]"
```

Runtime dependencies live in `pyproject.toml` under `[project] dependencies`. Optional Redis and Pydantic support, and the test tools, live in extras. A plain install does not pull Redis or Pydantic. There is no `requirements.txt`.

## Test

```bash
pytest
```

## Publish

When the package is ready for PyPI, build and upload it. Confirm the project name is free on PyPI first, and fill in the author details in `pyproject.toml`.

```bash
pip install build twine
python -m build
twine upload dist/*
```

## Documentation

- [Leaderboard](docs/leaderboard.md) — ordered set of user ids, with users loaded from Postgres
- [Trie (Prefix Tree)](docs/trie.md) — city names in a Redis Search trie, with cities loaded from Postgres on search
- [Write-Back Caching example](docs/write-back-caching.md) — collect last-visit times, then save them to the database
