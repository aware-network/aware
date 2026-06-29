# Iteration 07 - Code Source Projection Resolve Package Delta

State: `Done`
Owner: `codex-019e49ee-68e0-74c0-a442-ba96f0ff438d`
Approval: `Luis approved in-thread on 2026-05-21`

Phase: `apis/code/docs/specs/code-service-api-semantic-contract/phases/01-apis-code-scaffold/README.md`
Issue: `docs/issues/2026/05/21/fb-2026-05-21-code-source-projection-resolve-package-delta-v0.md`
Sibling spec: `modules/code/docs/specs/semantic-source-projection-contract/SPEC.md`
LOCK: this iteration adds the Code API-owned source_projection package-delta
resolve endpoint and local service adapter only. It must not execute semantic
providers, apply filesystem deltas, or add Workspace orchestration.

## Goal

Expose `code.source_projection.resolve_package_delta` as the Code API/service
bridge from provider-produced `CodeSourceProjectionResult` evidence to
`CodePackageDelta`.

## Scope In

- `apis/code/dto/aware/code/features/source_projection.aware`
- `apis/code/bindings/code.apis.aware`
- generated Code API Python packages under `apis/code/python`
- `services/code/bindings/code.services.aware`
- `services/code/aware.service.toml`
- `services/code/aware_code_service/api_service_protocol.py`
- `services/code/tests`

## Scope Out

- provider execution
- provider-specific source-projection algorithms
- FileSystem SDK apply behavior
- Workspace materialization flow changes

## Expected Deltas

- Generated API DTOs include
  `ResolveCodeSourceProjectionPackageDeltaRequest/Response`.
- Generated Code API client and service protocol include
  `code.source_projection.resolve_package_delta`.
- `services/code` resolves through existing section-delta validation and
  package-delta resolution.
- The service protocol dependency pin is advanced to the new generated API
  hash.

## Proofs (commands)

1. `.venv/bin/aware-cli compile --repo-root /home/luis/aware --json api --api-toml apis/code/aware.api.toml --materialize-service-protocol`
2. `.venv/bin/aware-cli compile --repo-root /home/luis/aware service --service-toml services/code/aware.service.toml`
3. `.venv/bin/python3 -m py_compile services/code/aware_code_service/api_service_protocol.py services/code/tests/test_code_api_service_protocol_unit.py services/code/tests/test_code_service_root_unit.py services/code/tests/test_code_service_implementation_package_unit.py`
4. `.venv/bin/pytest -q services/code/tests/test_code_service_root_unit.py services/code/tests/test_code_api_service_protocol_unit.py services/code/tests/test_code_service_implementation_package_unit.py`
5. `.venv/bin/pytest -q services/code/tests`
6. `.venv/bin/python3 -m compileall -q apis/code/python/aware_code_service_api apis/code/python/aware_code_service_dto apis/code/python/aware_code_service_protocol services/code/aware_code_service services/code/tests`
7. `.venv/bin/flake8 services/code/aware_code_service/api_service_protocol.py services/code/tests/test_code_api_service_protocol_unit.py services/code/tests/test_code_service_root_unit.py services/code/tests/test_code_service_implementation_package_unit.py --select=F,E9`

## Exit Checks

- [x] Source-projection resolve request/response DTOs exist.
- [x] Generated API client dispatches source-projection resolve.
- [x] Generated service protocol dispatches source-projection resolve.
- [x] Local Code service resolves provider result evidence to `CodePackageDelta`.
- [x] Resolver has no Meta, FileSystem, or Workspace imports.

## Sign-Off

- Start: `2026-05-21T13:20:41Z`
- End: `2026-05-21T13:28:06Z`
- Proofs: Code API compile, Code service compile, `py_compile`, and focused
  Code service tests (`32 passed`) passed.
- Commit: `76d7d0738f516237d2cb56406f35e093097d696f`
- Handoff: Meta can now target the Code API result envelope and resolve through
  the source_projection capability instead of bypassing to section_delta.
