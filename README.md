# Aware Kernel

Aware Kernel is a WorkspaceRevision-backed public kernel checkout.

This Git repository is a filesystem surface materialized from Aware workspace
truth. `workspaces/aware_kernel` is the selected kernel workspace: the smallest
graph operating substrate that can describe code packages, hold revision truth,
materialize runtime state, and publish receipt-backed outputs.

## Meta Is The Kernel Control Package

Meta is the package that lets Aware describe and safely change itself.

It turns `.aware` source into ObjectConfigGraph package truth, projection and
runtime graph views, FunctionCall execution contracts, ObjectInstanceGraph
commits, generated artifacts, and receipts. Generated files are therefore
materialized outputs, not source authority.

For public kernel OSS, this makes Meta the change-control layer: package
semantics, graph identity, runtime execution, materialization, and receipts all
have to pass through Meta-owned contracts before kernel changes can be treated
as stable.

## What Is Here

- `workspaces/aware_kernel/aware.workspace.toml`: selected workspace descriptor.
- `workspaces/aware_kernel/aware.environment.toml`: selected environment
  descriptor for kernel materialization.
- `workspaces/aware_kernel/docs/WORKSPACE.md`: public checkout rules and current
  package boundary.
- `workspaces/aware_kernel/docs/ONTOLOGY_MIGRATION_MATRIX.md`: module-by-module
  migration from root packages into workspace-local kernel packages.
- `workspaces/aware_kernel/modules/storage`: first workspace-local migrated
  kernel module seed.

## WorkspaceRevision Truth

Aware development is driven by WorkspaceRevision truth. Git is the public
developer surface for inspection, review, and contribution; the canonical
release path materializes selected workspaces from committed revision state.

The public mirror is intentionally selected. It does not include private product
workspaces or agent/workspace runtime packages.

## Stability Direction

Stable kernel publication follows this order:

1. Meta correctness: source semantics, graph identity, FunctionCall execution,
   OIG commits, materialized outputs, and receipts stay green as one system.
2. Coverage: key package dynamics are proven through focused Meta tests and
   WorkspaceRevision materialization receipts.
3. Performance: provider-delta and runtime-context paths stay incremental, so
   kernel changes do not require broad rematerialization when scoped deltas are
   enough.

## Current Boundary

This seed publishes the public kernel workspace first. Product workspaces can be
added later as separate selected workspaces once their public boundaries are
ready.

Start with:

```bash
ls workspaces/aware_kernel
cat workspaces/aware_kernel/docs/WORKSPACE.md
```
