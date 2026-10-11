# Workspace SDK neutral publication source

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
