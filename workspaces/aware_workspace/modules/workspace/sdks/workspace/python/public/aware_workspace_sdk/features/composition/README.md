# Workspace composition provider v1

`aware.workspace.composition.v1` is the provider-neutral read projection for
repository → Workspace → module → semantic-package composition.

The current `local_checkout_manifest` provider observes canonical authored
manifests under an explicitly granted root. Its snapshots always report:

- `resolution_state = authored_declaration`
- an observation digest over the manifests it consumed
- `authority_ref = null`
- no inferred semantic provider key, OIG coordinate, WorkspaceRevision, or
  materialization receipt

Repository membership and Workspace identity are intentionally separate. For
example, repository membership `aware_home` resolves to the canonical Workspace
handle `home_story_workspace`; consumers must not require equality.

The future Workspace Service provider will map the Workspace API and
`workspace.semantic_provider.catalog` into the same DTO. Its resolved results
will report `resolution_state = revision_resolved`, an authenticated authority
reference, provider keys, and advertised capabilities. Replacing the provider
must not change Aware Development navigation or rendering contracts.

`package_kind`, `provider_key`, and `capabilities` are open strings. The DTO can
therefore describe additional semantic package families without adding UI-side
enums.

The local provider is read-only. It performs confined manifest reads with fixed
budgets and stable typed failures; it does not write sources or create service
authority.
