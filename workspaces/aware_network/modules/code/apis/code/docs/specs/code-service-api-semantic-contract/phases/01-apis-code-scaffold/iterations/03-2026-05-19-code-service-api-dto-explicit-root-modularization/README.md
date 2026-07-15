# Iteration 03 - Code Service API DTO Explicit-Root Modularization

- Issue: `fb/2026-05-19/code-service-api-dto-explicit-root-modularization-v0`
- Status: complete
- Owner: `codex-019e3efc-1c8c-7361-bbbe-6374ded0fb8a`
- Commit: `a457eea32979c336f5bf66e8ac940de563526d94`

## Goal

Move Code Service API DTO feature source into nested folders while preserving
public `code.*` DTO FQNs through the package manifest explicit namespace root.

## Source Layout

`apis/code/dto/aware.toml` declares:

```toml
[build.namespace]
mode = "explicit_roots"

[[build.namespace.roots]]
path = "code/**/*.aware"
domain = "default"
schema = "code"
```

The DTO source layout is:

- `code/service.aware`
- `code/features/semantic_contract.aware`
- `code/features/package_common.aware`
- `code/features/package_delta.aware`
- `code/features/package_layout.aware`

## Proofs

- First compile attempt exposed that Meta package materialization still used the
  layout-derived Structure namespace helper.
- Structure package namespace resolution now accepts explicit roots and fails
  closed for unmatched or conflicting roots.
- `aware-cli compile api --api-toml apis/code/aware.api.toml --materialize-service-protocol`
  materializes `code-service-dto` with 40 DTO nodes under `default.code`.
- Generated API/protocol artifacts contain `aware_code_service_dto.default.code.*`
  refs and no `code.features` drift.
- Generated import smoke keeps endpoint ref `code.semantic_contract.describe`.
