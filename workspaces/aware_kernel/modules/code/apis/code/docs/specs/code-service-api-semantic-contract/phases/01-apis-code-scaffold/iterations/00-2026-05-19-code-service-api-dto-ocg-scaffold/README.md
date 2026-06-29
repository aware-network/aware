# Iteration 00 - Code Service API DTO OCG Scaffold

Owner: `codex-019e2fb7-f5a9-7a21-b305-a26cec2a226b`
Issue: `fb/2026-05-19/code-service-api-dto-ocg-scaffold-v0`
Status: complete

## Scope

Create the first generated Code Service API scaffold with DTO source ownership
under `apis/code`.

Changed source:

- `apis/code/dto/aware.toml`
- `apis/code/dto/aware/code/semantic_contract.aware`
- `apis/code/aware.api.toml`
- `apis/code/bindings/code.apis.aware`

Expected generated outputs:

- `apis/code/python/aware_code_service_api`
- `apis/code/python/aware_code_service_protocol`

## Contract

1. DTO source lives under `apis/code/dto`, not under `modules/code`.
2. Code Service API endpoints reference `aware_code_service_dto` request and
   response classes.
3. The generated service protocol is the public operation boundary for later
   `services/code` local adapter work.
4. Runtime `aware_code` remains an implementation adapter only.

## Proofs

Planned:

- `.venv/bin/aware-cli compile package code-service-dto`
- `.venv/bin/aware-cli compile api --api-toml apis/code/aware.api.toml --materialize-service-protocol`
- `test -f apis/code/python/aware_code_service_api/aware_code_service_api/client.py`
- `test -f apis/code/python/aware_code_service_protocol/aware_code_service_protocol/protocols.py`
- Import-boundary scan confirming this iteration did not add DTO source under
  `modules/code/structure/api`.

Actual:

- `.venv/bin/aware-cli compile package code-service-dto` intentionally failed
  because standalone package compile currently resolves module-owned packages
  only. This confirms the DTO package is not module-owned.
- `.venv/bin/aware-cli compile --repo-root /home/luis/aware --json api --api-toml apis/code/aware.api.toml --materialize-service-protocol`
  succeeded. The API compiler materialized `code-service-dto` through the API
  Meta dependency graph, then generated `aware_code_service_api` and
  `aware_code_service_protocol`.
- Generated file checks passed for:
  - `apis/code/python/aware_code_service_api/aware_code_service_api/client.py`
  - `apis/code/python/aware_code_service_protocol/aware_code_service_protocol/protocols.py`
- Python compile/import smoke passed for generated API and service protocol
  packages, including endpoint ref
  `code.semantic_contract.describe`.
- Boundary scan passed: no new `CodeSemanticContract`,
  `code-service-dto`, or `aware_code_service` source landed under
  `modules/code/structure/api`.

## Sign-Off

- Implementation commit: `c77493b2da1bf9878219633c1c5e5bcccc722bc5`
- Receipt sync: recorded in the issue closeout receipt.
