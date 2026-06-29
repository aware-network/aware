# Aware ORM Release Readiness Matrix

- Status: Active
- Owner: `codex-019e6d23-98b4-7b43-8fed-2ae28a09fb1f`
- Tracking issue: `docs/issues/2026/05/31/fb-2026-05-31-aware-orm-release-readiness-matrix-v0.md`
- Architecture review: `docs/issues/2026/05/31/fb-2026-05-31-aware-orm-architecture-test-review-recommendations-v0.md`
- Selected-kernel admission: `docs/issues/2026/05/31/fb-2026-05-31-aware-kernel-orm-selected-workspace-admission-v0.md`

This matrix is the tick-through surface for making `aware-orm` ready for Git
release and PyPI publication as the first public Aware Python package.

The honest release posture is:

- public minimal ORM core: package release-candidate;
- selected-kernel workspace package: admitted;
- service advanced-query substrate: release-candidate now that the P0 query
  gates below passed; still subject to TestPyPI/release gates.

## Product Rail Lock

The public ORM rail is:

```text
Aware ontology/state package artifacts
-> Meta-owned ontology-to-ORM graph artifact translators
-> package-local SQL/registry/projection artifacts
-> aware-orm DB boot + runtime metadata binding
-> branch-aware Session + SQLite/Postgres backends
-> QuerySpec/GraphSQL retrieval over committed projection/state stores
-> service/local consumers
```

The projection rail is:

```text
Meta OIG commit/change truth
-> Meta-owned OIG interpretation/projector lane
-> ORM projection primitives
-> SQL projection rows
-> read-only retrieval/query surface
```

ORM must not interpret OIG commits as a dependency direction. Meta/Structure
prepare public DTOs, bundles, registries, or projection plans and call the ORM
core. ORM remains the installable SQL/session/projection primitive package.
ORM graph binding artifacts are ORM-owned representation; Meta translates
ObjectConfigGraph/ClassConfig producer shapes into that representation.

## Hard Quarantine

| Rail | Current status | Release rule |
| --- | --- | --- |
| Base package importing Aware ontologies, Meta runtime, Structure runtime, services, or internal utilities | Guarded by public boundary tests | Base wheel must stay client-installable without these packages. |
| Ontology mutation querying SQL as truth | Forbidden direction | Ontology mutation may use identity-map/pre-state introspection; SQL is a committed projection/retrieval index. |
| ORM importing OIG commit internals | Inverted out of ORM | Meta owns OIG commit/change interpretation and calls ORM projection primitives. |
| ORM exposing Meta projector shim | Removed | `aware_orm.projection.projector` is not a public package module; Meta tests import the Meta projector directly. |
| ORM exposing ObjectConfigGraph/ClassConfig adapter modules | Removed | `aware_orm.runtime.binding_dtos`, `aware_orm.runtime.ocg_orm_binding`, `aware_orm.graph.builders`, and `aware_orm.projection.builders` are absent from public artifacts; Meta owns producer-model conversion under `aware_meta.orm_artifacts`. |
| CRUD deriving SQL tables from ObjectConfig/ClassConfig table hints | Removed | Persistence requires package-local SQLRuntimeMetadata registered for the model class FQN. |
| SQLite entering Postgres-only eager GraphSQL | Guarded | Default eager reads fall back to row queries on SQLite/fs/noop; explicit GraphSQL calls fail fast on unsupported backends until dialect-specific generators exist. |
| Stale production-positioning docs | Removed from public ORM docs tree | Public docs must not overstate release or production readiness. |
| Legacy bootstrap adapter in public artifacts | Removed | `aware_orm.bootstrap` and the `bootstrap` extra are not shipped in public wheel/sdist artifacts. |
| Optional Postgres drivers in base install | Guarded | `asyncpg` and `psycopg2-binary` remain behind `aware-orm[postgres]`. |

## Readiness Matrix

| Order | Area | Status | Acceptance gate | Tracking |
| ---: | --- | --- | --- | --- |
| 1 | Consumer boundary clarification | Done | ORM does not depend on Meta/Structure/service internals for the base install; producer-owned integration direction is recorded. | `docs/issues/2026/05/28/fb-2026-05-28-aware-orm-clean-consumer-boundary-clarification-v0.md` |
| 2 | Meta/Structure projection inversion | Done | Meta owns OIG commit/change interpretation and calls ORM projection primitives; ORM no longer ships a projector shim. | `docs/issues/2026/06/01/fb-2026-06-01-aware-orm-binding-dto-terminology-cleanup-v0.md` |
| 3 | Release honesty metadata/docs | Done | License, PyPI metadata, README boundary, optional Postgres extra, wheel file inclusion, and public import gates are recorded and tested. | `docs/issues/2026/05/31/fb-2026-05-31-aware-orm-release-readiness-honesty-v0.md` |
| 4 | Public boundary test gate | Done | Built wheel verifies allowed base dependencies, optional Postgres drivers, included README/changelog/license, and clean public imports. | `workspaces/aware_kernel/libs/orm/tests/runtime/test_public_boundary.py` |
| 5 | Full ORM baseline suite | Done | Full ORM suite passes from the selected-kernel path: `247 passed, 6 skipped`. | `docs/issues/2026/06/03/fb-2026-06-03-aware-orm-model-query-builder-ergonomics-v0.md` |
| 6 | Selected-kernel workspace admission | Done | `aware-orm` lives under `workspaces/aware_kernel/libs/orm`, selected-kernel workspace planning resolves it as an `aware_code` Python package, and bridge root selection is removed. | `docs/issues/2026/05/31/fb-2026-05-31-aware-kernel-orm-selected-workspace-admission-v0.md` |
| 7 | DB boot registry/install rail | Done | Registry-driven SQL install plans support generated multi-table SQL and SQLite/Postgres adapter selection. | `docs/issues/2026/05/29/fb-2026-05-29-aware-orm-public-release-test-gates-v0.md` |
| 8 | SQLite session/local-state foundation | Done | SQLite backend and local-state helpers cover config, commit/read/update/delete, memory DB, rollback, schema health, repair, and drift fail-closed paths. | `workspaces/aware_kernel/libs/orm/tests/session/test_sqlite_backend.py` |
| 9 | Postgres optional adapter boundary | Done | Base import does not import Postgres drivers; Postgres drivers are exposed only through `aware-orm[postgres]`. | `workspaces/aware_kernel/libs/orm/tests/runtime/test_public_boundary.py` |
| 10 | Postgres migration/runtime CI proof | Done | CI or opt-in container lane runs Postgres migration/query tests with explicit environment receipts. | `docs/issues/2026/05/31/fb-2026-05-31-aware-orm-postgres-ci-container-proof-v0.md` |
| 11 | QueryMixin collection test hygiene | Done | The uncollected `get_list_uses_canonical_metadata` test is renamed with a `test_` prefix and runs in focused ORM tests. | `docs/issues/2026/05/31/fb-2026-05-31-aware-orm-query-readiness-p0-v0.md` |
| 12 | Ontology mutation read-barrier proof | Done | `Session.execute_query` is directly tested to reject DB reads in write execution mode. | `docs/issues/2026/05/31/fb-2026-05-31-aware-orm-query-readiness-p0-v0.md` |
| 13 | Eager graph dialect safety | Done | SQLite/fs/noop default eager reads fall back to row queries, and explicit GraphSQL calls reject unsupported backends before Postgres SQL generation. | `docs/issues/2026/05/31/fb-2026-05-31-aware-orm-query-readiness-p0-v0.md` |
| 14 | Service query conformance | Done | Same service-owned schema/query corpus passes against SQLite and Postgres with equivalent results: equality, range, like, in/gte, null, pagination, many-to-many relation path, and count. | `docs/issues/2026/05/31/fb-2026-05-31-aware-orm-service-query-conformance-v0.md` |
| 15 | Advanced filter semantics | Done | Equality, range, like, in, null, AND/OR grouping, sorting, pagination, relation paths, and many-to-many traversal have a single tested contract. | `docs/issues/2026/05/31/fb-2026-05-31-aware-orm-queryspec-contract-v0.md` |
| 16 | QuerySpec AST contract | Done | Public typed query AST compiles through safe metadata-bound identifiers, backend/dialect emitters, and explicit unsupported-operator failures. | `docs/issues/2026/05/31/fb-2026-05-31-aware-orm-queryspec-contract-v0.md` |
| 16.1 | QuerySpec model API contract | Done | Generated ORM models expose strict `query`, `first_query`, and `count_query` methods; Session exposes a structured QuerySpec backend hook with SQL fallback so service consumers do not call SQLGenerator directly. | `docs/issues/2026/06/02/fb-2026-06-02-aware-orm-queryspec-model-api-contract-v0.md` |
| 16.2 | Model query builder ergonomics | Done | Generated ORM models expose `Model.f.<field>` field refs and a fluent `Model.query().where(...).order_by(...).limit(...).all/first/count` API that compiles to `QuerySpec`. | `docs/issues/2026/06/03/fb-2026-06-03-aware-orm-model-query-builder-ergonomics-v0.md` |
| 16.3 | Agent-first exact-match ergonomics | Done | Generated ORM models expose `by_id`, `one`, `first`, `where`, `many`, and chainable `match` helpers for service/ontology-replica exact-match reads without raw QuerySpec or SQLGenerator calls. | `docs/issues/2026/06/15/fb-2026-06-15-aware-orm-agent-first-query-sugar-v0.md`, `docs/issues/2026/06/15/fb-2026-06-15-aware-orm-chainable-match-ergonomics-v0.md` |
| 17 | Graph retrieval contract | Done | Backend-aware graph SQL supports nested relationships, cardinality, depth/cycle policy, branch/projection scope, and identity-map reuse. | `docs/issues/2026/05/31/fb-2026-05-31-aware-orm-graph-retrieval-contract-v0.md` |
| 18 | Service-state E2E proof | Done | Service-owned OCG/state package installs a local SQLite schema, seeds rows, runs dynamic queries, and reports health/drift receipts. | `docs/issues/2026/05/31/fb-2026-05-31-aware-orm-service-state-e2e-v0.md` |
| 19 | Public docs cleanup | Done | Stale production-positioning and Repository-era docs are removed from the public ORM docs tree before OSS publication. | `docs/issues/2026/06/01/fb-2026-06-01-aware-orm-deprecated-surface-removal-v0.md` |
| 19.1 | Public README release contract | Done | README is structured as the public package contract: install posture, package boundary, generated-model query ergonomics, service ontology-replica usage, session ownership, DB boot/runtime artifacts, compatibility notes, release gates, and future semantic-contract publication direction. | `docs/issues/2026/06/17/fb-2026-06-17-aware-orm-public-readme-release-pass-v0.md` |
| 20 | Build artifact audit | Done | `uv build --package aware-orm` from the selected-kernel path produces a narrow wheel and sdist: package source plus README/changelog/license/metadata, with `aware_orm/bootstrap`, repo-only docs/tests/scripts, and caches excluded. | `docs/issues/2026/06/01/fb-2026-06-01-aware-orm-deprecated-surface-removal-v0.md` |
| 21 | Binding DTO / terminology cleanup | Done | Persistence requires class-FQN SQLRuntimeMetadata, removed shims/loaders are absent from public artifacts, and stale object-config terminology is out of ORM runtime APIs. | `docs/issues/2026/06/01/fb-2026-06-01-aware-orm-binding-dto-terminology-cleanup-v0.md` |
| 22 | Native ORM graph artifact boundary | Done | ORM owns `graph_artifacts` / `graph_binding` and `_aware/orm.graph.binding.msgpack`; Meta owns ObjectConfigGraph/ClassConfig to ORM artifact translation; Python plugin writes package artifacts; Structure writes environment bundle artifacts; API/DTO workspace package rendering does not fall through to committed-OIG hydration. | `docs/issues/2026/06/01/fb-2026-06-01-aware-orm-native-graph-artifact-contract-v0.md` |
| 23 | TestPyPI dry run | Not started | Package can be published to TestPyPI and installed into a clean venv with base and `postgres` extra variants. | TBD |
| 24 | Git/PyPI release | Not started | Release tag, changelog, GitHub release notes, PyPI publish, and post-install smoke are complete. | TBD |

## Current Prep Receipt

2026-06-02 release-prep pass:

- `aware_orm.session.switch_session` no longer probes Runtime or Structure
  package names; runtimes integrate by registering an ORM `SessionContext`.
- `CHANGELOG.md` now records the 2026 public release-candidate surface and the
  remaining TestPyPI/Git/PyPI gates.
- `QuerySpec` is now exposed through generated model methods and an optional
  structured backend hook, locking the Service consumer boundary before the
  Service-owned replica proof resumes.
- The preferred Service consumer shape is now a generated-model query builder
  over `QuerySpec`, keeping `QuerySpec` stable for adapters while giving service
  authors field-ref ergonomics.
- Focused public boundary gate passed: `8 passed`.
- Full ORM suite passed from the selected-kernel path: `247 passed, 6 skipped`.

2026-06-17 public README release pass:

- README now leads with public install/release posture, package boundary,
  generated-model read ergonomics, service ontology-replica usage, host/session
  ownership, DB boot/runtime artifacts, compatibility notes, and release gates.
- The agent-first query surface is documented as the preferred service
  consumer contract: `by_id`, `one`, `first`, `where`, `many`, `match`,
  `match_if_present`, `match_when`, and `match_unless`.
- README records the future semantic-contract publication direction without
  making semantic metadata a current runtime dependency.
- TestPyPI and Git/PyPI release rows remain `Not started`.

## Release Gates

### Minimal Public Core

- Base package installs without Aware ontology, Meta, Structure, runtime,
  service, internal utility, or Postgres driver dependencies.
- Public imports succeed from built wheel:
  - `aware_orm`
  - `aware_orm.models`
  - `aware_orm.session`
  - `aware_orm.db`
  - `aware_orm.runtime`
  - `aware_orm.local_state`
- README, changelog, and license are included in wheel/sdist.
- `aware_orm.bootstrap`, repo docs, tests, scripts, and caches are excluded
  from public wheel/sdist artifacts.
- `aware_orm.projection.projector` and `aware_orm.load.lazy_relationship` are
  absent from public wheel/sdist artifacts.
- `aware_orm.runtime.binding_dtos`, `aware_orm.runtime.ocg_orm_binding`,
  `aware_orm.graph.builders`, and `aware_orm.projection.builders` are absent
  from public wheel/sdist artifacts and import probes.
- Package binding uses `_aware/orm.graph.binding.msgpack`; Meta-owned
  translators are the only ObjectConfigGraph/ClassConfig-to-ORM artifact
  producers.
- CRUD persistence uses SQLRuntimeMetadata registered by model class FQN; it does
  not guess SQL tables from ClassConfig table hints.
- Full ORM suite passes from `workspaces/aware_kernel/libs/orm/tests`.
- Selected-kernel workspace materialization plans `aware-orm` as a code package.

### Service Query Readiness

- Query behavior is specified through a typed public contract, not ad hoc
  filter lists.
- SQLite and Postgres execute the same query corpus with equivalent results.
- Eager graph retrieval is backend-aware.
- Relation paths, many-to-many joins, sorting, pagination, counts, and nested
  hydration are covered by actual backend tests.
- Ontology mutation read barriers prevent SQL reads during write execution mode.

### Git/PyPI Release

- Public docs do not overstate production/service-query readiness.
- Root and selected-kernel package paths are consistent in build/test docs.
- Build artifacts install into clean virtual environments.
- TestPyPI install smoke passes for base and `postgres` extra.
- Git tag/release notes state the honest posture:
  - public minimal ORM core available;
  - service advanced-query contract has passed rows 10-18;
- PyPI publication remains gated by rows 23-24 until TestPyPI/release receipts
    are complete.

## Tick Rules

- Mark a row `Done` only when the acceptance gate has a committed receipt.
- Rows 10-18 are the completed "service advanced-query ready" gate.
- Keep rows 23-24 blocking for "PyPI release ready".
- Do not move Git/PyPI release to `Done` while public docs or README command
  paths point at stale package locations.
