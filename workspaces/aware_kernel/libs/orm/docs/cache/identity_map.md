# Identity Map Semantics

`aware_orm.cache.identity_map` keeps one in-memory instance per `(class, id)`
inside a session and scopes that cache by branch.

Current public contract:

- `IdentityMap` owns class/id de-duplication.
- `SessionScopedIdentityMap` adds branch context and branch statistics.
- Duplicate objects with identical data preserve the existing instance.
- Duplicate objects with different data replace the existing entry; callers
  must resolve conflicts before reuse.

Validation lives in `workspaces/aware_kernel/libs/orm/tests/cache`.
