# Invariant 02 - Workspace Aggregates Revision Workflows

## Contract

Workspace composes Code API and FileSystem SDK into product workflows. It does
not own the public Code semantic DTO schema and it does not become the shared
FileSystem helper layer.

## Must Hold

- Workspace SDK consumes FileSystem SDK for local filesystem/code delta helpers.
- Workspace Service consumes FileSystem SDK for service-side filesystem/code
  delta helpers.
- Workspace owns WorkspaceRevision, materialization, readiness, commit,
  changelog, and publication receipts.
- `aware-dev status` can combine local FileSystem SDK truth, Code semantic
  contract DTOs, and remote Workspace materialization authority.

## Must Not Happen

- Workspace SDK must not import Workspace runtime or Workspace service
  internals.
- Workspace Service must not import Workspace SDK as an implementation shortcut.
- Workspace must not duplicate FileSystem SDK mapping logic as a shared layer.
- Workspace must not call provider compiler internals to classify local status.

## Proof Direction

- Workspace SDK consumer tests prove it uses FileSystem SDK, not runtime
  internals.
- Workspace Service consumer tests prove it uses FileSystem SDK, not Workspace
  SDK.
- Status tests prove local semantic dirty reports can be built from filesystem
  state plus Code semantic contract DTOs.
- Revision/materialization tests prove Workspace remains the aggregation and
  receipt authority.
