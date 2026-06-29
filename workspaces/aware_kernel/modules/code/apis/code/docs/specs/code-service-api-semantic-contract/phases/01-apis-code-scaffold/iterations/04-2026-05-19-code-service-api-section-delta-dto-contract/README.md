# Iteration 04 - Code Service API Section Delta DTO Contract

- Issue: `fb/2026-05-19/code-service-api-section-delta-dto-contract-v0`
- Status: complete
- Owner: `codex-019e3ee9-cbdb-7351-a412-b3a317a3c5f3`
- Commit: `af3f9dd3dc31b848f0fc05f800b4cb836661a6a6`

## Goal

Add the API-owned section/segment delta DTO contract before any service
resolver, Meta adapter, Workspace orchestration, or FileSystem SDK apply work.

## Contract

The API rail is:

```text
semantic event
  -> CodeSectionDeltaSet
  -> code.section_delta.resolve_package_delta
  -> CodePackageDelta
```

This iteration only defines DTOs and generated protocol refs. Resolver behavior
lands later in `services/code`.

## DTO Surface

- `CodeSectionDeltaOperationKind`
- `CodeSectionRef`
- `CodeSegmentRef`
- `CodeSectionDeltaEntry`
- `CodeSectionDeltaSet`
- `ValidateCodeSectionDeltaRequest/Response`
- `NormalizeCodeSectionDeltaRequest/Response`
- `FingerprintCodeSectionDeltaRequest/Response`
- `ResolveCodeSectionDeltaPackageDeltaRequest/Response`

## Endpoint Refs

- `code.section_delta.validate`
- `code.section_delta.normalize`
- `code.section_delta.fingerprint`
- `code.section_delta.resolve_package_delta`

## Boundary

- `apis/code` owns the DTO and protocol vocabulary.
- `services/code` will later implement `CodeSectionDeltaSet -> CodePackageDelta`.
- Meta will later adapt OCG semantic events into `CodeSectionDeltaSet`.
- FileSystem SDK continues to apply only `CodePackageDelta` and has no role in
  this API contract iteration.

## Proofs

- `aware-cli compile --repo-root /home/luis/aware --json api --api-toml apis/code/aware.api.toml --materialize-service-protocol`
  materialized `code-service-dto` with 53 DTO nodes.
- Generated endpoint refs exist for `code.section_delta.validate`,
  `code.section_delta.normalize`, `code.section_delta.fingerprint`, and
  `code.section_delta.resolve_package_delta`.
- Generated API/protocol compileall and import smoke passed.
- `services/code/aware.service.toml` refreshed only the generated Code API
  service-protocol dependency pin; no section-delta resolver logic was added.
- `pytest -q services/code/tests` passed (`15 passed`).
