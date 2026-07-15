# Phase 01 - apis/code Scaffold

Status: complete
Owner: `codex-019e2fb7-f5a9-7a21-b305-a26cec2a226b`

## Goal

Create `apis/code` as the canonical generated API-Service package for Code
semantic contract DTOs and service-protocol endpoints.

## Acceptance

- `apis/code/dto/aware.toml` exists as the API-owned OCG DTO package.
- `apis/code/aware.api.toml` exists as the Code Service API package.
- `apis/code/bindings/code.apis.aware` exposes semantic contract,
  package-delta, package-layout, section-delta, and source-projection
  capabilities.
- Generated Python public package exists for `aware_code_service_api`.
- Generated Python service protocol exists for `aware_code_service_protocol`.
- No new DTO source is introduced under `modules/code/structure/api`.

## Iterations

- `iterations/00-2026-05-19-code-service-api-dto-ocg-scaffold/README.md`
- `iterations/01-2026-05-19-code-service-api-dto-feature-modularization/README.md`
- `iterations/02-2026-05-19-aware-source-explicit-namespace-roots/README.md`
- `iterations/03-2026-05-19-code-service-api-dto-explicit-root-modularization/README.md`
- `iterations/04-2026-05-19-code-service-api-section-delta-dto-contract/README.md`
- `iterations/05-2026-05-21-code-api-dto-semantic-export/README.md`
- `iterations/06-2026-05-21-code-source-projection-capability-dto/README.md`

## Exit Check

Phase 01 exited with implementation commit
`c77493b2da1bf9878219633c1c5e5bcccc722bc5`. The API-owned DTO package
materializes through the Code API compile rail, and generated API/service
protocol packages validate without new DTO source under `modules/code`.

## Source Layout

Code Service DTO source is explicit-root and feature-driven:

- `code/service.aware` owns common request/response envelopes.
- `code/features/semantic_contract.aware` owns semantic contract DTOs and operations.
- `code/features/package_common.aware` owns package common enums.
- `code/features/package_delta.aware` owns package delta DTOs and operations.
- `code/features/package_layout.aware` owns package layout DTOs and operations.
- `code/features/section_delta.aware` owns section/segment delta DTOs and
  resolver protocol operations.
- `code/features/source_projection.aware` owns semantic source-projection
  request/result DTOs and validation/normalization/fingerprint operations over
  `CodeSectionDeltaSet` evidence.

`apis/code/dto/aware.toml` opts into `build.namespace.mode = "explicit_roots"`
with `code/**/*.aware -> default.code`, so physical feature folders are
organizational and generated public DTO FQNs remain `code.*`.

Best-practice target:

- API/DTO packages should support explicit namespace roots.
- Physical nesting under an explicit namespace root should be organizational,
  not semantic identity.
- Layout-derived namespaces remain valid only when a package intentionally
  chooses folder-to-domain/schema identity.
- Code DTO source now uses nested feature folders while preserving `code.*`
  generated DTO FQNs through explicit roots.
