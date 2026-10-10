# aware-issue-sdk

## Lossless repository consumer binding source checkpoint

Explicitly supply the genuine `IssueRepositoryPublicationClient` as
`IssueSdkOperationClient(..., repository_client=original_client)`. Publication
and closeout then dispatch through Issue runtime into supplying Workspace SDK.
They return `IssueRepositoryOperationResult`, an immutable JSON presentation
of the complete existing owner projections, not an authority handle or a
replacement native publication value. Its `to_wire()` returns detached data.
The `aware.issue.repository-operation.v2` presentation is deliberately not the
ordinary-operation v1 mutation/commit DTO or its generated/native binding.
Do not decode it to recover original admissions or completion authority.

The runtime retains original provider history for the same-lifetime SDK loop.
CLI's explicit `publish-close` projects that loop as two separate effects.
Standalone close from a fresh provider refuses even if the supplied Git commit
is reachable. Receipt presentation is read-only evidence, never a restart rail.

Without the explicit binding, historical provider result validation remains
available for existing transports, but the FS adapter's old publication/close
entrances now refuse without effects. No foreign writer, synthetic lifecycle
metadata or compensating rollback lives in that adapter. The neutral/native
binding, successor metadata and installed profile still require qualification;
the source checkpoint does not update or release the existing package version.

## Compatibility storage-owner migration: 0.10.1

SDK 0.10.1 imports the unchanged JSON storage mechanism directly from
`aware_file_system.local_json_state`. It requires FileSystem
`>=0.3.1,<0.4.0` and the storage-free Issue read Runtime `>=0.3.0,<0.4.0`.
The matching FS adapter 0.9.1 requires these floors and SDK `>=0.10.1,<0.11.0`;
CLI 0.7.1 requires that SDK floor and FS `>=0.9.1,<0.10.0`.
These patch successors preserve canonical requests/results, operation
identities and operational logic. The Runtime's removed old storage import is
a separate breaking 0.3.0 boundary, without a shim.

`local_state.py` remains an explicitly filesystem-backed compatibility cache,
not neutral evaluation or a new authority provider. Its direct FileSystem
dependency honestly represents that retained surface; this is not a claim that
the entire SDK implementation is pure. The existing parser/projection logic
remains in storage-free Runtime. Service backend persistence uses the same
mechanism privately, never transferring authority to a client. Late durability
exceptions can follow an already applied replacement; preserve evidence and
observe before any separately admitted next action, without automatic retry.

This cut supersedes the storage-extraction hold below, but not the separate
SPEC successor qualification, canonical profile/projection or fresh installed
proof. Historical versions and receipts remain historical.

## Breaking Service/view separation: 0.10.0

SDK 0.10.0 removes the Service/view compatibility modules `client`,
`markdown_import` and `view_state_providers`, their thirteen root exports, and
the `service`/`view` extras. They move intact into the sibling internal
`aware-issue-service-sdk-adapter 0.1.0`, using imports from
`aware_issue_service_sdk_adapter` and that package's corresponding extras.
There is no forwarding shim, core-to-adapter dependency or fallback provider.
Python class/import identities change; arbitrary pickle compatibility is not
promised. Historical candidates and receipt pins remain unchanged.

The eleven ordinary operations, seventeen authored roots and failure evidence
keep their existing SDK coordinates and implementation. SDK requires Runtime
`>=0.2.0,<0.3.0`; FS adapter 0.9.0 and CLI 0.7.0 require SDK
`>=0.10.0,<0.11.0`, and CLI requires FS `>=0.9.0,<0.10.0`.
These are source allocations, not a qualified installed composition. SPEC's
governed successor bounds need separate qualification.

This establishes physical Service-source separation, not a package-wide claim
of transport-free implementation. `local_files.py` and `local_state.py` remain
filesystem compatibility surfaces; Runtime's shared JSON storage helper and
both callers require a separate extraction. No copied storage/domain engine,
generated API release or automatic Service-to-FS authority handover is admitted.
Canonical profile extension and fresh installed proof remain pending.

## Result validation and failure evidence

`IssueSdkOperationClient` validates the eleven ordinary Issue request/result
entrances against their existing public Python types. Successful results must
correlate to the invoking operation and Issue; commit results must correlate to
the exact requested paths and preview/apply mode. This is transport-contract
checking, not another lifecycle policy, parser, publication engine or authority
provider. Valid provider results are returned unchanged, with one invocation.

Failures use the authored `.aware` values `IssueReadProjectionResolveError`,
`IssueMutationError` and `IssueCommitWorkspaceError`. They are carried by
`IssueProviderResultError`, which remains an `IssueOperationContractError`
(`ValueError`) for compatibility. Its `failure` is the immutable value; its
`provider_result` retains the original in-process report when available, and
its exception cause preserves the original validation/invocation failure.

Only rejection before provider invocation reports `effect=none`. Invoked
provider or return-validation failures report `effect=unknown`; a reported
commit cannot prove the invoking request succeeded. Neither path retries,
rolls back, reopens work nor restores authority. Check durable records before
any separately admitted next action.

`to_wire()` exports a detached, bounded allowlisted snapshot labeled
`unvalidated_provider_report`. Foreign coordinates remain inside that report,
not the accepted request coordinates. Publication/operator/reference/index
evidence is retained where supplied; arbitrary serialization hooks, raw
Markdown and projection history are not executed/exported. Omitted or
unrepresentable fields have capture diagnostics. Full raw values remain
in-process, so the bounded wire snapshot is not a lossless full serialization.
Both CLI formats preserve this failure value and exit `2` without retry.

The result-boundary checkpoint alone did not complete the authored
request/result roots. The bounded closure below supplies those declarations
for the eleven ordinary operations only. Optional admission operations,
neutral export-profile qualification, successor package versions and installed
readiness remain separate. The existing source-change/draft custody admissions
keep their original owner interfaces.

## Authored ordinary-operation closure

The genuine `.aware` leaf defines the eleven ordinary requests, three shared
results and three error roots, including the owner-produced read projection's
nested wire structure. The existing SDK manifest selects these authored files;
there is no replacement operation catalog or agent-authored selection registry.

The neutral source-contract oracle and public parsed-definition provider agree
for an explicit selection of these eleven operations and seventeen schema
roots. Their `issue_sdk.*` operation identities, `aware_issue_sdk.*` type
namespace, endpoint metadata and local provider bindings are unchanged. This
does not qualify all nineteen entries in the authored SDK inventory: separate
iteration observation and legacy endpoint-only operations remain outside this
bounded proof.

Each ordinary request now exposes `to_wire()` using its existing validated
values. Collection values are detached; result serialization continues to
delegate to the canonical Issue runtime projection. Typed-value parity checks
exercise real requests, provider results, publication refusals, closeout
evidence and nonempty projection payloads against the genuine authored closure.

These declarations specify transport structure, not lifecycle or publication
policy. Defaults are not constants or admission proofs; structural validation
does not prove request/result correlation, digest currentness, ownership, scope,
or authority. The SDK and selected domain provider retain those checks. The
neutral source-contract proof creates no generated files or ontology objects,
does not qualify a renderer or Service/API binding, and is not an installation
receipt. Package metadata and versions are unchanged by this cut.

## Historical compatible source checkpoint: 0.9.1

The earlier bounded source qualification allocated SDK **0.9.1**, FS
adapter **0.8.1**, and CLI **0.6.1**. FS requires SDK `>=0.9.1,<0.10.0`;
CLI requires that SDK range and FS `>=0.8.1,<0.9.0`. This prevents a consumer
requesting the repaired boundary from resolving predecessor implementations.
Existing SPEC governed ranges admit these patch successors without widening.
These are authored package versions, not installed distributions or public
releases. Historical source/wheel pins and accepted candidates stay unchanged.

All seventeen ordinary request/result/error roots resolve from the lazy public
SDK facade in a fresh source process with Service/generated and lower-owner
imports blocked. The eight already mapped source-change names are now also
advertised by `__all__`; their interfaces and authority are unchanged.

At that checkpoint, Runtime's mandatory Service edge and SDK's mixed physical
sources blocked neutral installation. The 0.2.0 Runtime and 0.10.0 SDK source
moves above supersede those two findings; they do not retroactively change the
historical receipt. Compatibility storage extraction, SPEC successor
qualification and canonical profile extension remain pending before a fresh
installed-neutral claim. Historical export-pruning recipes cannot silently
become canonical selection.

## Single-use source-change supplier contract

`aware_issue_sdk.source_change` declares `IssueSourceChangeRequest`, the
optional `IssueSourceChangeProvider`/client and opaque admission port.
Requests bind an exact Issue digest, manifest locator/preimage, candidate bytes,
ordered directories and setup intent; they are never permits. There is no
actor-string or callback-guard request. The original provider exposes
`validate_source_change` for genuine issuer-bound validation, so compositions
need not import private Issue implementation checks.

Consumption permits only bound physical preparation/replacement/finish.
Receipts/effects are structural evidence, not transferable grants. Filesystem
implementations disclose their actual identity/confinement grade. Protocol
owns candidate semantics and eventual concrete writer integration; this
supplier contract does not qualify setup or a fresh SPEC reader. Publication
and installed qualification remain separate effects.

Canonical provider-neutral Issue operations; internal Service/view compatibility
facades now live in their separate adapter. Filesystem and future Service/API
bindings share SDK operation identities;
the interface does not select authority.

Issue domain owners retain lifecycle and publication semantics. An explicitly
selected filesystem provider owns FS-mode records; a separately admitted
Service/API provider owns service-mode records. The SDK is the public client
boundary, not an authority selector or a service-unavailability fallback. It
must not import Issue service internals or Workflow runtime internals.

`aware_issue_runtime` owns canonical Issue Markdown parsing, domain identity,
structured content/activity order, absolute time authority, and exact source.
`IssueDevelopmentReadProjectionV2` is a pure SDK adapter over that domain
projection. It adds Development closed vocabularies with raw/provenance
preservation, deterministic reading/reference facets, and occurrence-keyed
attention candidates without filesystem or provider I/O. Versioned immutable
fixtures live under `contracts/development_read_projection/v2/`; Dart and later
service adapters must consume or pass those fixtures without implementing
another parser.

The base distribution contains provider-neutral operation contracts, Issue
read semantics, and compatibility filesystem helpers. Generated service DTO/API
and view dependencies belong to the separate internal adapter's `service` and
`view` extras, not this distribution. Physical source separation is not proof
of an installed consumer closure or supported Service/API authority.

Provider-neutral lifecycle contracts expose ensure, start, resume, scope,
update, evidence, block, owner transfer, and close under the existing
`issue_sdk.*` operation identities. Mutating requests carry explicit actor
evidence and filesystem source CAS; the selected provider remains responsible
for authority-specific admission and receipts.

Filesystem handoff composes existing operations: the current owner blocks the
Issue, `issue_sdk.set_issue_owner` records the replacement, and the replacement
rereads and invokes `issue_sdk.resume_issue`. There is no second handoff
operation or process-local ownership pointer.

`issue_sdk.commit_workspace` exposes checked exact-path repository publication
without importing Workspace implementation types into the public SDK contract.
An applied `close_issue` result may additionally carry the authority-produced
`closeout_publication_receipt_ref`; declarations and caller-supplied evidence
do not manufacture that receipt.
