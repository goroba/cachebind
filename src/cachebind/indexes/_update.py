"""Shared update context managers for copy-on-write index edits."""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING
from uuid import uuid4

from cachebind.indexes._replace import (
    _assert_replaceable_async,
    _assert_replaceable_sync,
    _replace_async,
    _replace_sync,
)

if TYPE_CHECKING:
    from cachebind.indexes.base import Index


def update_staging_key(live_key: str) -> str:
    return f"{live_key}:update:{uuid4().hex}"


def _assert_copyable_sync(index: Index, client: object) -> None:
    probe = f"{index.key}:copy_capable:{uuid4().hex}"
    try:
        index.storage.copy(client, index.key, probe)
    except NotImplementedError as exc:
        raise NotImplementedError(
            f"{type(index.storage).__name__} cannot copy a single-key index"
        ) from exc
    else:
        index.storage.drop(client, probe)


async def _assert_copyable_async(index: Index, client: object) -> None:
    probe = f"{index.key}:copy_capable:{uuid4().hex}"
    try:
        await index.storage.copy(client, index.key, probe)
    except NotImplementedError as exc:
        raise NotImplementedError(
            f"{type(index.storage).__name__} cannot copy a single-key index"
        ) from exc
    else:
        await index.storage.drop(client, probe)


@contextmanager
def update_context(index: Index, client: object):
    _assert_copyable_sync(index, client)
    _assert_replaceable_sync(index, client)
    staging = index.detach(update_staging_key(index.key))
    index.storage.copy(client, index.key, staging.key)
    try:
        yield staging
    except BaseException:
        staging.drop(client)
        raise
    else:
        _replace_sync(index, client, staging)


@asynccontextmanager
async def async_update_context(index: Index, client: object):
    await _assert_copyable_async(index, client)
    await _assert_replaceable_async(index, client)
    staging = index.detach(update_staging_key(index.key))
    await index.storage.copy(client, index.key, staging.key)
    try:
        yield staging
    except BaseException:
        await staging.drop(client)
        raise
    else:
        await _replace_async(index, client, staging)