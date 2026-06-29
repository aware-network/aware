# Iteration 05 - Code API DTO Semantic Export

Issue: `fb/2026-05-21/code-api-dto-semantic-export-v0`

## Intent

Put Code on the same API-owned DTO semantic export rail as the other generated
API DTO packages. Code already owns `apis/code/dto`; this iteration makes the
API manifest publish that DTO package as an `api_dto` semantic export and
materializes the generated Python DTO distribution.

## Changes

- `apis/code/aware.api.toml` declares `code-service-dto` as an `api_dto`
  semantic export.
- Code API compile emits `apis/code/python/aware_code_service_dto`.
- Root Python workspace metadata includes `aware_code_service_dto`.

## Acceptance

- [x] Code DTO source remains under `apis/code/dto`.
- [x] Code API manifest owns the DTO semantic export.
- [x] Generated Code DTO package imports through root Python workspace metadata.
- [x] No module API DTO source is introduced.

## Validation

- `uv --cache-dir /tmp/uv-cache run aware-cli compile --repo-root /home/luis/aware --json api --api-toml apis/code/aware.api.toml --materialize-service-protocol`
- `uv --cache-dir /tmp/uv-cache lock --check`
- `uv --cache-dir /tmp/uv-cache run python -c "from aware_code_service_dto.default.code_semantic_contract import CodeSemanticContract; from aware_code_service_dto.default.code_package_delta import CodePackageDelta; from aware_code_service_dto.default.code_service_request import CodeServiceRequest; print(CodeSemanticContract.__name__, CodePackageDelta.__name__, CodeServiceRequest.__name__)"`
- `uv --cache-dir /tmp/uv-cache run python -m compileall -q apis/code/python/aware_code_service_dto`
- `uv --cache-dir /tmp/uv-cache run pytest -q modules/api/runtime/tests/test_api_public_package_materialization.py::test_compile_api_workspace_materializes_api_dto_python_package_from_semantic_export modules/api/runtime/tests/test_api_public_package_materialization.py::test_compile_api_workspace_materializes_api_dto_export_without_dependency`

## Follow-Up

- Continue retiring remaining `modules/**/structure/api` rails API by API now
  that Code's semantic contract DTO package is on the canonical export rail.
