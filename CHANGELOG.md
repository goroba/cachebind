# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `lease_get` on key-value indexes: read cache or run a callback under a fill lease on miss, then `set`.
- `LeasableKeyValueStorage` / `AsyncLeasableKeyValueStorage` and `LeasableKeyValueIndex` / `AsyncLeasableKeyValueIndex` protocols.
- Redis hash and string storages support fill-lease acquire and release.
- `docs/lease_get.md` on cache stampede, thundering herd, and using `lease_get`.

### Changed

- `README.md` no longer documents `lease_get`; see `docs/lease_get.md`.

## [1.2.1] - 2026-11-25

### Added

- `docs/architecture.md` describing layers and the `cachebind.backends.redis` package.

### Changed

- Redis wire helpers, key operations, and copy/merge logic live under `cachebind.backends.redis`; storage adapters delegate to it.
- Redis hash, set, ordered-set, and trie `copy`/`merge` use batched pipelines; absent-key clones use `DUMP`/`RESTORE` for an independent copy.

### Fixed

- Staging keys for `update` and related flows stay isolated from live data when the Redis client does not provide a true `COPY` (for example fakeredis).

## [1.2.0] - 2026-11-24

### Added

- `merge` index context manager: combine a detached staging build into the live key without overwriting unrelated entries.
- `update` index context manager: copy live data into staging, edit, then publish with replace semantics.
- `MergeableIndex` / `AsyncMergeableIndex` and `MergeableStorage` / `AsyncMergeableStorage` protocols.
- `UpdatableIndex` / `AsyncUpdatableIndex` and `CopyableStorage` / `AsyncCopyableStorage` protocols.

### Changed

- Leaderboard recipe documents `merge` and `update` workflows.

## [1.1.2] - 2026-11-24

### Added

- `CHANGELOG.md` with release history and Keep a Changelog format.
- PyPI/project metadata links: Homepage, Documentation, Repository, and Changelog in `pyproject.toml`.

### Changed

- `README.md`: drop redundant repository line (links live in package metadata and recipes).

## [1.1.1] - 2026-11-23

### Added

- Snapshot indexes can be used as context managers for scoped snapshot lifecycle.

## [1.1.0] - 2026-11-23

### Added

- Index protocols: `Droppable`, `Evictable`, `Iterable`, and `Snapshotable`.
- Storage protocols: `Droppable`, `Replaceable`, `Iterable`, and `Snapshotable`.
- Index replacement API for swapping index configuration or backing storage.

### Fixed

- Broken documentation links in `README.md`.

## [1.0.2] - 2026-11-21

### Changed

- Documentation updates in `README.md`.

## [1.0.1] - 2026-11-21

### Changed

- Patch release (metadata and packaging only).

## [1.0.0] - 2026-11-21

### Added

- Initial public release of **cachebind**: layered **storage**, **indexes**, and **serializers** for cache bindings.
- Key-value, set, ordered-set, and trie storages and indexes (sync and async).
- Serializers with `mserialize` / `mdeserialize` for batch operations.
- Index operations: iteration, dropping, and swapping.
- Breadcrumb encoding for cache keys and eviction identifiers.
- Tag makers, tag-aware persistence responses, `evict()` on indexes, and tag keeper for grouped eviction.
- Optional serializers on index actions; `NoopSerializer`.
- Write-back caching documentation example.

[1.2.1]: https://github.com/goroba/cachebind/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/goroba/cachebind/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/goroba/cachebind/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/goroba/cachebind/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/goroba/cachebind/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.com/goroba/cachebind/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/goroba/cachebind/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/goroba/cachebind/releases/tag/v1.0.0