# ORM Base Model And CRUD Mixins

`aware_orm.models` provides the public model base and mixins used by generated
ORM model packages.

Current public contract:

- `BaseORMModel` owns identity, branch context, session binding, runtime SQL
  metadata lookup, and model introspection helpers.
- `CRUDMixin` stages insert/update/delete SQL through the active `Session`.
- `QueryMixin` owns retrieval helpers; query behavior is specified through the
  public query contracts rather than a deprecated Repository facade.
- Relationship and branch mixins remain ORM primitives for generated models.

Validation lives in `workspaces/aware_kernel/libs/orm/tests/models`,
`workspaces/aware_kernel/libs/orm/tests/session`, and
`workspaces/aware_kernel/libs/orm/tests/runtime`.
