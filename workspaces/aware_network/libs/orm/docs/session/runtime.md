# ORM Session Runtime

`aware_orm.session` is the public unit-of-work layer for branch-aware sessions,
identity-map access, pending SQL queues, and backend selection.

Current public contract:

- `Session` owns pending insert/update/delete queues and read execution.
- Backends implement the shared persistence protocol.
- SQLite, Postgres, filesystem, and no-op rails are backend selections, not
  separate public ORM models.
- SQL reads are blocked during write execution mode so ontology mutation does
  not treat projection DB state as truth.

Validation lives in `workspaces/aware_kernel/libs/orm/tests/session` and
`workspaces/aware_kernel/libs/orm/tests/runtime`.
