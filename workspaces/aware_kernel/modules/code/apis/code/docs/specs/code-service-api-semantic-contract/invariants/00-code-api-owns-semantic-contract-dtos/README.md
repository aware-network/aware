# Invariant 00 - Code API Owns Semantic Contract DTOs

## Contract

`apis/code` is the public schema authority for Code semantic contract DTOs.

This includes:

- `CodeSemanticContract`
- capability participation/execution-policy descriptors
- semantic scope/profile/bundle descriptors
- syntax lane descriptors
- package role descriptors
- artifact ownership descriptors
- materialization input/output/runtime/context descriptors
- `CodePackageDelta`
- package layout/path-role contract DTOs
- semantic provider binding DTOs

## Must Hold

- Cross-workspace consumers import generated Code API DTOs, not
  `aware_code` runtime dataclasses, as the public semantic contract boundary.
- `services/code` can adapt runtime classes into DTOs, but the DTO schema is
  owned by `apis/code`.
- `modules/code/runtime/aware_code` remains the implementation engine and
  compatibility source during migration.
- The current `ModuleSemanticContract` shape is mirrored before consumers are
  forced to migrate.

## Must Not Happen

- Do not make `modules/code/structure/api` the permanent public API owner.
- Do not require FileSystem SDK or Workspace SDK to import Code runtime
  registries to understand semantic contract shape.
- Do not reduce the API to a thin service-status shape. The full semantic
  contract descriptor surface must be DTO-addressable.

## Proof Direction

- Generated Code API DTO package exists under `apis/code`.
- Generated Code service protocol exists under `apis/code`.
- Runtime-to-DTO adapter tests prove the current runtime contract can be
  represented without losing descriptor families.
- Import-boundary tests prove consumers can read DTOs without importing
  provider runtime implementation modules.
