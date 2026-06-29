# Invariant 01 - FileSystem SDK Resolves Code Semantic Contract

## Contract

`sdks/filesystem` is the semantic-aware local filesystem helper layer.

It consumes generated Code API DTOs and generated FileSystem API DTOs to build
local status, layout classification, and delta apply workflows.

## Must Hold

- FileSystem SDK accepts `CodeSemanticContract`, `CodePackageDelta`, and
  package-layout DTO objects directly.
- FileSystem SDK owns `CodePackageDelta -> FileSystemDeltaSet`.
- FileSystem SDK owns local path/root/digest/layout classification helpers.
- FileSystem SDK uses generated FileSystem API clients or injected local
  clients for scan/collect/apply.
- Optional Code API fetch hooks are additive; core local status can run from
  DTOs already present on disk or in a local status index.

## Must Not Happen

- FileSystem Service must not become semantic-aware Workspace logic.
- FileSystem SDK must not import Workspace runtime/service internals.
- FileSystem SDK must not require remote Code API calls for basic local status.
- FileSystem SDK must not own WorkspaceRevision truth.

## Proof Direction

- SDK tests map Code DTO deltas to `FileSystemDeltaSet`.
- SDK tests classify path/layout ownership from Code semantic contract DTOs.
- SDK tests prove generated FileSystem API client injection.
- Import-boundary scans prove no Workspace service/runtime imports.
