# Iteration 06 - Code Source Projection Capability DTO

State: `Done`
Owner: `codex-019e49ee-68e0-74c0-a442-ba96f0ff438d`
Approval: `Luis approved in-thread on 2026-05-21`

Phase: `apis/code/docs/specs/code-service-api-semantic-contract/phases/01-apis-code-scaffold/README.md`
Issue: `docs/issues/2026/05/21/fb-2026-05-21-code-source-projection-capability-dto-v0.md`
Sibling spec: `modules/code/docs/specs/semantic-source-projection-contract/SPEC.md`
LOCK: this iteration may add the API-owned `source_projection` DTO and protocol
envelope only. It must not execute providers, apply filesystem changes, or make
Workspace coordinate semantic meaning.

## Goal

Materialize the Code API-owned `source_projection` capability DTO above the
landed `CodeSectionDeltaSet` rail.

## Scope In

- `apis/code/dto/aware/code/features/source_projection.aware`
- `apis/code/bindings/code.apis.aware`
- generated Code API Python packages under `apis/code/python`
- `services/code/aware_code_service/api_service_protocol.py`
- `services/code/tests`
- Code API semantic-contract spec receipts for this iteration

## Scope Out

- provider execution
- provider-to-CodeSectionDeltaSet algorithms
- FileSystem apply behavior
- Workspace orchestration
- module-owned API DTO source

## Expected Deltas

- `source_projection.aware` defines request/result DTOs that reference
  `CodeSectionDeltaSet` instead of duplicating section-delta schema.
- `code.source_projection.validate`, `normalize`, and `fingerprint` materialize
  through generated Code API and service-protocol packages.
- `services/code` exposes a thin local adapter for envelope validation,
  normalization, and fingerprinting only.

## Proofs (commands)

1. `uv run aware-cli compile --repo-root /home/luis/aware --json api --api-toml apis/code/aware.api.toml --materialize-service-protocol`
2. `uv run aware-cli compile --repo-root /home/luis/aware service --service-toml services/code/aware.service.toml`
3. `uv run python -m py_compile services/code/aware_code_service/api_service_protocol.py services/code/tests/test_code_api_service_protocol_unit.py services/code/tests/test_code_service_root_unit.py services/code/tests/test_code_service_implementation_package_unit.py`
4. `uv run pytest -q services/code/tests/test_code_service_root_unit.py services/code/tests/test_code_api_service_protocol_unit.py`
5. `uv run pytest -q services/code/tests`
6. `uv run python -m compileall -q apis/code/python/aware_code_service_api apis/code/python/aware_code_service_dto apis/code/python/aware_code_service_protocol services/code/aware_code_service services/code/tests`
7. `uv run flake8 services/code/aware_code_service/api_service_protocol.py services/code/tests/test_code_api_service_protocol_unit.py services/code/tests/test_code_service_root_unit.py services/code/tests/test_code_service_implementation_package_unit.py --select=F,E9`
8. `uv run python -c "from aware_code_service_api.models.code_source_projection_request import CodeSourceProjectionRequest; from aware_code_service_dto.default.code_source_projection_result import CodeSourceProjectionResult; from aware_code_service_protocol.protocols import CODE__SOURCE_PROJECTION__VALIDATE_ENDPOINT_REF; print(CodeSourceProjectionRequest.__name__, CodeSourceProjectionResult.__name__, CODE__SOURCE_PROJECTION__VALIDATE_ENDPOINT_REF)"`

## Proof Receipts

- Code API compile materialized 68 DTO nodes and generated source-projection
  client/protocol refs.
- Code service compile completed after updating the API service-protocol pin and
  service binding declarations.
- `py_compile` passed for touched service implementation and tests.
- Focused Code service protocol/root tests passed: `25 passed`.
- Full Code service test slice passed: `31 passed`.
- Generated Code API/DTO/protocol packages and Code service modules passed
  `compileall`.
- Flake8 F/E9 passed for touched Python files.
- Root Python import smoke printed
  `CodeSourceProjectionRequest CodeSourceProjectionResult code.source_projection.validate`.
- `rg -n "sys\\.path|path\\.insert|PYTHONPATH" ...` only matched the README
  guardrail text.

## Exit Checks

- [x] `source_projection.aware` exists under `apis/code/dto/aware/code/features`.
- [x] Generated Code API client exposes `code.source_projection`.
- [x] Generated Code service protocol exposes `CodeSourceProjectionCapabilityServiceProtocol`.
- [x] Local Code service adapter validates, normalizes, and fingerprints source-projection envelopes.
- [x] No provider/FileSystem/Workspace execution behavior is introduced.

## Roadblock Rules

Mark `Roadblock` and stop if:

- source-projection DTOs require a second section-delta schema.
- the generated API rail cannot express the capability without module-owned API
  DTO source.
- provider execution becomes necessary for this envelope proof.

## Sign-Off

- Start: `2026-05-21T11:39:11Z`
- End: `2026-05-21T11:54:24Z`
- Proofs: Code API compile, Code service compile, `py_compile`, focused tests
  (`25 passed`), full service tests (`31 passed`), `compileall`, flake8 F/E9,
  import smoke, and no local `sys.path` usage beyond README guardrail text.
- Commit: `8e68b84071f44d259c6c2f170bb226a9181765e1`
- Handoff: after this lands, the next lane can prove a provider emitting
  `CodeSectionDeltaSet` through the Code-owned source-projection contract.
