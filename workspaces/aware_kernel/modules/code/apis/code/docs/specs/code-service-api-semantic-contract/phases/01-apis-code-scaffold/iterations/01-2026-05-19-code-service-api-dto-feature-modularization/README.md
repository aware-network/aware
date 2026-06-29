# Iteration 01 - Code Service API DTO Feature Modularization

Owner: `codex-019e2fb7-f5a9-7a21-b305-a26cec2a226b`
Issue: `fb/2026-05-19/code-service-api-dto-feature-modularization-v0`
Status: complete

## Scope

Refactor the Code Service DTO source layout from one large `.aware` file into
a same-schema, feature-driven layout that preserves generated DTO FQNs.

Final source layout:

- `apis/code/dto/aware/code/service.aware`
- `apis/code/dto/aware/code/semantic_contract.aware`
- `apis/code/dto/aware/code/package_common.aware`
- `apis/code/dto/aware/code/package_delta.aware`
- `apis/code/dto/aware/code/package_layout.aware`

## Contract

1. Code Service DTOs stay API-owned under `apis/code/dto`.
2. Common operation envelopes live in `code/service.aware`.
3. Feature DTOs live in same-schema files under `code/` so public `code.*`
   DTO FQNs remain stable.
4. Nested feature directories are not used for this DTO package because they
   change the `.aware` schema namespace.
5. Generated API and service protocol output remains behaviorally stable.

## Proofs

- A nested `code/features/*.aware` trial failed with unresolved `code.*` class
  references, proving nested folders are not the right namespace shape for this
  DTO package.
- `.venv/bin/aware-cli compile --repo-root /home/luis/aware --json api --api-toml apis/code/aware.api.toml --materialize-service-protocol`
  succeeded after the same-schema split.
- The compile materialized `code-service-dto` with 40 DTO nodes.
- Generated `aware_code_service_api` and `aware_code_service_protocol`
  packages were materialized.
- Import smoke confirms endpoint ref
  `code.semantic_contract.describe` remains stable.

## Sign-Off

- Implementation commit: `889a6e7acff42f07cf7a158c85bac0d1a379b90f`
- Closeout commit: pending
