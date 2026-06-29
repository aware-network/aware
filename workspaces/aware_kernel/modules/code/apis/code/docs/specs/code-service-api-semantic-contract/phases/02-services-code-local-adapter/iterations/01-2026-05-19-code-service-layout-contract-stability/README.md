# Iteration 01 - Code Service Layout Contract Stability

Owner: `codex-019e2fb7-f5a9-7a21-b305-a26cec2a226b`
Issue: `fb/2026-05-19/code-service-layout-contract-stability-v0`
Status: complete

## Scope

Strengthen the `services/code` proof surface so FileSystem SDK can classify
paths from Code DTOs without depending on Code runtime or service internals.

## Contract

1. Code Service publishes stable `CodeSemanticContract`,
   `CodePackageLayoutContract`, `CodeSemanticProviderBinding`, and
   `CodePackageDelta` protocol behavior.
2. FileSystem SDK consumes Code DTO objects directly.
3. FileSystem SDK may receive DTOs from a generated Code API client supplied by
   a higher-level caller, but it must not import `services/code`.
4. `services/code` must not import FileSystem SDK or FileSystem service
   internals.
5. Code Service does not classify filesystem paths; it only publishes contract
   and layout DTO truth.

## Proofs

- `pytest -q services/code/tests` passed (`15 passed`).
- `python -m compileall -q services/code/aware_code_service services/code/tests`
  passed.
- `flake8 services/code/aware_code_service services/code/tests --select=F,E9`
  passed.
- `aware-cli compile --repo-root /home/luis/aware service --service-toml services/code/aware.service.toml`
  passed.
- Code Service runtime package scan proves no `aware_file_system_sdk`,
  `aware_file_system_service`, or `sdks.filesystem` dependency in
  `services/code/aware_code_service`.

## Sign-Off

- Implementation commit: `7eac9b7bee1886743fc49d0fa5cd4f032e7bcbda`
- Closeout commit: pending
