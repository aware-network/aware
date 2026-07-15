# aware-file-system-sdk

Handwritten SDK facade over generated `aware_file_system_service_api` clients,
with Code package delta helpers that consume canonical `aware_code_service_api`
DTOs.

Contract:

- wraps generated FileSystem API client methods for root verification,
  snapshot scan, delta collect, and delta apply
- converts Code API `CodePackageDelta` DTO shape into
  `FileSystemDeltaSet` for local materialization
- classifies checkout paths from Code API `CodePackageLayoutContract` and
  optional `CodeSemanticContract` DTOs without calling Code service endpoints
- receives those DTOs from higher-level consumers such as Workspace SDK; callers
  may fetch them from Code Service, but FileSystem SDK only consumes the API DTO
  objects
- may be used by integration proofs after an external caller resolves
  `CodeSourceProjectionResult` through Code Service into `CodePackageDelta`
- rejects root escapes and inline-content digest mismatches before calling the
  FileSystem API client
- passes `backend_kind` through to the generated FileSystem API so callers can
  request the service-owned Rust backend without importing Rust or service
  internals in the SDK
- does not import Workspace SDK, Workspace runtime, FileSystem service
  internals, or Code service internals
- does not call Code service endpoints; Code API is used as DTO vocabulary

Boundary proof:

- `docs/proofs/integrations/source_projection_filesystem_sdk_apply/test_source_projection_filesystem_sdk_apply.py`
  proves external Code Service orchestration can hand the resolved
  `CodePackageDelta` into FileSystem SDK for local apply receipts without
  moving Code Service ownership into this SDK.

Primary entrypoints:

- `AwareFileSystemSdk`
- `FileSystemCodePackageDeltaClient`
- `FileSystemCodeLayoutClassifier`
- `build_file_system_sdk`
- `build_code_layout_classifier`
