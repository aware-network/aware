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

## Saved draft receipt SDK 0.3.4

`SpecificationSavedReceiptClient(provider).present_draft_receipt(request)` is a
separate read-only port for an **existing full CLI043 draft capture**. It never
calls a draft writer, reobserves the original repository or restores authority.
The physical provider and customer registrar are separate implementation cuts;
this package supplies their neutral values, validation and presentation.

`SpecificationSavedReceiptRequest` requires an explicit normalized absolute
`base_ref`, a canonical relative `source_ref` and the exact saved-file byte
guard `expected_source_sha256`. That guard is not an Issue, Protocol manifest,
SPEC closure or omission digest. `input_profile` is fixed to
`specification.cli043-draft-transport.v1`; no producer-format guessing occurs.
Views are `summary` and `full`.

Every successful SDK result retains the full original bytes as bounded
canonical `full_body_hex`, including summary results. The complete captured
packet is validated through original SPEC values and snapshot codecs before
omission. Only the ten enumerated collection pointers can be replaced;
descriptors bind their exact encoding, counts and guarded source access. Effect
collections retain none/applied/unknown and confirmed/unconfirmed-durability
counts. All scalar failures, cleanup responsibilities, uncertainty and residue
remain visible. Full view keeps original whitespace and returns no summary.

Legacy FileSystem fallback cleanup is mapped only for validation: unreported
`ledger_complete` and `before_identity` stay absent in the capture and summary.
Top-level Issue custody has its own exact transport mapping: its reported
`ledger_complete` is preserved, while its unreported `before_identity` remains
absent. Neither mapping changes the captured bytes or guesses a producer.
Present attempt/client/execution/context coordinates are joined across evidence,
cleanup, Issue disposition and custody before omission. Unknown coordinates
remain unknown; the original exact comparison between the two custody carriers
also remains in force. No completeness or preimage identity is invented.
A malformed omitted member
refuses the whole presentation. Presentation success describes capture review,
not the captured operation's success, currentness, approval or retry permission.

The six new authored values use
`aware.specification.saved-receipt-value.v1` through dedicated codecs;
`encode_specification_value`/`decode_specification_value` route these same
values without changing the existing envelope for historical carriers.
Source JSON is limited to 16 MiB, depth 32, 262,144 nodes, 1 MiB individual
strings and signed 64-bit integers. Duplicate keys, invalid UTF-8, nonfinite
numbers and unexpected fields refuse. Requests have a 64 KiB wire limit;
results/errors have a 192 MiB ceiling, including the retained raw hex.

Local request/copy failures report no provider invocation or acquisition.
Correlated provider refusals preserve original evidence. Invalid returns carry
explicitly unvalidated reports with unknown effects/cleanup, never success or
automatic retry; untransportable reports retain their type and an explicit
unavailability diagnostic. These values are detached data, not admissions or
permanent retention. The default dependency remains neutral Specification
runtime only. Live mutation JSON, filesystem implementation, selected command
and installed consumer closure are unchanged by this source cut.

## Read-only draft input observation SDK 0.3.3

`SpecificationInputObservationClient(provider).observe_draft_input(request)`
uses an explicitly selected read-only input provider, separate from retained
SPEC document and draft-write authority. `SpecificationInputObservationRequest`
contains explicit `source_ref` and `base_ref`. The result retains their exact
correlation, resolved source coordinate, provider identity, byte count, exact
`source_sha256` and immutable `body` bytes through bounded canonical `body_hex`.
The fixed input limit is 2 MiB. Successful results require confirmed descriptor
closure and describe observed state—not every-write detection or later currentness.

`SpecificationInputObservationError` retains original request, invocation,
cleanup and bounded observed-byte evidence. Malformed provider reports remain
explicitly unvalidated with unknown cleanup/effects; they cannot supply a guard.
No admission, descriptor or provider can be decoded from these values.
`encode_specification_input_value` / `decode_specification_input_value` use the
existing strict SDK envelope, with a 4 MiB plus 64 KiB wire bound before input
decoding. Original value encodings and operation identities remain unchanged.

The authored operation is `specification_sdk.observe_draft_input`, backed by
`specification.input.observe`. Pure snapshot decoding/rendering and governed
`create_draft` remain separate; apply still consumes explicitly reviewed guards.

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
