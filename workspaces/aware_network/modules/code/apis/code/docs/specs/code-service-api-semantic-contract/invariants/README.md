# Code Service API Semantic Contract - Invariants

This index lists first-class invariants for the Code Service API semantic
contract spec.

## Invariants

1. `00-code-api-owns-semantic-contract-dtos`
   - `apis/code` is the public DTO and capability endpoint authority for Code
     semantic contracts.
2. `01-filesystem-sdk-resolves-code-semantic-contract`
   - `sdks/filesystem` consumes Code semantic contract DTOs to classify local
     filesystem/code layout and apply file deltas.
3. `02-workspace-aggregates-revision-workflows`
   - Workspace aggregates status, materialization, commit, revision, and
     publication workflows above Code API and FileSystem SDK.

## Proof Anchors

- `apis/code/docs/specs/code-service-api-semantic-contract/SPEC.md`
- `apis/code/docs/specs/code-service-api-semantic-contract/PHASES.md`
- `docs/conversations/2026-05-19-CODE-SEMANTIC-CONTRACT-LOCK.md`
- `docs/issues/2026/05/19/fb-2026-05-19-code-api-semantic-contract-study-v0.md`
