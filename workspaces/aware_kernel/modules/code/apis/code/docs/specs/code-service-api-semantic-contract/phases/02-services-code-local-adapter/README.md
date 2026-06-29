# Phase 02 - services/code Local Adapter

Status: complete
Owner: `codex-019e2fb7-f5a9-7a21-b305-a26cec2a226b`

## Goal

Create `services/code` as the canonical local service implementation package
for the generated Code Service API semantic contract protocol.

## Acceptance

- `services/code/aware.service.toml` exists and declares the
  `aware-code-service` implementation package.
- The service depends on `code-service-api` as an `api_service_protocol`
  dependency with a concrete expected hash.
- `aware_code_service` exports service bindings and an in-process generated API
  client.
- Generated endpoint refs dispatch locally:
  - `code.semantic_contract.describe`
  - `code.semantic_contract.validate`
  - `code.semantic_contract.normalize`
  - `code.package_delta.normalize`
  - `code.package_delta.fingerprint`
  - `code.package_layout.describe`
  - `code.package_layout.validate`
  - `code.section_delta.validate`
  - `code.section_delta.normalize`
  - `code.section_delta.fingerprint`
  - `code.section_delta.resolve_package_delta`
- Runtime semantic contract truth is adapted to API-owned DTOs without moving
  the runtime contract classes in this phase.
- Runtime/API semantic contract conversion is isolated in the Code Service
  adapter layer and proves both `ModuleSemanticContract -> CodeSemanticContract`
  and API DTO -> runtime-compatible contract shape.
- `aware-code-service` resolves through root workspace metadata; service tests
  and local consumers do not need ad hoc `sys.path` injection.
- Section-delta resolver behavior starts with `replace_segment` and returns
  API-owned `CodePackageDelta` DTOs without applying filesystem changes.

## Iterations

- `iterations/00-2026-05-19-code-service-local-adapter/README.md`
- `iterations/01-2026-05-19-code-service-layout-contract-stability/README.md`
- `iterations/02-2026-05-19-code-section-delta-runtime-resolver/README.md`
- `iterations/03-2026-05-19-code-semantic-contract-runtime-api-adapter/README.md`

## Exit Check

Phase 02 exited with implementation commit
`0f94a279b57defa6df28a5bc8a0116f8d495db99`. `services/code` now fulfills
the generated Code Service API protocol locally from current runtime semantic
contract truth, and focused service tests plus service compile prove the local
adapter and dependency binding. Follow-up iterations prove section-delta
resolution and semantic-contract conversion while keeping package resolution in
`pyproject.toml`.

## Boundary

The local adapter is intentionally thin. It reads current runtime semantic
contract descriptors from `modules/code/runtime/aware_code`, translates them
into API-owned DTOs from `apis/code`, and exposes service-protocol fulfillment
for local or remote consumers.

This phase does not move runtime semantic contract classes out of
`modules/code/runtime`; that migration can happen later behind the stable Code
Service API boundary.

Code Service publishes layout and semantic DTO truth. FileSystem SDK consumes
those DTOs and owns local path classification/apply behavior. Code Service must
not import FileSystem SDK or FileSystem service internals.

Code Service may resolve API-owned `CodeSectionDeltaSet` into
`CodePackageDelta`. FileSystem SDK remains the owner of
`CodePackageDelta -> FileSystemDeltaSet -> filesystem.delta.apply`.
