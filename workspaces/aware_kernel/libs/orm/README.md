# aware-orm

`aware-orm` is the installable Python ORM core for Aware generated model
packages, projection indexes, branch-aware sessions, and package-local runtime
artifacts.

It is not a standalone generic ORM. In Aware, domain truth is carried by
Object Instance Graph commits and generated package artifacts. SQL databases are
rebuildable read/projection indexes owned by a runtime host.

## Release Posture

This package is a public release candidate for the Aware ORM core.

The current release truth is this README plus:

- `docs/ORM_RELEASE_READINESS_MATRIX.md`
- `docs/OSS_CLEAN_LATEST_AUDIT.md`
- `CHANGELOG.md`

Current status:

- The base install boundary is release-gated and does not import Aware
  ontology, Meta, Structure, runtime, service, internal utility, or PostgreSQL
  driver packages.
- The public generated-model query surface is ready for service and ontology
  replica consumers.
- SQLite service-state reads, QuerySpec reads, graph retrieval, DB boot, and
  PostgreSQL proof rails are covered by focused tests.
- PyPI publication is still gated by TestPyPI install smoke, release tag/notes,
  final publish checks, and post-install receipts.

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
`postgres` extra. There is no public `bootstrap` extra.

## Public Contract

`aware-orm` owns:

- base model and generated-model mixins;
- branch-aware `Session` behavior and pluggable persistence backends;
- identity-map, read-barrier, CRUD queueing, rollback, and backend selection;
- generated-model query helpers over the stable `QuerySpec` contract;
- package-local runtime artifact installation from generated `_aware`
  artifacts;
- DB boot planning/execution for generated SQL roots;
- projection/runtime primitives that producer packages can call.

`aware-orm` does not own:

- ontology truth or OIG commit semantics;
- ServiceHost, Environment, Node, Workspace, or Meta orchestration;
- source `.aware` parsing or semantic materialization;
- application-specific service logic;
- direct public use of raw SQL generator internals for service reads.

## Generated Model Reads

Services should use generated ORM model methods for common exact-match reads.
These methods compile to `QuerySpec` and execute through the active ORM session.

```python
customer = await Customer.by_id(customer_id)
order = await Order.one(id=order_id)

active_orders = await Order.where(
    customer_id=customer_id,
    status="active",
).all()

active_count = await Order.where(status="active").count()
```

Use this surface first for agent-authored service code:

- `Model.by_id(id)` for primary identity reads.
- `Model.one(...)` / `Model.first(...)` for one exact-match row.
- `Model.where(...).all()` for a chainable exact-match query.
- `Model.many(...)` for a direct list read.
- `Model.where(...).count()` for counts.

## Chainable Filters

Start with `Model.where(...)`, then append exact-match filters with the
chainable `match` helpers:

```python
orders = await (
    Order.where(customer_id=customer_id)
    .match(status="active")
    .match_if_present(region_id=request.region_id)
    .match_when(request.include_priority, priority="high")
    .match_unless(request.include_archived, archived=False)
    .order_by(Order.f.created_at.desc())
    .limit(25)
    .all()
)
```

Rules:

- `match(...)` appends exact equality predicates.
- `match_if_present(...)` skips only values that are `None`.
- `False`, `0`, and `""` are real filter values and are not skipped.
- `match_when(...)` and `match_unless(...)` make conditional equality filters
  explicit without caller-side `if` blocks.
- Field names are validated against generated model fields.
- Plain `where(...)` and `match(...)` do not skip `None`; use
  `match_if_present(...)` when absence should mean "do not filter".

## Advanced Predicates

Use field refs for comparisons, ranges, relation paths, ordering, and other
advanced predicates:

```python
orders = await (
    Order.where(status="active")
    .where(Order.f.total.gte(50))
    .where(Order.f.relation("items").sku.eq("ABC123"))
    .order_by(Order.f.created_at.desc())
    .limit(25)
    .all()
)
```

This is still `QuerySpec` backed. The explicit field-ref builder exists for
advanced predicates; the exact-match helpers exist for the common service path.

## Service Ontology Replicas

Service ontology replicas should treat ORM sessions as read projection sessions.
The service owns a local projection DB, advances it from Environment fanout
commits, and queries generated ontology ORM models through the same public model
methods:

```python
identity = await Identity.by_id(identity_id)

members = await (
    SessionMember.where(session_id=session_id)
    .match(status="active")
    .all()
)
```

Consumers should not materialize commit history for normal reads. They should
query the local ontology replica DB through generated ORM models. Mutation
authority stays with ontology/service APIs and commit fanout; service-local ORM
replica sessions are read-only projection sessions.

## QuerySpec

`QuerySpec` is the stable lower-level query contract for adapters, backends, and
serialized query plans:

```python
from aware_orm.filters import EqFilter
from aware_orm.query_spec import QuerySpec

rows = await Order.query(QuerySpec(where=EqFilter(column="status", value="active")))
```

Most service code should not construct `QuerySpec` directly. Prefer generated
model helpers and the query builder. Backends can implement the structured
`execute_query_spec` hook; otherwise ORM sessions use metadata-bound SQL
generation as a fallback.

## Sessions And Hosts

Generated model reads require an active ORM session. Runtime hosts are
responsible for creating and binding that session:

- ServiceHost binds service ontology-replica sessions.
- Environment/Node/Workspace lanes can register generated package artifacts and
  session contexts.
- Tests can bind sessions directly through the ORM session context helpers.

The ORM package defines the session primitives; it does not boot an Aware
environment by itself.

## DB Boot And Runtime Artifacts

Public DB boot planning and execution live under `aware_orm.db`. Package-local
runtime artifact installation lives under `aware_orm.runtime`.

Generated package artifacts provide:

- ORM model manifests;
- ORM graph binding snapshots;
- SQL metadata;
- relationship metadata;
- SQL roots for DB boot.

Legacy SQL grammar/bootstrap modules are monorepo compatibility rails and are
excluded from public PyPI wheel/sdist artifacts. New public callers should use
`aware_orm.db` and `aware_orm.runtime`.

## Base Package Boundary

Public imports covered by release tests include:

- `aware_orm`
- `aware_orm.models`
- `aware_orm.session`
- `aware_orm.db`
- `aware_orm.runtime`
- `aware_orm.local_state`

Those imports are tested to avoid importing:

- `aware_meta`
- `aware_meta_ontology`
- `aware_runtime`
- `aware_structure`
- `aware_utils`
- `services`
- `asyncpg`
- `psycopg2`
- `tomli`

Compatibility modules can consume producer-provided generated artifacts when
those artifacts are installed by a host. Producer packages remain responsible
for translating Aware semantics into ORM artifacts before calling ORM core
primitives.

## External Aware Integration Points

Runtime hosts provide the roots and artifacts that ORM needs. Public ORM runtime
code must not discover an Aware source repository from cwd or parent-directory
markers.

- Persistent filesystem state uses explicit `AWARE_ROOT`.
- Environment manifests come from explicit paths or paths relative to
  `AWARE_ROOT`.
- Generated model, SQL, and graph-binding artifacts come from installed package
  resources or host-provided artifact directories.
- Source checkout discovery is limited to local bootstrap/generation tooling and
  proof scripts, not remote runtime.

## Semantic Contract Direction

This README is the current public documentation source for the ORM consumer
contract. The same contract should later be exposed through Aware semantic
contract metadata so agents and services can discover it programmatically.

The intended semantic-contract shape is:

- package boundary: what the base install owns and does not import;
- generated-model query surface: `by_id`, `one`, `where`, `many`, `match`,
  `match_if_present`, `match_when`, `match_unless`;
- advanced predicate surface: `Model.f.<field>` refs and relation paths;
- session ownership: hosts bind sessions, ORM executes reads;
- replica policy: service ontology replica sessions are read projections, not
  mutation authority.

Until that metadata exists, treat this README and the release readiness matrix
as the public contract.

## Compatibility Notes

Legacy generated-model helpers such as `get_by_id(...)`, `get(...)`,
`get_list(...)`, `find(...)`, `find_all(...)`, `batch_get(...)`,
`exists(...)`, and class-level `count(...)` are compatibility-only. Do not use
them in new service ontology-replica or product service code; they can route
through generated SQL strings or implicit eager GraphSQL.

Preferred new code:

- `by_id(...)`
- `one(...)`
- `where(...).all()`
- `many(...)`
- `where(...).count()`
- chainable `match(...)` helpers

Callers should not invoke `SQLGenerator` directly for service reads.

## Release Gates

The public release gate builds the wheel and verifies:

- base wheel metadata has only the allowed base dependencies;
- PostgreSQL drivers are exposed only through the `postgres` extra;
- README, changelog, and license files are included in wheel/sdist artifacts;
- repo-only docs, tests, scripts, caches, and legacy bootstrap modules are
  excluded from public artifacts;
- public imports do not import Aware ontology/runtime/structure/service
  internals or optional PostgreSQL drivers;
- generated SQL files are accepted by DB boot planning and execution tests;
- generated-model query reads are available through public model methods and
  the `QuerySpec` backed builder, not raw SQL generator calls.

Run the focused public gate:

```bash
uv run pytest -q workspaces/aware_kernel/libs/orm/tests/runtime/test_public_boundary.py
```

Run the full ORM suite:

```bash
uv run pytest -q workspaces/aware_kernel/libs/orm/tests
```

Run the PostgreSQL proof from the package root with a local/admin database URL:

```bash
cd workspaces/aware_kernel/libs/orm
AWARE_DB_TEST_ADMIN_URL=postgresql://user:password@localhost:5432/postgres \
  uv run --extra postgres python scripts/run_postgres_ci_proof.py \
  --receipt-path /tmp/aware-orm-postgres-ci-proof.json
```

## License

MIT. See `LICENSE`.
