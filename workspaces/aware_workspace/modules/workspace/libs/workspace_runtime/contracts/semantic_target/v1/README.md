# Workspace semantic target binding v1

This contract is the operational boundary between admitted source evidence and
semantic meaning resolution. Workspace owns the binding because it owns the
destination repository/package coordinates. It does not resolve source-domain
meaning.

## Flow

```text
generic admitted source authority
  + exact workspace.repository snapshot
  + Workspace-owned authored/revision-resolved package catalog
  + semantic-provider compatibility advertisement
  + Human/Agent selection provenance
  -> aware.workspace.semantic-target-binding.v1
  -> selected semantic provider (later)
```

The `workspace.semantic_target` participant declares only
`workspace.repository` as a Local Service dependency. At startup it reads each
catalog manifest through the snapshot-confined Workspace source-read operation
and rejects absent, moved, or digest-mismatched evidence.

`catalog_targets` accepts the generic source capability, contract version, and
authority fingerprint. It returns only explicitly compatible target/provider
pairs and fingerprints the complete source, repository, composition, and
candidate set. No compatibility is inferred from a package name.

`bind_target` requires that fingerprint plus one exact package/provider pair,
an expected operational-state revision, and selection provenance. `selected_by`
is an opaque actor reference; `selector_mode` is `human` or `assistant`.
Persistence is capability-scoped, compare-and-set local operational state.

`read_binding` requires the same exact source coordinate. Any repository epoch,
cursor, or snapshot movement invalidates the binding until Workspace composition
is refreshed and the participant restarts.

## Authority and non-claims

- Authority remains `local_uncommitted`.
- `authored_declaration` catalogs have no `authority_ref`.
- `revision_resolved` catalogs require an exact `authority_ref`.
- The source contract is generic. Workspace does not import Code or understand
  SQL, Django, Python, Rust, JavaScript, or another source family.
- The provider advertisement is compatibility evidence, not provider
  execution. Workspace does not import or invoke Ontology or Meta.
- The binding is not resolved meaning, an `.aware` source edit, a
  `WorkspaceRevision`, a materialization plan, a graph commit, or an OIG fact.

The representative fixture joins the E1 Existing-System source authority to an
Ontology package and the future `ontology.semantic_resolution` capability. It
freezes the boundary only; the provider capability is implemented separately.

