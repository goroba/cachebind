# Write-Back Caching example

An application can collect small writes in the cache and copy them to the database later. The cache takes the frequent writes. The database receives them in one pass.

Last visit is a typical case. Each time a user opens the app, store the time. A later job reads those times and saves them.

The job must not lose a visit that arrives while it is saving, and it must not delete a visit that has not been saved yet. `snapshot`, `iter`, and `drop` do that.

## Collect

Build the index once. The user id is a `UUID`. The value is a `datetime`. The storage is a Redis hash, so the whole index is one key.

```python
from datetime import datetime
from uuid import UUID

from cachebind import DatetimeSerializer, build_async_key_value_index
from cachebind.storage import AsyncRedisHashStorage

last_visits = build_async_key_value_index(
    "last_visits",
    id_type=UUID,
    model_type=datetime,
    serializer=DatetimeSerializer(),
    storage=AsyncRedisHashStorage(),
)
```

On each visit, store the current time. A second visit for the same user replaces the first. Leave the TTL unset, so a visit is still there when the job runs.

```python
from datetime import datetime, timezone

await last_visits.set(client, user_id, datetime.now(timezone.utc))
```

`client` is an async Redis client created with `decode_responses=True`.

## Flush

`snapshot` is a context manager. On enter it moves the collected times aside and yields an unregistered index for that data. `last_visits` stays registered and is empty. Visits that arrive after the snapshot go there, and they are not part of this flush.

Walk the snapshot and save each time. The id comes back as text, which is how it was stored, so turn it back into a `UUID`. On a successful flush, leaving the block drops the snapshot.

```python
from uuid import UUID

async with last_visits.snapshot(client) as snapshot:
    async for user_id, visited_at in snapshot.iter(client):
        await save_last_visit(UUID(user_id), visited_at)
```

`save_last_visit` writes one user to the database. Writing the same user again is safe when the database keeps the later time.

If a save fails inside the block, the context manager does not drop the snapshot. The `snapshot` binding from the `as` clause still refers to that data, so you can retry the loop or call `await snapshot.drop(client)` when you are done.

`drop` deletes only the snapshot. It does not touch `last_visits`, and it does not change the registry.

A string storage cannot do this. It keeps a separate Redis key for each id, so `snapshot`, `iter`, and `drop` raise `NotImplementedError`.