# Workspace SDK neutral publication source

## Aware architecture setup

Select `aware-workspace-sdk[setup]`. Physical repository preparation remains a
separate operation: the directory below must already exist. This profile creates
authored Aware manifests and registrations, then aligns explicitly selected Repository or registered Workspace UV roots.
It performs no Git initialization, semantic materialization or public release.

```python
from pathlib import Path
from aware_workspace_sdk.architecture_setup import WorkspaceSetupClient

with WorkspaceSetupClient.filesystem(
    repository_root=Path("/absolute/prepared/repository"),
    uv_executable=Path("/absolute/path/to/uv"),
) as client:
    repo = client.create_repository("example", license_expression="MIT")
    repo.create_python_package(
        "base", distribution="example-base", import_root="example_base",
    )
    workspace = repo.create_workspace("application")
    workspace.create_python_package(
        "support", distribution="example-support", import_root="example_support",
        dependencies=("example-base>=0.1,<0.2",),
    )
    module = workspace.create_module("greeting")
    package = module.create_python_package(
        "client", distribution="greeting-client", import_root="greeting_client",
        dependencies=("example-support>=0.1,<0.2",),
    )
    repo.align_package_manager()
    updated = repo.update_locks()
    assert all(result.returncode == 0 for result in updated)
    checked = repo.check_locks()
    assert all(result.returncode == 0 for result in checked)
```

Creation does not implicitly run projection or UV. `client.repository()`,
`repo.workspace(name)` and `workspace.module(name)` select existing registered
entities. Repeated matching setup preserves authored package contents; conflicting
configuration refuses. `preview(ArchitectureSetupRequest(...))` is read-only;
`apply(request, expected_plan_sha256=preview.plan_sha256)` refuses changed plans.

All three owners expose `create_python_package(...)`, with `libs/<name>/python`
as the default owner-relative path. Repository/Workspace register exact manifest
paths in their `codes` lists; Module registers its declared package id and kind.
Support placement cannot overlap registered child ownership. Duplicate normalized
distributions, conflicting existing configuration and unregistered dependencies
at alignment refuse; matching repeats preserve authored source contents.

For low-level previews, `ArchitectureSetupRequest("python_package", owner=...)`
accepts `repository`, `workspace` or `module` (default). Repository selection
requires no Workspace/Module qualifier; Workspace requires only `workspace`;
Module requires both. The standalone `aware-workspace setup python-package`
provides the same selection with `--owner`, and preview/exact-path apply.

Workspace owns placement and registration; Code owns the Python content profile.
A future `.aware` profile must consume the separately accepted Code-Language
semantic contract and original supplier. This candidate provides no semantic
creation command, grammar interpretation or fallback. Distinct semantic package
occurrences and admitted edges must survive that future join.

The initial language profile is authored Python Code. Empty authored v1 Modules
are valid before their first package; this issues no semantic execution grant.
Repository licensing entries are explicit policy bindings: setup does not invent
license text, legal documents or their contents. Author those documents before a
release that requires them.

Alignment uses the original package-manager TOML renderer. Select the Repository
by default, or call `workspace.align_package_manager()`, `workspace.update_locks()`
and `workspace.check_locks()` to establish and use that registered Workspace root.
Align each required context before locking: Workspace alignment changes only its
own root and members; Repository alignment leaves nearer Workspace roots intact.
Members come from exact Aware registrations. Same-context dependencies use
`workspace = true`; cross-context dependencies use relative editable paths.
Existing incompatible sources refuse before writes, including normalized names.
Alignment preserves unrelated sources, requirements and versions.

This bounded profile refuses semantic packages, unregistered/plain intermediate
projects, leaf UV workspaces, custom `uv.toml`, membership globs/exclusions,
conflicting local policies and shadowed leaf locks. Such existing catalogs keep
their separately selected canonical projector. UV 0.11.19 is selected explicitly; lock commands are
offline, never automatically retried and return their actual commands, output
and lock digests for the actual selected root. The CLI selectors are
`setup align --workspace <handle>` and `setup locks update|check --workspace <handle>`;
`--repository-root` always binds the prepared repository. Dependency contexts must
also be aligned. Lock execution rechecks the captured metadata and selected
directory identities before and after the process. Post-effect drift and changed
check bytes preserve an uncertain receipt. Installation is a separate operation.

A lock timeout raises `ArchitectureSetupError` with a `PackageManagerReceipt`
in `receipt`: status `uncertain`, no observed return code, the exact command,
partial output, and before/after lock observations and digests. An unavailable
after-observation is distinct from an absent lock. Timeout output bytes are
decoded reversibly with UTF-8 `surrogateescape`. Inspect this evidence before
another attempt; a timeout does not establish rollback or an unchanged lock.

Effects are local, cooperative descriptor-walk CAS. They do not establish hostile
topology confinement, Service/Object authority or public executable acceptance.
Failure may leave child files or parent directories; inspect the error's receipt
before another attempt. Parent registrations are published after child files.

## Public delta capture source candidate

`aware_workspace_sdk.repository_delta_capture` exposes
`WorkspaceRepositoryDeltaCaptureClient.filesystem(repository_root=...,
cache_root=..., retention=...)`. It witnesses external filesystem effects through
the original Workspace observer and canonical capture coordinator. No Object,
Issue, Meta or Protocol dependency is added. Capture grants no write permission
and does not infer which operation caused an observed change.

Select an original allocated retention client, select capture, then initialize
retention using `capture.repository_binding_ref`. Alternatively, pass an already
active original client for that binding. `prepare_capture(selected_paths=(...))`
obtains its snapshot internally and spends preparation even on refusal.
`observe_capture()` obtains its own exact-path batch and retains original deltas;
it accepts no caller snapshot, batch or provider. `capture_observation()` returns
detached evidence without polling. `release_capture()` closes only that observer,
never the borrowed retention client or domain files.

The actual retained store, observation cache and source root must be physically
separate. Excluded paths are refused, not reported absent. Failures preserve known
deltas and an incomplete ledger; cleanup uncertainty remains unknown and does
not authorize retry. This is cooperative command-local observation, not continuous
confinement, every-write detection or operation recovery.

This source candidate requires successor dependency/profile and installed
qualification. Existing `0.2.2` SDK/runtime and `0.1.2` FS metadata is unchanged;
do not package advancing source as the historical installed candidate. The
selected operational CLI and public protocol profile remain unchanged.

## Repository preparation successor

`aware_workspace_sdk.repository_preparation` owns the authored typed closure
for `repository_sdk.prepare_repository`. Operation identity is preserved; it
is not inferred from the Python namespace. SDK 0.2.1 selects runtime 0.2.1;
the explicit `preparation` extra selects FS adapter 0.1.1. Default SDK imports
do not select a physical provider or import Service/generated capabilities.

`WorkspaceRepositoryPreparationClient.filesystem(repository_root=...,
execution_id=...)` requires an exact canonical absolute root and this harness's
unambiguous execution identity. Preview requires no write admission. Apply
requires an original plan and a fresh single-use admission from that same client.
Closing a plan retires only its own resources. Decoded observations, booleans,
matching digests and copied handles cannot substitute for authority.

Result validation correlates the original request, root, execution and attempt,
validates HEAD/diagnostics and detaches values. Invalid returns retain the
original owner's effects and explicitly unvalidated reports; they grant no retry
permission. This is source qualification, not an installed initializer or a new
environment command selection. Protocol bootstrap and thin `aware init` follow
separately after review.

The neutral `aware_workspace_sdk` source owns publication values, codecs and
genuine owner ports under `repository_publication`. It does not implement Git
IO, parse Issue authority or expose the legacy generated-client/ORM features.
The root intentionally exports no feature APIs and has no Service forwarding shim.

SDK requests and result validation dispatch to Workspace runtime; physical Git
publication remains in the single original Workspace FS writer. Cross-domain
composition stays runtime → supplying SDK. Repository publication is distinct
from semantic WorkspaceRevision commit.

Legacy source callers now import the internal sibling
`aware_workspace_service_sdk_adapter.client` or its explicit feature/state
modules. The relocated bodies retain their original behavior and stable operation
identities; that compatibility sibling is not a newly qualified neutral Service API.

## Qualification boundary

Qualification attaches to an exact source/installed closure, not the package
namespace. The historical split is followed by separately pinned publication
and source-projection successors. The new public capture source above is not
part of those immutable installed candidates; successor metadata, profile,
honest locks and fresh checkout-hidden installation still need qualification
for this addition.

See [source extraction and remaining gates](../../../../../../../../docs/reports/workspace-sdk-service-source-extraction-20261010.md).


### Repository tree projection metadata

`aware_workspace_sdk.repository_tree_projection_values` and
`repository_tree_projection_codec` provide the accepted v1 closed descriptive
values and canonical JSON. The codec checks exact field/types, required nulls,
ordering, modes, complete ancestor declarations, binding commitments and
conjunctive metadata/body limits. Live handles and native body bytes are excluded;
decoding cannot issue a plan, spend an Issue admission or restore an owner.

This source checkpoint supplies the portable contract layer. The original tree
client/runtime, Issue consumption, physical executor and complete-call resource
qualification remain under the separate tree-projection implementation Issues.
No new base dependency, installation or release version is selected here.


`repository_tree_projection` now exposes original native client selection and
closed plan/admission/result types. Its source-first preparation uses the
original workflow source and owned body retention, then refuses while the
original FileSystem preparation/binding join is absent. It currently issues no
positive tree plan or result. Issue enrollment, serialized tree execution and
complete-call qualification remain pending; unavailable entrances do not select
a substitute writer or restore authority from decoded metadata.


## Optional native tree metadata conversion

The existing codec can use a package-local extension for complete descriptive
binding conversion. Public clients, original runtime providers, input validation,
logical quotas and canonical wire bytes retain the same contracts. Both operands
are freshly converted. No operation, source, dependency or publication authority
is supplied by this formatter.

The original generated field converter captures its native function and a sealed
metadata-only context before its code is published. The context is GC-tracked,
contains declarations only, and cannot be constructed through its private type.
Original descriptor, function/default and schema checks surround fresh reads.
The unchanged Python caller performs the root semantic/commitment check.

The existing Hatchling hook compiles on CPython 3.12/Linux with an available
Python-selected compiler. The extension checks its exact compiled CPython patch
and uses a local interpreter/ABI/platform wheel tag. Unsupported or absent native
images use the portable implementation; no compiler runs during SDK import or
ordinary execution. A compilation error on a supported build fails that build.
No dependency, package version, provider selection or store format changes.

For disposable source qualification, invoke the same build function through
`hatch_build.py --output-directory /absolute/existing/disposable/directory`.
Its JSON result records source/compiler/binary hashes and the exact command.
That receipt is build evidence; installed consumer and performance qualification
remain separate.

The same optional internal image also supplies fresh closed-schema receipt-field
conversion to the neutral Workspace runtime through its existing SDK dependency.
Receipt assembly preserves the original lazy hint lookup, schema-change fallback,
field/error order, function metadata and original generic codec. A separate,
once-sealed GC-visible declaration context retains no receipt values. Its native
functions and weak context reference are captured before publishing the encoder
code pin. Every historical receipt is still read and encoded on every durable
publication; index bytes, history and physical publication remain unchanged.
Older supported SDKs, missing helper exports and tree-only native images retain
portable receipt conversion. This private formatter supplies no owner authority.

The optional image also provides a formatting-only memo for the two original
FileSystem receipt indexes. It traverses fresh exact primitive values on every
call and keys cached canonical text by their complete injective representation.
Both stores share one GC-visible context, capped at16MiB and4,096 entries; no
DTO, admission, source verdict, owner handle or prior payload is retained.
Complete receipt conversion, every history record and every original durable
publication remain unchanged. Callee/keyword/stream lookup order, portable
fallback, restart bytes and physical cleanup remain the original contracts.

The canonical source build records a bounded semantic profile of the five
standard JSON functions and their defaults in its disposable compiler input.
An unmatched/custom encoder, missing image/helper or unsupported primitive uses
the original selected serializer. The qualifier does not read source files or
compile at import. Source/build evidence does not establish installed authority
or the complete-call latency gate.

The tree codec's false/false JSON profile shares that same retained cache budget.
It still performs both complete fresh conversions and all semantic, commitment,
logical-reference and byte-limit checks. Fresh primitive keys have a disjoint
profile prefix, so store text cannot substitute for tree text. On a miss, a
bounded native Unicode writer renders the already-captured primitive key without
constructing another payload graph; unsupported shapes use the original selected
serializer. Cache entries remain immutable data and supply no validation verdict.
The original wire function is assembled before its existing native seal; older
images keep the portable wire path. Transient buffers remain subject to the
original complete-call peak-memory gate as well as the retained cache bound.

For disposable attribution only, the canonical builder accepts
`--diagnostic-counters`. This explicitly recorded image times the same six C
entrances internally with bounded numeric-only thread-local state. It preserves
their original method identities and exports diagnostic read/reset calls only
in that build. Default/Hatch images contain no clock instrumentation or those
exports. Diagnostic costs include observer overhead and are never substituted
for the unchanged uninstrumented resource gate.

The optional record-graph capability keeps the original lazy hint invocation and
fresh ordered reads for each nested original record. If schema metadata moves
during hint lookup, the retained original post-hint continuation consumes that
same lookup result. Older images keep the original path. Constant lookup names
use interpreter-owned identifiers only for live Unicode-only dictionaries;
general-key dictionaries retain the original allocation, comparison and error
behavior. Neither refinement caches values or authentication conclusions.
The explicit diagnostic build additionally exposes a literal-lookup parity probe;
that probe is absent from default images and supplies no operational authority.

The optional image also accepts the runtime's finite, detached preparation-copy
specification. It retains class declarations and original function/code pairs,
never input values or owner handles. Each copy reads the original `fields()`
snapshot and every current name/member again, preserves tuples and the existing
atomic-membership schedule, and authenticates fields, fallback and generated
converter dispatch. Unknown leaves retain the original walker/deepcopy route.
The original Python pre/post guards remain; older SDKs/images keep that complete
Python walker. This changes no source, authorization or supplier contract.

An original owner can bind that same false/false canonical-text profile before
its functions are sealed. Exact tuples and lists share stock JSON array text;
the key still traverses every logical occurrence afresh. Unsupported values,
subclasses and cycles retain the selected serializer. The owner's literal
keyword tuple is preserved for fallback dispatch, including ordering. This uses
the existing shared formatting budget and stores neither owner data graphs nor
authorization decisions. Older images keep the original owner function.

Receipt namespaces use freshly compared dictionary-version witnesses for the
bindings already verified at sealing. Function code/defaults remain live checks
on every entrance. Changed namespaces take the original key/binding checks;
sealing repeats its original proof after allocation before publication. This
retains no authorization verdict and does not change operation retirement.


The private preparation copier optionally qualifies the stock `dataclasses.fields`
code through the existing build profile. It rebuilds each current filtered field
snapshot; configuration retains declarations only. Exact own-slot metadata may
use the native snapshot. Changed descriptors, namespaces, arbitrary collections,
tracing or pending/near-threshold GC keep the original function entrance. There
is no GC suppression. Configuration references are owned across allocations and
the original code/export association is rechecked before sealing. Older profiles
keep the original delegate. Supplier and public factory signatures are unchanged.

Receipt recursion also handles exact built-in tuples of retained record types
through the same original context. It reads the current tuple origin/arguments,
keeps ordered iteration and each child's lazy hints, complete metadata checks,
current fields and dispatch authentication. Non-exact collections, unsupported
shapes, callbacks, tracing, monitoring and depth limits retain the original
encoder. This introduces no new callable, context, dependency or value cache.

For an eligible stock ASCII index profile, a formatting miss can render directly
from that invocation's complete fresh primitive key. The same canonical writer
preserves ASCII escapes, surrogate pairs, integer boundaries and sorted field
order. Unknown shapes and other modes retain the original restoration/serializer
path. Original profile checks surround rendering; cache charging, limits, store
bytes and every durable publication remain unchanged.

Receipt conversion derives immutable Field descriptor offsets once within each
original native invocation. Every flag/name still checks the original class
version, current getattribute and bounds and loads the current slot. Changed or
uncertain geometry retains generic attribute dispatch. No field contents or
authority is memoized, and no context or callable interface is added.

The original tree path validator may bind the optional pure ASCII-positive
intrinsic (private ABI 2) into a sealed code constant before declaration capture.
The sealer authenticates its exact original image, function and calling flags.
Every path is still checked freshly. Only exact ASCII text and an exact bounded
integer can take the positive branch; malformed/unsupported values, subclasses,
Unicode and absent older images retain the literal original validator. The
initial `isascii()` dispatch and original refusal order remain unchanged. This
primitive retains no values, hints, owner handles or authorization decisions and
provides no operational authority. Export rebinding cannot replace the retained
pure intrinsic.

The native binding conversion builds a bounded, invocation-local identity index
for its immutable sealed hint declarations. It retains no values, hint results
or authorization decisions and ends with that C invocation. Collisions and
unknown identities preserve the original first-match scan. Every successful
lookup, including an indexed hit, still checks the current original hint-shape
registry entry before using the declaration. Authentication, collection checks,
field reads, validation order and both full operand validations are unchanged.
The public protocol, context object layout and optional native ABI are unchanged.

The private index formatter may capture up to 4,096 primitive record keys
(up to 8 MiB) during the same call's complete eligibility and logical-quota
preflight. Every use checks the original GC collection epochs; any collection
or actual Python serializer callback invalidates the remaining snapshots and
restores the original fresh traversal. Unknown values and integer profiles use
the original preflight. These transient formatting keys do not retain source
objects or authority, change public quotas or survive the invocation.

When the first staged row is missing from the closed private text cache, the
formatter may retain already cached immutable text for later freshly keyed
rows until that invocation finishes. Original per-row cache lookup, counters,
eviction, authentication and logical traversal still run. This only avoids
regenerating callback-free native text evicted by earlier insertions; nested
large-object literal formatting remains active. GC changes and literal
callbacks invalidate the remaining staged keys and text. No input or authority
is retained across calls, and the shared cache budget remains 16MiB.

The optional private `ASCII_PATH_BATCH_ABI=1` returns the last path only after
a fresh exact-ASCII scan of the complete original final path sequence. Raw-object
eligibility precedes mapping or iterator dispatch; every decline keeps the
literal ordered Python loop. The original last-path local remains retained.
Its same-context code-constant binding is authenticated at sealing. It retains
no path or verdict between calls and supplies no source or mutation authority.
## Refusal evidence source successor

The reviewed-workflow source successor distinguishes two known current-input
denials (`review_issue_changed`, `review_authority_sources_changed`) from the
physical attempt to retain them. `SetupReviewError.failure.refusal` holds a
detached `SetupRefusalRecord`; `failure.reads` preserves original private read
returns. The record carries the original review/request/attempt, actual decision
or apply-input reference, owner observations, phase and `product_dispatch="not_invoked"`.
It always has `authorizes_retry=False` and grants no admission.

Only a completed original no-replace write and confirmed sequence cleanup give
the failure a new durable refusal reference. Read its exact bytes through
`read_evidence` and decode `SetupRefusalRecord` with the public owner codec
(`aware.workspace.setup-review.setup-refusal-record.v1`). Earlier v1 wire fields
remain unchanged. Unwritten/lost returns have no invented completed reference;
the primary denial survives and `retention_error` exposes the independent capture
failure. Capture interruptions preserve their original exception and expose
`setup_review_failure` / `setup_review_retention_error` instead. Unknown cleanup
and spent physical sequences remain incomplete; none of this permits retry,
guard refresh or treating the refusal record as an executable review.

This source behavior requires separately qualified successor artifacts. It is
not added to previously frozen wheels or advertised as installed availability.
