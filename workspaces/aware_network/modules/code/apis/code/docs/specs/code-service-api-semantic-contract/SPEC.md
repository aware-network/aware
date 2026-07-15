# Code Service API Semantic Contract - SPEC

Status: in progress
Owner: `codex-019e2fb7-f5a9-7a21-b305-a26cec2a226b`

This file is the spec-package entrypoint. Do not add a parallel root
`README.md`.

## Goal

Make `apis/code` the canonical API-Service owner for Code semantic contract
DTOs so local and remote consumers can share one schema boundary.

The end state is:

```text
Code API
  -> owns SemanticContract DTOs and CodePackageDelta DTOs

FileSystem SDK
  -> consumes Code DTOs to classify local code layout and build FS deltas

Workspace SDK / Workspace Service
  -> aggregate Code + FileSystem into status, materialize, apply, commit,
     revision, and publication workflows
```

This is the lock: Code leads with the semantic contract; FileSystem resolves
local filesystem semantics from that contract; Workspace aggregates product and
revision workflows above both.

## Canonical Direction

- `apis/code` owns generated DTOs, generated API client, and generated service
  protocol for Code semantic contracts.
- `services/code` owns the local protocol adapter over `aware_code` runtime.
- `modules/code/runtime/aware_code` remains the implementation engine for
  parsing, language plugins, runtime registries, and adapter functions.
- `sdks/filesystem` owns local semantic filesystem helpers over generated
  FileSystem API DTOs and Code semantic contract DTOs.
- `workspaces/aware_workspace` owns WorkspaceRevision, materialization,
  commit, status, and publication orchestration.
- `aware-dev status` is the first product consumer of the combined local truth:
  filesystem state plus Code semantic contract DTO index plus Workspace
  revision/materialization authority.

The target dependency direction is:

```text
aware-dev
  -> aware-workspace-sdk
  -> aware-file-system-sdk
  -> aware_file_system_service_api
  -> aware_code_service_api DTOs

workspace-service/runtime
  -> aware-file-system-sdk
  -> aware_file_system_service_api
  -> aware_code_service_api DTOs
```

The invalid dependency direction is:

```text
workspace-sdk -> workspace runtime/service internals
workspace service/runtime -> workspace-sdk
filesystem service -> workspace adapter
filesystem service -> code runtime registry
workspace -> provider semantic implementation internals
```

## Current Truth

- The retired module-owned Code API package at `modules/code/structure/api`
  has been removed. Code API DTO ownership now lives under `apis/code`.
- `modules/code/runtime/aware_code/module_semantic_contract.py` currently owns
  the Python dataclasses for `ModuleSemanticContract` and descriptor families.
- `modules/code/runtime/aware_code/semantic_contract.py` is Code's own provider
  contract, not the public schema authority for every semantic provider.
- `modules/code/docs/specs/semantic-capability-contract/SPEC.md` already locks
  the runtime capability rail around `CodePackageDelta -> semantic provider
  capability -> semantic evidence -> Workspace lifecycle`.
- `apis/filesystem` and `services/filesystem` already prove the generated
  API-Service pattern: generated DTO/API/protocol under `apis/*`, local
  service adapter under `services/*`, and transport-free in-process protocol
  dispatch.
- `docs/conversations/2026-05-19-CODE-SEMANTIC-CONTRACT-LOCK.md` locks the
  product direction: Code API owns semantic contract DTOs; FileSystem SDK
  consumes those DTOs; Workspace SDK/Service consume FileSystem SDK.
- `apis/code/aware.api.toml` now declares `code-service-dto` as an `api_dto`
  semantic export, and Code API compile materializes
  `apis/code/python/aware_code_service_dto` as the generated Python DTO package.
- `apis/code/dto/aware/code/features/section_delta.aware` now owns the
  provider-neutral section-delta DTO rail, including `CodeSectionDeltaSet`.
- `apis/code/dto/aware/code/features/source_projection.aware` now owns the
  Code API source-projection envelope above `CodeSectionDeltaSet`.
- `apis/code/bindings/code.apis.aware` now exposes `code.section_delta`
  protocol endpoints, including `resolve_package_delta`.
- `apis/code/bindings/code.apis.aware` now exposes
  `code.source_projection.validate`, `normalize`, `fingerprint`, and
  `resolve_package_delta`.
- `services/code/aware_code_service/api_service_protocol.py` now implements the
  local resolver from `CodeSectionDeltaSet` to `CodePackageDelta`.
- `services/code/aware_code_service/api_service_protocol.py` now implements
  local validation, normalization, and fingerprinting for source-projection
  request/result envelopes, plus package-delta resolution for provider result
  evidence. It does not execute semantic providers.
- `modules/code/docs/specs/semantic-source-projection-contract/SPEC.md` now
  owns the higher-level semantic source-projection contract above the landed
  delta rail.

## Scope

In scope:

- Future `apis/code` API-Service contract for semantic contract DTOs.
- DTO families needed to represent the current `ModuleSemanticContract` shape.
- DTO families needed to represent `CodePackageDelta` and package layout/path
  role contracts.
- Service protocol proof direction for `services/code`.
- FileSystem SDK consumer boundary for local layout classification and
  `CodePackageDelta -> FileSystemDeltaSet -> filesystem.delta.apply`.
- Workspace aggregation boundary for status, materialization, apply, commit,
  revisions, and publication.

Out of scope for this lock:

- Implementing `apis/code` files.
- Reintroducing `modules/code/structure/api`.
- Migrating all existing runtime imports away from `aware_code` classes.
- Implementing `sdks/filesystem`.
- Changing Workspace SDK or Workspace Service consumers.
- Making FileSystem Service semantic-aware; semantic FS helpers belong in
  FileSystem SDK, not the service backend.

## Semantic Contract DTO Surface

`apis/code` must expose DTOs for the full shared semantic contract, not only a
small service status shape.

Initial DTO families:

- `CodeSemanticContract`
  - provider key
  - semantic scope keys
  - capability participation
  - capability execution policy
  - capability profiles
  - capability bundles
  - syntax lanes
  - package roles
  - artifact leaf ownership
  - materialization inputs
  - materialization artifact outputs
  - materialization package outputs
  - materialization runtime declarations
  - materialization runtime context declarations
  - materialization execution context declarations
- `CodePackageDelta`
  - package identity
  - root/package/source refs
  - changed file entries
  - before/after digests
  - semantic contract provider refs
  - optional provider payloads
- `CodeSectionDeltaSet`
  - package identity and baseline fingerprint evidence
  - section refs by path, section type, qualname, id, identity hash, and semantic key
  - segment refs by segment name, expected hash, and optional byte-range evidence
  - section-delta entries for segment replacement, full-section replacement,
    section insertion, and section deletion
  - resolver request/response DTOs for `CodeSectionDeltaSet -> CodePackageDelta`
- `CodeSourceProjection`
  - capability DTO family owned by Code API
  - request context for semantic events, source-projection action bindings,
    package/source context, provider key, semantic owner, and product intent
  - result evidence carrying produced `CodeSectionDeltaSet`, diagnostics,
    skipped-event evidence, and provider receipt refs
  - must not duplicate `CodeSectionDeltaSet` or `CodePackageDelta` schema
- `CodePackageLayoutContract`
  - package root
  - sources root
  - generated roots
  - manifest refs
  - path role patterns
  - semantic owner hints
- `CodeSemanticProviderBinding`
  - provider key
  - provider role/name/module refs
  - package FQN
  - manifest kind/path
  - semantic package metadata

The DTOs should mirror the existing runtime contract shape first, then runtime
adapters can convert between `aware_code` classes and generated Code API DTOs.

## API Capability Direction

The first `apis/code` contract should be DTO-first and capability-light.

Candidate capability groups:

- `semantic_contract`
  - describe provider/package semantic contract
  - validate serialized semantic contract DTOs
  - normalize runtime-adapted semantic contract DTOs
- `package_delta`
  - validate/normalize `CodePackageDelta`
  - summarize delta fingerprints and changed paths
- `section_delta`
  - validate/normalize `CodeSectionDeltaSet`
  - fingerprint semantic event to section-delta intent
  - expose a generated resolver protocol for `CodeSectionDeltaSet -> CodePackageDelta`
- `source_projection`
  - normalize/validate source-projection requests over semantic events and
    action policy
  - fingerprint request/result envelopes for preview and receipt correlation
  - carry provider output as `CodeSectionDeltaSet` evidence
  - leave `CodeSectionDeltaSet -> CodePackageDelta` to `section_delta`
    resolver endpoints
- `package_layout`
  - describe package layout/path role contract
  - validate path role contract DTOs

The first proof does not need hosted service intelligence. It needs generated
DTOs and generated service protocol proving the contract can be transported,
validated, and consumed without importing `aware_code` runtime classes.

`code.section_delta.resolve_package_delta` is a Code API protocol contract.
Resolver behavior belongs in a later `services/code` issue; the API-first
contract does not import FileSystem SDK and does not apply filesystem changes.

## FileSystem SDK Contract

`sdks/filesystem` is the reusable semantic-aware local filesystem layer.

It may consume Code DTOs directly:

```text
CodeSemanticContract DTO
CodePackageDelta DTO
CodePackageLayoutContract DTO
```

It owns:

- `CodePackageDelta -> FileSystemDeltaSet`
- local layout and path-role classification from Code semantic contract DTOs
- root/digest/status helpers over generated FileSystem API DTOs
- `filesystem.delta.apply` ergonomic wrapper

It must not own:

- WorkspaceRevision truth
- provider semantic meaning
- Code runtime registries
- FileSystem Service backend implementation

The core SDK must accept DTO objects directly. Optional client/fetch hooks may
later call Code API, but local status must not require a remote Code service.

## Workspace Contract

Workspace aggregates. It does not own Code or FileSystem local semantics.

Workspace SDK and Workspace Service consume the same FileSystem SDK helpers:

```text
Workspace SDK -> FileSystem SDK -> FS API DTOs + Code API DTOs
Workspace Service -> FileSystem SDK -> FS API DTOs + Code API DTOs
```

Workspace owns:

- WorkspaceRevision composition and receipts
- materialization request/receipt orchestration
- semantic changelog aggregation
- commit/readiness/status product flows
- remote authority and publication workflows through Hub/Workspace services

Workspace must not become:

- the shared FileSystem adapter layer
- the public Code semantic contract schema owner
- a direct importer of provider compiler internals for local status truth

## Product Contract

The first operator product target remains:

```text
aware-dev status
```

Local truth:

```text
filesystem state
-> FileSystem SDK status/delta helpers
-> Code API semantic contract DTO index
-> semantic dirty report
```

Remote truth:

```text
Workspace Service materialization
-> WorkspaceRevision receipts
-> Hub authority/publication refs
```

The status rail must support:

- local-first status without Git as truth
- semantic dirty grouping by provider/package
- unmapped path reporting
- materialization readiness/staleness
- next actions for materialize, apply, verify, and publish

## Data / Identity / Mutation Rules

Fail-closed rules:

1. Public Code semantic contract DTOs live under `apis/code`, not under module
   runtime imports.
2. `services/code` may adapt from runtime classes, but it does not make runtime
   classes the public DTO boundary.
3. FileSystem Service remains generic filesystem operation fulfillment.
4. FileSystem SDK may be Code-contract-aware; FileSystem Service should not be.
5. Workspace SDK must not import Workspace runtime or Workspace service
   internals.
6. Workspace Service must not import Workspace SDK as an implementation
   shortcut.
7. Workspace dependency imports remain provider-key to concrete CodePackage FQN
   grants.
8. Local status must be explainable from filesystem receipts plus Code semantic
   contract DTOs, even when remote materialization is unavailable.

## Evidence And Testing Contract

Required proofs for future implementation iterations:

- `apis/code` compile/generation proof for generated Python API and service
  protocol packages.
- DTO adapter tests:
  - runtime `ModuleSemanticContract` -> generated `CodeSemanticContract`
  - generated `CodeSemanticContract` -> runtime-compatible adapter input
  - `CodePackageDelta` validation and fingerprint stability
- Service protocol tests:
  - generated Code service protocol dispatches in-process without network
  - `services/code` local protocol handler adapts over `aware_code`
- FileSystem SDK tests:
  - Code DTOs classify local path/layout ownership
  - `CodePackageDelta` maps to `FileSystemDeltaSet`
  - local apply uses generated FileSystem API client/facade
- Workspace consumer tests:
  - Workspace SDK consumes FileSystem SDK without runtime/service imports
  - Workspace Service consumes FileSystem SDK without importing Workspace SDK
- Import-boundary scans:
  - SDKs must not import Workspace service/runtime internals
  - FileSystem Service must not import Workspace adapters
  - Code API DTO tests must not require provider runtime implementation imports

## Work Governance

- Invariant index: `invariants/README.md`
- Invariant units:
  - `invariants/00-code-api-owns-semantic-contract-dtos/README.md`
  - `invariants/01-filesystem-sdk-resolves-code-semantic-contract/README.md`
  - `invariants/02-workspace-aggregates-revision-workflows/README.md`
- Phases ledger: `PHASES.md`
- Shared iteration contract: `docs/specs/TEMPLATE_ITERATIONS_PROTOCOL.md`
- Phase directories: `phases/<phase_order>-<phase_slug>/README.md`
- Active iteration artifacts:
  `phases/<phase_order>-<phase_slug>/iterations/<iter_order>-<YYYY-MM-DD>-<iter_slug>/README.md`
