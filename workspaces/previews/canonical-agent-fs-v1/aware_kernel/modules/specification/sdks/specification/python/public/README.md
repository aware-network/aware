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

## Authored closure and value encoding — SDK 0.3.2

The genuine `aware/aware.sdk.toml` and its `.aware` value declarations close
the existing `specification_sdk.observe` and `specification_sdk.create_draft`
request, result and error roots. Their provider identities remain
`specification.source.observe` and `specification.draft.create`. Declaration
schema version 1 describes structure, not an installed capability or authority
selection. No generated target is needed for this source contract proof.

`encode_specification_value(value)` and `decode_specification_value(bytes)`
use the explicit `aware.specification.sdk-value.v1` canonical JSON envelope:
`contract`, allowlisted SDK `type_ref`, and `value`. Runtime values retain their
existing Python classes; SDK schema names describe their nested transport view.
The decoder reconstructs existing carriers with their original validators and
checks the complete canonical re-encoding, including derived identities/digests.
Unknown types, extra/missing fields, noncanonical bytes and malformed nested
values return typed `invalid_sdk_wire_value` refusals.

Two positional Python shapes need explicit named records in this encoding:

- Cleanup members: `{relative_path, content: {encoding: "hex", body}}`.
- Filesystem identities: `{device, inode}`, or `null` for absence.

Member bytes are lossless, including empty/non-UTF-8 bytes. Ordered events,
known publication, partial cleanup, missing observations and three-valued
attempt/completeness knowledge are preserved. A decoded snapshot is detached
data: it cannot replace an original reader, Issue admission, custody guard or
provider. Shape validation alone does not verify currentness or authorization.

This is an additive SDK value encoding, **not the existing CLI JSON receipt
format**. CLI arrays, receipt keys and operation behavior remain unchanged;
consumers must explicitly select this envelope before decoding it. Codec refusal
describes a value-conversion failure, not the effect of an earlier writer; retain
the original operation result/error and evidence independently.

The public package still requires only neutral Specification runtime
`>=0.1.0,<0.2.0`. Schema/parser/source-oracle tools are test/build inputs, not
consumer dependencies. Installed composition, canonical consumer projection and
public delivery remain separately qualified.

## Detached cleanup knowledge — SDK 0.2.1

The additive keyword-only `SpecificationOperationError.cleanup_evidence`
carries `SpecificationDraftCleanupEvidence` and its five nested immutable
values. These preserve the original full Issue request, optional execution,
per-holder ownership/attempt/outcome observations, ordered physical effects,
residue, diagnostics, and SPEC's own invocation history. Missing evidence stays
missing; a physical ledger with no completeness field retains `None`.
Protocol-owner attempted/completion knowledge is unobservable at this seam and
must remain `None` / `unknown`, even after a SPEC release invocation returns.

An optional original-context `observe_draft_cleanup()` lookup is used when
reconstructing provider and post-publication result refusals. SDK validation
checks attempt/source correlation and non-regressing history, not supplier
authorization. Malformed/foreign error data cannot replace the original
observer's history. Failed v1 ledger lookup still preserves available cleanup
knowledge on the typed unknown-effect refusal. Known publication is retained
independently of result validation and cleanup uncertainty.

These snapshots are historical data, not instructions to retry cleanup or
restore a retired writer. In particular, an unavailable newer lookup preserves
the last original fields plus explicit unavailable-observation diagnostics;
those old fields do not establish current completion. No supplier imports or
mandatory dependency edges are added to the neutral SDK. Genuine owner
authorization remains in the optional composition, and installed CLI/consumer
cleanup acceptance follows separately.

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
