# Iteration 00 - Code Service Local Adapter

Owner: `codex-019e2fb7-f5a9-7a21-b305-a26cec2a226b`
Issue: `fb/2026-05-19/code-service-local-adapter-v0`
Status: complete

## Scope

Add `services/code` as the local implementation package behind the generated
Code Service API protocol.

Implemented surface:

- `aware_code_service.service_bindings:build_service_bindings`
- `aware_code_service.api_service_protocol`
- `aware_code_service.local_api_client`
- `aware_code_service.service_providers`

Implemented endpoint groups:

- `code.semantic_contract`
- `code.package_delta`
- `code.package_layout`

## Contract

1. Code semantic DTO ownership stays in `apis/code`.
2. Code Service protocol ownership stays in generated
   `aware_code_service_protocol`.
3. `services/code` is a local adapter over runtime truth, not a new DTO owner.
4. Runtime semantic contract classes remain in `modules/code/runtime` for this
   phase and are translated into API DTOs at the service boundary.
5. FileSystem SDK and Workspace consumers should consume the generated API
   client/service protocol, not runtime internals.

## Proofs

- `services/code/aware.service.toml` declares `code-service-api` as an
  `api_service_protocol` dependency with expected hash
  `16877758831f51f14b45f5eb13b6d115a9650d1c3bcc5f1f3f437e0d076d14d6`.
- `pytest -q services/code/tests` passed (`10 passed`).
- `python -m compileall -q services/code/aware_code_service services/code/tests`
  passed.
- `flake8 services/code/aware_code_service services/code/tests --select=F,E9`
  passed.
- `aware-cli compile --repo-root /home/luis/aware service --service-toml services/code/aware.service.toml`
  passed and materialized
  `.aware/service/runtime/aware-code-service/service.manifest.json`.

## Sign-Off

- Implementation commit: `0f94a279b57defa6df28a5bc8a0116f8d495db99`
- Closeout commit: pending
