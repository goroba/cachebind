"""Shared merge context managers for snapshot-capable indexes."""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING
from uuid import uuid4

from cachebind.indexes.base import get_registry

if TYPE_CHECKING:
    from cachebind.indexes.base import Index


def merge_staging_key(live_key: str) -> str:
    return f"{live_key}:merge:{uuid4().hex}"


def _assert_mergeable_sync(index: Index, client: object) -> None:
    probe = f"{index.key}:merge_capable:{uuid4().hex}"
    try:
        index.storage.merge(client, probe, index.key)
    except NotImplementedError as exc:
        raise NotImplementedError(
            f"{type(index.storage).__name__} cannot merge a single-key index"
        ) from exc


async def _assert_mergeable_async(index: Index, client: object) -> None:
    probe = f"{index.key}:merge_capable:{uuid4().hex}"
    try:
        await index.storage.merge(client, probe, index.key)
    except NotImplementedError as exc:
        raise NotImplementedError(
            f"{type(index.storage).__name__} cannot merge a single-key index"
        ) from exc


def _commit_merge_sync(index: Index, client: object, staging: Index) -> None:
    registry = get_registry(index.client_type)
    if staging.key in registry:
        raise ValueError(
            f"source key {staging.key!r} is registered; build staging with detach(), not build_*"
        )
    index.storage.merge(client, staging.key, index.key)
    staging.drop(client)


async def _commit_merge_async(index: Index, client: object, staging: Index) -> None:
    registry = get_registry(index.client_type)
    if staging.key in registry:
        raise ValueError(
            f"source key {staging.key!r} is registered; build staging with detach(), not build_*"
        )
    await index.storage.merge(client, staging.key, index.key)
    await staging.drop(client)


@contextmanager
def merge_context(index: Index, client: object):
    _assert_mergeable_sync(index, client)
    staging = index.detach(merge_staging_key(index.key))
    try:
        yield staging
    except BaseException:
        staging.drop(client)
        raise
    else:
        _commit_merge_sync(index, client, staging)


@asynccontextmanager
async def async_merge_context(index: Index, client: object):
    await _assert_mergeable_async(index, client)
    staging = index.detach(merge_staging_key(index.key))
    try:
        yield staging
    except BaseException:
        await staging.drop(client)
        raise
    else:
        await _commit_merge_async(index, client, staging)