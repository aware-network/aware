# Workspace SDK neutral publication source

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

This is a source split, not an available installed successor. Historical
`0.1.0` metadata still declares the old generated/ORM closure and cannot be used
to package advancing split bytes as an unchanged public release. Successor
package metadata, canonical registrations/profile, honest locks and fresh
checkout-hidden installation follow separate qualification.

See [source extraction and remaining gates](../../../../../../../../docs/reports/workspace-sdk-service-source-extraction-20261010.md).
