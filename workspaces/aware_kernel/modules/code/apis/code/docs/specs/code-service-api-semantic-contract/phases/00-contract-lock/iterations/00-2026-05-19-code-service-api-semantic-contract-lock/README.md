# Iteration 00 - Code Service API Semantic Contract Lock

Owner: `codex-019e2fb7-f5a9-7a21-b305-a26cec2a226b`
Issue: `fb/2026-05-19/code-service-api-semantic-contract-lock-v0`
Status: complete

## Scope

Create the first spec package for the future `apis/code` semantic contract
owner.

Changed docs:

- `apis/code/docs/specs/code-service-api-semantic-contract/SPEC.md`
- `apis/code/docs/specs/code-service-api-semantic-contract/invariants/README.md`
- `apis/code/docs/specs/code-service-api-semantic-contract/invariants/00-code-api-owns-semantic-contract-dtos/README.md`
- `apis/code/docs/specs/code-service-api-semantic-contract/invariants/01-filesystem-sdk-resolves-code-semantic-contract/README.md`
- `apis/code/docs/specs/code-service-api-semantic-contract/invariants/02-workspace-aggregates-revision-workflows/README.md`
- `apis/code/docs/specs/code-service-api-semantic-contract/PHASES.md`
- `apis/code/docs/specs/code-service-api-semantic-contract/phases/00-contract-lock/README.md`
- `apis/code/docs/specs/code-service-api-semantic-contract/phases/00-contract-lock/iterations/00-2026-05-19-code-service-api-semantic-contract-lock/README.md`

## Inputs

- `docs/conversations/2026-05-19-CODE-SEMANTIC-CONTRACT-LOCK.md`
- `docs/conversations/2026-05-18-AWARE-STATUS-PRODUCT.md`
- `docs/issues/2026/05/19/fb-2026-05-19-code-api-semantic-contract-study-v0.md`
- `modules/code/docs/specs/semantic-capability-contract/SPEC.md`
- FileSystem API-Service precedent under `apis/filesystem` and
  `services/filesystem`

## Decisions

1. `apis/code` owns public semantic contract DTOs.
2. `services/code` adapts runtime implementation into generated DTO/protocol
   boundaries.
3. `sdks/filesystem` consumes Code DTOs and FileSystem DTOs for local semantic
   filesystem helpers.
4. Workspace SDK and Workspace Service consume FileSystem SDK; neither imports
   the other as an implementation shortcut.
5. `aware-dev status` is the first product proof over local filesystem state,
   Code semantic contract DTOs, and Workspace remote authority.

## Proofs

Docs-only checks:

- `test -f apis/code/docs/specs/code-service-api-semantic-contract/SPEC.md`
- `test -f apis/code/docs/specs/code-service-api-semantic-contract/invariants/README.md`
- `test -f apis/code/docs/specs/code-service-api-semantic-contract/PHASES.md`
- `test -f apis/code/docs/specs/code-service-api-semantic-contract/phases/00-contract-lock/README.md`

## Sign-Off

- Implementation commit: `10c95b82bb967c73d02ba4660c6df20395232850`
- Receipt sync commit: pending
