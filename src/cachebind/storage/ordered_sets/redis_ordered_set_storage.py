"""Synchronous Redis ordered-set storage."""

from collections.abc import Iterator, Sequence

from cachebind.backends.redis import (
    SCAN_COUNT,
    Redis,
    copy_zset,
    empty_range,
    members_from_range,
    merge_zset,
    pairs_from_range,
    rank_value,
    replace_key,
    score_value,
    swap_key,
    zset_windows,
)
from cachebind.storage.ordered_sets.storage import OrderedSetStorage


class RedisOrderedSetStorage(OrderedSetStorage[Redis, str]):
    """Synchronous Redis ordered sets. ``name`` is the Redis key."""

    def add(self, client: Redis, name: str, member: str, score: float) -> None:
        client.zadd(name, {member: score})

    def madd(self, client: Redis, name: str, members: Sequence[tuple[str, float]]) -> None:
        if not members:
            return
        client.zadd(name, {member: score for member, score in members})

    def remove(self, client: Redis, name: str, member: str) -> None:
        client.zrem(name, member)

    def mremove(self, client: Redis, name: str, members: Sequence[str]) -> None:
        if not members:
            return
        client.zrem(name, *members)

    def contains(self, client: Redis, name: str, member: str) -> bool:
        return client.zscore(name, member) is not None

    def score(self, client: Redis, name: str, member: str) -> float | None:
        return score_value(client.zscore(name, member))

    def rank(self, client: Redis, name: str, member: str) -> int | None:
        return rank_value(client.zrank(name, member))

    def range(self, client: Redis, name: str, start: int, stop: int) -> list[str]:
        if empty_range(start, stop):
            return []
        return members_from_range(client.zrange(name, start, stop))

    def range_with_scores(
        self, client: Redis, name: str, start: int, stop: int
    ) -> list[tuple[str, float]]:
        if empty_range(start, stop):
            return []
        return pairs_from_range(client.zrange(name, start, stop, withscores=True))

    def rev_rank(self, client: Redis, name: str, member: str) -> int | None:
        return rank_value(client.zrevrank(name, member))

    def rev_range(self, client: Redis, name: str, start: int, stop: int) -> list[str]:
        if empty_range(start, stop):
            return []
        return members_from_range(client.zrevrange(name, start, stop))

    def rev_range_with_scores(
        self, client: Redis, name: str, start: int, stop: int
    ) -> list[tuple[str, float]]:
        if empty_range(start, stop):
            return []
        return pairs_from_range(client.zrevrange(name, start, stop, withscores=True))

    def snapshot(self, client: Redis, name: str) -> str:
        return swap_key(client, name)

    def replace(self, client: Redis, source: str, dest: str) -> None:
        replace_key(client, source, dest)

    def copy(self, client: Redis, source: str, dest: str) -> None:
        copy_zset(client, source, dest)

    def merge(self, client: Redis, source: str, dest: str) -> None:
        merge_zset(client, source, dest)

    def drop(self, client: Redis, name: str) -> None:
        client.delete(name)

    def iter(
        self, client: Redis, name: str, *, count: int = SCAN_COUNT
    ) -> Iterator[tuple[str, float]]:
        for window in zset_windows(client, name, count=count):
            yield from window
