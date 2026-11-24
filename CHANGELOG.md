# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.1.1]: https://github.com/goroba/cachebind/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/goroba/cachebind/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.com/goroba/cachebind/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/goroba/cachebind/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/goroba/cachebind/releases/tag/v1.0.0