# Specification SDK

Explicitly selected provider operations over neutral Specification values.
No Service/API, generated DTO, ontology runtime, filesystem implementation or
authority fallback is imported here. Portable observation/identity values are
content evidence, not capabilities, approval or Issue admission.

`create_draft` establishes explicit contract meaning at an absent target.
This first writer refuses definitions containing iterations: no trusted
maintainer-approval writer is supplied. Existing iteration plans remain
observable. Workflow owns their work association independently.

This is a source implementation, not a customer distribution or release.

## Draft evidence — SDK 0.2.0

`SpecificationDraftEvidence` and its immutable member/effect values carry ordered
attempt history. Seven distinct physical kinds, absent fields, repeated paths,
cleanup diagnostics, residue and both durability flags are preserved. Package
outcome is independent of SDK validation: an `effect="unknown"` error may retain
known `package_outcome="published"`. Neither is Phase acceptance or permission.

An explicitly supplied `draft_evidence_reader` provides the fixed original
attempt snapshot. The SDK reads it before returned result/error fields and
verifies stable attempt/candidate correlation, an unchanged ordered prefix of
previously observed effects, and no regression from known publication. Residual
scratch paths may shrink during cleanup. Inconsistent history or reader failure
retains the last valid history as incomplete, unverified and unknown (preserving known publication),
or explicitly returns no evidence when none was available. Reobserve; do not
blindly retry an uncertain writer. Returned evidence cannot replace that reader.

The ordinary constructor and result's first three fields remain compatible;
omitted evidence is legacy compatibility, not governed acceptance. SDK 0.2.0
explicitly changes result/error carriage and bounds its only dependency to neutral
runtime `>=0.1.0,<0.2.0`. Existing consumer wheels stay pinned until separately
qualified; no CLI, FS adapter or aggregate lock is upgraded by this source cut.

Typed readers prove value/error behavior only. The later governed factory must
verify original Issue, Protocol and FileSystem ports. Snapshots can survive
release without retaining live postimage authority or authorizing another write.
