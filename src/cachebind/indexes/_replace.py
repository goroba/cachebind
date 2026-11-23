"""Shared replace and snapshot context managers for snapshot-capable indexes."""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING
from uuid import uuid4

from cachebind.indexes.base import get_registry

if TYPE_CHECKING:
    from cachebind.indexes.base import Index


def staging_key(live_key: str) -> str:
    return f"{live_key}:replace:{uuid4().hex}"


def _assert_snapshot_capable_sync(index: Index, client: object) -> None:
    probe = f"{index.key}:snapshot_capable:{uuid4().hex}"
    try:
        index.storage.snapshot(client, probe)
    except NotImplementedError as exc:
        raise NotImplementedError(
            f"{type(index.storage).__name__} cannot snapshot a single-key index"
        ) from exc


async def _assert_snapshot_capable_async(index: Index, client: object) -> None:
    probe = f"{index.key}:snapshot_capable:{uuid4().hex}"
    try:
        await index.storage.snapshot(client, probe)
    except NotImplementedError as exc:
        raise NotImplementedError(
            f"{type(index.storage).__name__} cannot snapshot a single-key index"
        ) from exc


def _assert_replaceable_sync(index: Index, client: object) -> None:
    try:
        _assert_snapshot_capable_sync(index, client)
    except NotImplementedError as exc:
        raise NotImplementedError(
            f"{type(index.storage).__name__} cannot replace a single-key index"
        ) from exc


async def _assert_replaceable_async(index: Index, client: object) -> None:
    try:
        await _assert_snapshot_capable_async(index, client)
    except NotImplementedError as exc:
        raise NotImplementedError(
            f"{type(index.storage).__name__} cannot replace a single-key index"
        ) from exc


def _missing_rename_source(exc: BaseException) -> bool:
    return "no such key" in str(exc).lower()


def _commit_sync(index: Index, client: object, staging: Index) -> None:
    registry = get_registry(index.client_type)
    if staging.key in registry:
        raise ValueError(
            f"source key {staging.key!r} is registered; build staging with detach(), not build_*"
        )
    try:
        index.storage.replace(client, staging.key, index.key)
    except Exception as exc:
        if _missing_rename_source(exc):
            index.storage.drop(client, index.key)
        else:
            raise


async def _commit_async(index: Index, client: object, staging: Index) -> None:
    registry = get_registry(index.client_type)
    if staging.key in registry:
        raise ValueError(
            f"source key {staging.key!r} is registered; build staging with detach(), not build_*"
        )
    try:
        await index.storage.replace(client, staging.key, index.key)
    except Exception as exc:
        if _missing_rename_source(exc):
            await index.storage.drop(client, index.key)
        else:
            raise


@contextmanager
def replace_context(index: Index, client: object):
    _assert_replaceable_sync(index, client)
    staging = index.detach(staging_key(index.key))
    try:
        yield staging
    except BaseException:
        staging.drop(client)
        raise
    else:
        _commit_sync(index, client, staging)


@asynccontextmanager
async def async_replace_context(index: Index, client: object):
    await _assert_replaceable_async(index, client)
    staging = index.detach(staging_key(index.key))
    try:
        yield staging
    except BaseException:
        await staging.drop(client)
        raise
    else:
        await _commit_async(index, client, staging)


@contextmanager
def snapshot_context(index: Index, client: object):
    _assert_snapshot_capable_sync(index, client)
    snapshot = index.detach(index.storage.snapshot(client, index.key))
    try:
        yield snapshot
    except BaseException:
        raise
    else:
        snapshot.drop(client)


@asynccontextmanager
async def async_snapshot_context(index: Index, client: object):
    await _assert_snapshot_capable_async(index, client)
    swapped = await index.storage.snapshot(client, index.key)
    snapshot = index.detach(swapped)
    try:
        yield snapshot
    except BaseException:
        raise
    else:
        await snapshot.drop(client)