# aware-orm

`aware-orm` is the installable Python ORM core for Aware projection indexes,
branch-aware sessions, and package-local runtime artifacts.

It is intentionally not a standalone generic ORM. Aware domain truth is carried
by OIG commits and generated package artifacts; SQL is a rebuildable projection
and retrieval index.

## Current Release Posture

The current public release truth is this README plus
`docs/ORM_RELEASE_READINESS_MATRIX.md` and
`docs/OSS_CLEAN_LATEST_AUDIT.md`.

- Base install boundary is release-gated and does not import Aware ontology,
  Meta, Structure, runtime, service, internal utility, or Postgres driver
  packages.
- Service-query readiness rows 10-18 are complete, including SQLite service
  state, QuerySpec, graph retrieval, and Postgres migration/runtime proof.
- PyPI publication is still gated by TestPyPI install smoke, release tag/notes,
  and final publish checks.
- The PyPI wheel and sdist intentionally ship only package source, README,
  changelog, license, and packaging metadata. Legacy bootstrap adapters,
  repo-only docs, tests, scripts, cache files, and historical status reports
  stay out of PyPI artifacts.
- Historical status, roadmap, production, integration-testing, success-report,
  and Repository-era query architecture docs have been removed from the ORM
  public docs tree.

## Install

Base package:

```bash
pip install aware-orm
```

PostgreSQL adapters:

```bash
pip install "aware-orm[postgres]"
```

The base wheel depends only on:

- `pydantic`
- `python-dotenv`

`asyncpg` and `psycopg2-binary` are optional and are installed only through the
`postgres` extra. There is no public `bootstrap` extra in the OSS package.

## Base Package Boundary

The base package is client-installable without importing or requiring Aware
ontology, structure, runtime, service, or internal utility packages. Public
imports covered by release tests include:

- `aware_orm`
- `aware_orm.models`
- `aware_orm.session`
- `aware_orm.db`
- `aware_orm.runtime`
- `aware_orm.local_state`

Those imports are tested to avoid:

- `aware_meta`
- `aware_meta_ontology`
- `aware_runtime`
- `aware_structure`
- `aware_utils`
- `services`
- `asyncpg`
- `psycopg2`
- `tomli`

## What This Package Owns

- ORM base models and model registry.
- Branch-aware sessions and pluggable persistence backends.
- Query and graph-plan execution helpers for projection indexes.
- Strict `QuerySpec` model reads through `Model.query(...)`,
  `Model.first_query(...)`, and `Model.count_query(...)`.
- Ergonomic generated-model query builders through `Model.query().where(...).all()`.
- DB boot planning and execution over generated SQL roots.
- Package-local runtime artifact installation from `_aware` artifacts.
- Projection runtime primitives that can stage SQL projection writes.

## Model Query Reads

Services should use generated ORM model methods for advanced reads:

```python
orders = await (
    Order.query()
    .where(Order.f.status.eq("active"))
    .where(Order.f.total.gte(50))
    .order_by(Order.f.created_at.desc())
    .limit(25)
    .all()
)

count = await Order.query().where(Order.f.status.eq("active")).count()
first = await Order.query().where(Order.f.customer_id.eq(customer_id)).first()
```

This is the public service-consumer contract. Callers should not invoke
`SQLGenerator` directly. The builder compiles to the stable `QuerySpec`
contract; ORM sessions execute `QuerySpec` through an optional structured
backend hook when available, otherwise they generate metadata-bound SQL and
execute the normal read path.

`QuerySpec` remains available for lower-level adapters and serialized query
contracts:

```python
from aware_orm.filters import EqFilter
from aware_orm.query_spec import QuerySpec

rows = await Order.query(QuerySpec(where=EqFilter(column="status", value="active")))
```

## External Aware Integration Points

Some compatibility modules can consume Aware-generated ontology or structure
objects when a producer package provides them. Those producer packages are not
base `aware-orm` dependencies and are not imported by the public base surface.

Examples:

- Generated ontology DTO/config objects used by graph or projection plan
  builders.
- Structure environment bundles used by compatibility runtime installers.
- Meta-owned OIG commit or projector lanes that call into ORM projection
  primitives.

The direction is producer-owned integration: Meta/Structure lanes prepare
public DTOs, bundles, or projection plans, then call the ORM core. The ORM base
package must not reach into service internals as an installation requirement.

## PostgreSQL

PostgreSQL support is opt-in:

```bash
pip install "aware-orm[postgres]"
```

Without that extra, PostgreSQL-specific code raises a clear runtime error when
the adapter is used. Importing the base package does not import PostgreSQL
drivers.

## DB Boot

Current public DB boot planning and execution lives in `aware_orm.db` and the
package-local runtime artifact helpers under `aware_orm.runtime`.

Legacy SQL grammar/bootstrap adapters remain only in monorepo source for older
kernel/workspace rails. They are excluded from PyPI wheel and sdist artifacts.
New public callers should use `aware_orm.db`; `aware_orm.bootstrap` is not a
public release API.

## Release Gates

The public release gate builds the wheel and verifies:

- base wheel metadata has only the allowed base dependencies;
- SQL grammar/bootstrap adapters are not exposed in public artifacts;
- Postgres drivers are exposed only through the `postgres` extra;
- README, changelog, and license files are included in the wheel;
- `aware_orm.bootstrap`, repo docs, tests, scripts, and caches are excluded
  from wheel and sdist artifacts;
- public imports do not import Aware ontology/runtime/structure/service
  internals or optional PostgreSQL drivers;
- generated multi-table SQL files are accepted by DB boot planning and
  execution tests.
- `QuerySpec` service reads are available through generated ORM model methods,
  not raw SQL generator calls.
- Generated model query-builder reads are available as the preferred Service
  consumer API.

Run the focused public gate:

```bash
uv run pytest -q workspaces/aware_kernel/libs/orm/tests/runtime/test_public_boundary.py
```

Run the full ORM suite:

```bash
uv run pytest -q workspaces/aware_kernel/libs/orm/tests
```

Run the Postgres proof from the package root with a local/admin database URL:

```bash
cd workspaces/aware_kernel/libs/orm
AWARE_DB_TEST_ADMIN_URL=postgresql://user:password@localhost:5432/postgres \
  uv run --extra postgres python scripts/run_postgres_ci_proof.py \
  --receipt-path /tmp/aware-orm-postgres-ci-proof.json
```

## License

MIT. See `LICENSE`.
