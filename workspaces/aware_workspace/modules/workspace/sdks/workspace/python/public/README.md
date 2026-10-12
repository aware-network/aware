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
