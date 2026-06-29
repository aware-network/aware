# Changelog

All notable changes to `aware-orm` are documented here. Dates use UTC.

## [1.0.0] - 2026-06-02

Public release candidate for the installable Aware ORM core.

### Package Boundary

- Locked the base install to `pydantic` and `python-dotenv`; PostgreSQL drivers
  remain opt-in through the `postgres` extra.
- Removed public artifact exposure for legacy bootstrap adapters, repo-only
  docs/tests/scripts/caches, the old lazy relationship loader, the Meta
  projector shim, and producer-shaped ObjectConfigGraph/ClassConfig adapter
  modules.
- Kept package artifact loading on ORM-owned `_aware/orm.graph.binding.msgpack`
  graph snapshots; Meta and Structure remain producer-owned integration lanes.
- Removed the remaining Runtime/Structure session-switch probing from ORM
  internals. Runtime hosts now integrate through the explicit ORM
  `SessionContext` injection API.

### Runtime And Query Core

- Added DB boot planning/execution contracts for package-local generated SQL
  roots with SQLite/PostgreSQL adapter selection.
- Added package-local runtime artifact installation for generated Python model
  manifests, ORM graph bindings, SQL metadata, relationship metadata, and plan
  registries.
- Locked branch-aware Session behavior, local/noop backends, identity-map
  semantics, CRUD queueing, rollback, and read-barrier behavior for ontology
  mutation paths.
- Added QuerySpec and graph retrieval contracts covering equality, range, like,
  in/null filters, AND/OR grouping, sorting, pagination, relation paths,
  many-to-many traversal, nested graph hydration, branch/projection scope, and
  unsupported-dialect failures.
- Exposed QuerySpec through model-level `query`, `first_query`, and
  `count_query` methods, backed by an optional structured session/backend hook
  with SQL-generation fallback.
- Added generated-model query builder ergonomics with `Model.f.<field>` field
  refs and `Model.query().where(...).order_by(...).limit(...).all/first/count`
  so services can express advanced reads without raw SQLGenerator or
  string-heavy QuerySpec setup.
- Added agent-first exact-match read helpers with `Model.by_id(...)`,
  `Model.one(...)`, `Model.first(...)`, `Model.where(...).all()`, and
  `Model.many(...)`, all compiled through the QuerySpec-backed builder path for
  service/ontology-replica consumers.
- Added chainable exact-match query composition helpers with
  `query.match(...)`, `query.match_if_present(...)`, `query.match_when(...)`,
  and `query.match_unless(...)` so service consumers can append optional
  filters without field-ref ceremony while preserving explicit advanced
  predicates.
- Proved the same service-owned query corpus against SQLite and PostgreSQL, with
  optional Postgres migration/runtime proof kept outside the base install.

### Public Documentation

- Reworked the README into the release-facing public contract for the ORM:
  install posture, package boundary, generated-model query ergonomics,
  service ontology-replica usage, session ownership, DB boot/runtime artifacts,
  compatibility notes, release gates, and the future semantic-contract
  publication direction.

### Release Evidence

- Focused public boundary gate: `8 passed`.
- Full ORM suite: `247 passed, 6 skipped`.
- TestPyPI publish/install smoke and final Git/PyPI release receipts remain the
  next release gates.
