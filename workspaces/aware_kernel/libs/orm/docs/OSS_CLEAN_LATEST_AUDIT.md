# Aware ORM OSS Clean Latest Audit

- Status: Active release gate
- Date: 2026-06-01
- Owner: `codex-019e6d23-98b4-7b43-8fed-2ae28a09fb1f`
- Issue: `docs/issues/2026/06/01/fb-2026-06-01-aware-orm-oss-clean-latest-audit-v0.md`

This audit classifies what `aware-orm` exposes for OSS/PyPI now, what is
monorepo-only compatibility source, and what must not be treated as current
release guidance.

## Current Public Surface

The release-front public surface is the minimal ORM kernel:

- `aware_orm`: top-level model and typed query exports.
- `aware_orm.models`: base ORM model, query/CRUD/relationship/branch mixins.
- `aware_orm.session`: branch-aware sessions, context injection, backends.
- `aware_orm.db`: current DB boot planning/execution contracts and adapters.
- `aware_orm.local_state`: SQLite local state contracts and helpers.
- `aware_orm.runtime`: package-local artifact install/binding/metadata sinks.
- `aware_orm.runtime.graph_artifacts`: ORM-owned graph artifact DTOs for package
  binding snapshots.
- `aware_orm.runtime.graph_binding`: package binding loader for ORM graph
  artifacts.
- `aware_orm.query_spec` and `aware_orm.query.graph_spec`: public query AST and
  graph retrieval contracts.
- `aware_orm.projection.plan`, `aware_orm.projection.runtime`, and
  `aware_orm.projection.serialization`: generic projection primitives.

Base install dependencies remain only `pydantic` and `python-dotenv`.
Postgres drivers remain behind `aware-orm[postgres]`.
There is no public `bootstrap` extra.

## Monorepo-Only Compatibility Source

These surfaces may still exist in the private monorepo or history for older
workspace rails, but they are not OSS/PyPI release-front APIs:

| Surface | Classification | Rationale |
| --- | --- | --- |
| `aware_orm.bootstrap` | Legacy kernel/workspace bootstrap adapter, excluded from public artifacts | Uses SQL grammar and older kernel bootstrap concepts. New public callers should use `aware_orm.db`; the bootstrap package and `bootstrap` extra are no longer shipped. |
| `aware_orm.runtime.bundle_runtime_install` | Structure adapter bridge | Lazily imports Structure only when a Structure environment bundle install is explicitly requested. Package-local runtime artifacts remain the public rail. |
| `aware_orm.projection.projector` | Removed public shim | Meta owns OIG commit/change interpretation. Projector tests live under Meta and import `aware_meta.graph.instance.orm_projector` directly. ORM owns only generic projection primitives. |
| `aware_orm.load.lazy_relationship` | Removed legacy loader | The old loader consumed object-config relationship shapes directly. Current relationship/query behavior is driven by ClassConfig binding metadata and package-local relationship metadata registries. |
| `aware_orm.runtime.binding_dtos` and `aware_orm.runtime.ocg_orm_binding` | Removed producer-shaped binding rail | Meta translates ObjectConfigGraph/ClassConfig producer shapes into ORM graph artifacts. ORM loads only `aware_orm.runtime.graph_artifacts` / `aware_orm.runtime.graph_binding`. |
| `aware_orm.graph.builders` and `aware_orm.projection.builders` | Moved to Meta-owned adapters | GraphSQL/projection plan construction from ontology producer models now lives under `aware_meta.orm_artifacts`; ORM keeps graph/projection primitives only. |
| `Session.switch_session` runtime/Structure probing | Removed from ORM internals | Runtime and host packages integrate through explicit `SessionContext` injection instead of package-name probing from ORM. |

## Historical Or Repo-Only Material

The current release guidance is limited to:

- `README.md`
- `CHANGELOG.md`
- `docs/ORM_RELEASE_READINESS_MATRIX.md`
- this audit

The remaining component notes under `docs/cache`, `docs/session`, `docs/graph`,
and `docs/models` are retained because live ORM source files reference them via
`# @doc-ref`; they are implementation notes, not broad release guidance.

Older status, roadmap, deployment, test-architecture, success-report, metaclass,
and Repository-era query docs were removed from the ORM public docs tree before
TestPyPI.

PyPI artifacts must not ship legacy bootstrap adapters, repo-only docs/tests/
scripts, or local caches. The sdist/wheel policy is now explicit in
`pyproject.toml`:

- include package source, README, changelog, license, and `pyproject.toml`;
- exclude `aware_orm/bootstrap`, `docs`, `tests`, `scripts`, `.pytest_cache`,
  `__pycache__`, and `*.pyc`.

## Findings

1. The wheel was already narrow: package source plus README/changelog/license.
2. The pre-audit sdist was too broad: it included repo-only docs, tests, and the
   Postgres proof script. Several of those files depend on monorepo-only
   ontology/runtime packages and are not suitable as PyPI source-release
   guidance.
3. Ignored `__pycache__` and `.pytest_cache` directories existed locally under
   `workspaces/aware_kernel/libs/orm`, but `.gitignore` ignores them and the
   artifact gate now asserts they do not enter wheel or sdist outputs.
4. `aware_orm.bootstrap.__init__` eagerly imported legacy bootstrap manager
   modules, which pulled History ontology on namespace import. This is now lazy
   so `import aware_orm.bootstrap` remains base-boundary clean.
5. The deprecated-surface removal pass deleted the remaining Repository-era,
   production-status, roadmap, test-architecture, and old DB-installer spec
   docs from the ORM public docs tree.
6. The deprecated-surface removal pass removed the public `bootstrap` extra,
   excluded `aware_orm/bootstrap` from wheel/sdist artifacts, and deleted the
   remaining stale historical docs from the ORM docs tree.
7. The binding/terminology cleanup removed the ORM projector shim, removed the
   legacy lazy relationship loader, moved projector behavior tests to Meta, and
   made CRUD persistence require class-FQN SQLRuntimeMetadata instead of
   guessing from ClassConfig table hints.
8. The native graph artifact pass removed the remaining producer-shaped binding
   DTO modules and moved ObjectConfigGraph/ClassConfig conversion into
   Meta-owned `aware_meta.orm_artifacts` adapters. The package artifact filename
   is now `_aware/orm.graph.binding.msgpack`.
9. The public release-prep pass removed the remaining Runtime/Structure
   session-switch probing from ORM internals. `switch_session()` now delegates to
   the ORM-owned `SessionContext` abstraction.

## Validation

- `uv run pytest -q workspaces/aware_kernel/libs/orm/tests/runtime/test_public_boundary.py`
  passed: `8 passed`.
- `uv build --package aware-orm --out-dir /tmp/aware-orm-deprecated-removal-dist-final`
  produced `aware_orm-1.0.0.tar.gz` and `aware_orm-1.0.0-py3-none-any.whl`.
- Built sdist excludes `aware_orm/bootstrap`, `docs/`, `tests/`, `scripts/`,
  `.pytest_cache`, `__pycache__`, and `*.pyc`.
- Built wheel/sdist exclude `aware_orm.projection.projector` and
  `aware_orm.load.lazy_relationship`.
- Built wheel/sdist exclude `aware_orm.runtime.binding_dtos`,
  `aware_orm.runtime.ocg_orm_binding`, `aware_orm.graph.builders`, and
  `aware_orm.projection.builders`.
- `uv build --package aware-orm --out-dir /tmp/aware-orm-native-graph-artifact-dist`
  produced `aware_orm-1.0.0.tar.gz` and `aware_orm-1.0.0-py3-none-any.whl`.
- `uv run pytest -q workspaces/aware_kernel/libs/orm/tests` passed:
  `233 passed, 6 skipped`.
- `uv run pytest -q modules/meta/runtime/tests/orm_artifacts modules/meta/runtime/tests/test_meta_materialization_workspace_provider.py modules/meta/runtime/tests/test_meta_workspace_materialize_compile_parity.py modules/meta/runtime/tests/test_object_config_graph_language_plugin_materialization_service.py`
  passed: `62 passed`.
- `uv run pytest -q modules/structure/runtime/tests/test_manifest_writer.py modules/structure/runtime/tests/test_environment_bundle.py modules/structure/runtime/tests/test_graphsql_loader.py modules/structure/runtime/tests/test_serialize_bindings.py modules/structure/runtime/tests/test_environment_db_artifact_receipt.py modules/structure/runtime/tests/test_environment_composition_db_schema_registry.py`
  passed: `19 passed`.
- `uv run pytest -q libs/environment-artifacts/tests/test_python_package_bootstrap_and_binding.py libs/environment-artifacts/tests/test_pipeline_compiler_attach.py libs/environment-artifacts/tests/test_environment_bootstrap_runtime_artifacts.py libs/environment-artifacts/tests/test_cli_runtime_artifact_contract.py libs/environment-artifacts/tests/test_lock_external_dependency_resolution.py`
  passed: `18 passed`.

## Release Recommendation

`aware-orm` is clean enough to continue to clean-venv and TestPyPI install
smoke after the artifact gate and public boundary tests pass. `aware_orm.bootstrap`
is not a public DB boot API and is not shipped in public artifacts.
`aware_orm.projection.projector` is removed; Meta is the only OIG projector
owner. Public docs should point to `aware_orm.db`, package-local ORM graph
artifacts, QuerySpec/GraphSpec, SQLite/Postgres backends, Meta-owned
ontology-to-ORM translators, the explicit `SessionContext` runtime integration
point, and the service-state E2E proof.
