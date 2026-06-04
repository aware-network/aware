# QueryMixin Graph Retrieval

`aware_orm.models.query_mixin.QueryMixin` exposes row and graph retrieval over
committed projection/state stores.

Current public contract:

- Query behavior is expressed through typed query/graph contracts.
- Default eager reads stay backend-aware: SQLite/fs/noop avoid Postgres-only
  GraphSQL generation, while explicit unsupported graph calls fail fast.
- Hydrated rows reuse the session identity map where possible.
- Ontology mutation handlers must use OIG/pre-state or service-owned read
  models; ORM SQL reads are for committed projection/state retrieval.

Validation lives in `workspaces/aware_kernel/libs/orm/tests/graph` and
`workspaces/aware_kernel/libs/orm/tests/runtime`.
