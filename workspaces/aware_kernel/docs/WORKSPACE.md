# Aware Kernel Workspace

`workspaces/aware_kernel` is the public kernel workspace selected from a
WorkspaceRevision.

The workspace descriptor is `aware.workspace.toml`. It declares the public
kernel package boundary.

The first public target is intentionally small:

- Workspace-local modules selected through `[[workspace.modules]]`.
- Core ontology substrate: Storage, Content, Code, History, Meta, and Ontology.

Environment, Identity, Attention, API contracts, SDK contracts, service
implementations, node descriptors, network topology, and product/operator
experience contracts are above the minimal kernel unless a concrete kernel
proof requires them.

The ontology migration matrix is
`workspaces/aware_kernel/docs/ONTOLOGY_MIGRATION_MATRIX.md`. It tracks the
module-by-module move from root `modules/*` packages into the selected
workspace-local `modules/*` layout, where each module owns semantic package
leaves such as `ontology`, `apis`, `services`, and `sdks`.

## Public Checkout Rules

- Package roots stay under `workspaces/aware_kernel`.
- Module roots stay under `workspaces/aware_kernel/modules/<module>`.
- `.aware/workspace/*` manifests are receipts for the checkout.
- Migrated kernel ontology functions are native `.aware` FunctionImpl
  authority.
- Hand-authored Python handlers are not authority for migrated kernel
  ontologies.
- Private product workspaces are not part of this selected workspace.
- Agent and Workspace implementation packages are not part of this selected
  kernel checkout.

## Readiness Checks

A ready public checkout has:

- `README.md` at repository root.
- `workspaces/aware_kernel/README.md`.
- `workspaces/aware_kernel/aware.workspace.toml`.
- No local absolute paths in public JSON manifests.
- No private product or agent/workspace package roots.
