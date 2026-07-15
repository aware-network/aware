# Iteration 03 - Code Semantic Contract Runtime API Adapter

Owner: `codex-019e2fb7-f5a9-7a21-b305-a26cec2a226b`
Issue: `fb/2026-05-19/code-semantic-contract-runtime-api-adapter-v0`
Status: complete

## Scope

Extract and prove the bridge between current runtime `ModuleSemanticContract`
truth and API-owned `CodeSemanticContract` DTO truth.

## Contract

1. `apis/code` owns the cross-boundary semantic contract DTO.
2. `modules/code/runtime/aware_code` still owns runtime provider authoring and
   execution types.
3. `services/code` owns the adapter because it legitimately imports both the
   runtime authoring ABI and generated Code API DTO package.
4. Workspace, FileSystem SDK, and Coordination consumers should consume API DTO
   truth, not runtime provider classes.
5. Workspace migration is intentionally separate from this adapter proof.

## Proofs

- Runtime `AWARE_CODE_SEMANTIC_CONTRACT` roundtrips through
  `CodeSemanticContract`.
- A rich `ModuleSemanticContract` fixture roundtrips through
  `CodeSemanticContract`.
- API DTO validation reports deterministic diagnostics.
- API-only fields that cannot be represented by current `ModuleSemanticContract`
  fail runtime conversion explicitly.
- `services/code` semantic-contract endpoint handlers use the adapter.
- `aware-code-service` resolves through root workspace metadata; Code Service
  tests no longer inject local paths through `sys.path`.
- Path-bootstrap scan over `services/code/tests` and
  `services/code/aware_code_service` returned no matches for `sys.path`,
  `find_aware_repo_root`, or import-order suppressions.
- `pytest -q services/code/tests` passed (`25 passed`).
- `python -m compileall -q services/code/aware_code_service services/code/tests`
  passed.
- `flake8 services/code/aware_code_service services/code/tests --select=F,E9`
  passed.
- `aware-cli compile --repo-root /home/luis/aware service --service-toml services/code/aware.service.toml`
  passed.

## Sign-Off

- Implementation commit: `07b9389048e95dcbd19e96390f97d4c247c1b4e1`
- Closeout commit: pending
