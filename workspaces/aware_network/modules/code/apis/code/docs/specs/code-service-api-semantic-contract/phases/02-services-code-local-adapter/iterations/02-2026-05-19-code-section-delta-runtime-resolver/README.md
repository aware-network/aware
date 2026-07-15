# Iteration 02 - Code Section Delta Runtime Resolver

Owner: `codex-019e2fb7-f5a9-7a21-b305-a26cec2a226b`
Issue: `fb/2026-05-19/code-section-delta-runtime-resolver-v0`
Status: complete

## Scope

Add the first `services/code` resolver behind the API-owned
`CodeSectionDeltaSet` contract.

## Contract

1. `apis/code` owns the section-delta DTOs and generated endpoint refs.
2. `services/code` validates, normalizes, fingerprints, and resolves the DTOs.
3. The first resolver supports `replace_segment` only.
4. Resolution emits `CodePackageDelta`; it does not apply filesystem changes.
5. FileSystem SDK remains the only owner of
   `CodePackageDelta -> FileSystemDeltaSet -> filesystem.delta.apply`.

## Proofs

- `pytest -q services/code/tests` passed (`20 passed`).
- `python -m compileall -q services/code/aware_code_service services/code/tests`
  passed.
- `flake8 services/code/aware_code_service services/code/tests --select=F,E9`
  passed.
- `aware-cli compile --repo-root /home/luis/aware service --service-toml services/code/aware.service.toml`
  passed.
- `resolve_package_delta` returns full file text in `CodePackageDeltaPath`
  after a byte-range `replace_segment`.
- Hash mismatch fails closed with no package delta.
- Code Service runtime package scan proves no `aware_file_system_sdk`,
  `aware_file_system_service`, or `sdks.filesystem` dependency in
  `services/code/aware_code_service`.

## Sign-Off

- Implementation commit: `f5e7c68a22fad80226349458b1275f40b2b15806`
- Closeout commit: pending
