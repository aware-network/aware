# Phase 00 - Contract Lock

Status: complete
Owner: `codex-019e2fb7-f5a9-7a21-b305-a26cec2a226b`

## Goal

Lock the semantic ownership direction before `apis/code`, `services/code`,
`sdks/filesystem`, or Workspace consumers move.

## Acceptance

- `apis/code` is declared as the Code semantic contract DTO owner.
- `services/code` is declared as the local adapter over `aware_code` runtime.
- `sdks/filesystem` is declared as the semantic-aware local filesystem helper
  layer over Code DTOs and FileSystem API DTOs.
- Workspace is declared as aggregator of status/materialization/commit/revision
  workflows.
- The invalid dependency directions are explicit.

## Iterations

- `iterations/00-2026-05-19-code-service-api-semantic-contract-lock/README.md`

## Exit Check

Phase 00 exits when the spec package exists and the issue closes with commit
evidence for the lock.

Exit evidence:

- Spec lock commit: `10c95b82bb967c73d02ba4660c6df20395232850`
