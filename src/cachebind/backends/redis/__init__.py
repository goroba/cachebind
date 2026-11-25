"""Redis backend: client, decode, keys, and helpers for every supported type."""

from cachebind.backends.redis.types import SCAN_COUNT, AsyncRedis, Redis, ResponseError
from cachebind.backends.redis.decode import decode, required_text, scan_done
from cachebind.backends.redis.keys import (
    async_copy_key,
    async_replace_key,
    async_swap_key,
    copy_key,
    replace_key,
    swap_key,
)
from cachebind.backends.redis.ordered_set import (
    empty_range,
    members_from_range,
    pairs_from_range,
    rank_value,
    score_value,
)
from cachebind.backends.redis.trie import (
    DEFAULT_LIMIT,
    check_limit,
    length_value,
    payloads_from_suggestions,
    sugadd_command,
    sugget_command,
)

__all__ = [
    "AsyncRedis",
    "Redis",
    "ResponseError",
    "SCAN_COUNT",
    "async_copy_key",
    "async_replace_key",
    "async_swap_key",
    "check_limit",
    "copy_key",
    "decode",
    "DEFAULT_LIMIT",
    "empty_range",
    "members_from_range",
    "length_value",
    "pairs_from_range",
    "payloads_from_suggestions",
    "rank_value",
    "replace_key",
    "required_text",
    "scan_done",
    "score_value",
    "sugadd_command",
    "sugget_command",
    "swap_key",
]