# Code Service API Semantic Contract - PHASES

Status: in progress
Owner: `codex-019e2fb7-f5a9-7a21-b305-a26cec2a226b`

## Phase Ledger

| Phase | Status | Iteration | Issue | Commit |
| --- | --- | --- | --- | --- |
| 00-contract-lock | complete | `phases/00-contract-lock/iterations/00-2026-05-19-code-service-api-semantic-contract-lock/README.md` | `fb/2026-05-19/code-service-api-semantic-contract-lock-v0` | `10c95b82bb967c73d02ba4660c6df20395232850` |
| 01-apis-code-scaffold | complete | `phases/01-apis-code-scaffold/iterations/00-2026-05-19-code-service-api-dto-ocg-scaffold/README.md` | `fb/2026-05-19/code-service-api-dto-ocg-scaffold-v0` | `c77493b2da1bf9878219633c1c5e5bcccc722bc5` |
| 01-dto-feature-modularization | complete | `phases/01-apis-code-scaffold/iterations/01-2026-05-19-code-service-api-dto-feature-modularization/README.md` | `fb/2026-05-19/code-service-api-dto-feature-modularization-v0` | `889a6e7acff42f07cf7a158c85bac0d1a379b90f` |
| 01-explicit-namespace-roots | complete | `phases/01-apis-code-scaffold/iterations/02-2026-05-19-aware-source-explicit-namespace-roots/README.md` | `fb/2026-05-19/aware-source-explicit-namespace-roots-v0` | `a5f4a9c3084ed88861ff00326a205b041fa30545` |
| 01-dto-explicit-root-modularization | complete | `phases/01-apis-code-scaffold/iterations/03-2026-05-19-code-service-api-dto-explicit-root-modularization/README.md` | `fb/2026-05-19/code-service-api-dto-explicit-root-modularization-v0` | `a457eea32979c336f5bf66e8ac940de563526d94` |
| 01-section-delta-dto-contract | complete | `phases/01-apis-code-scaffold/iterations/04-2026-05-19-code-service-api-section-delta-dto-contract/README.md` | `fb/2026-05-19/code-service-api-section-delta-dto-contract-v0` | `af3f9dd3dc31b848f0fc05f800b4cb836661a6a6` |
| 01-code-api-dto-semantic-export | complete | `phases/01-apis-code-scaffold/iterations/05-2026-05-21-code-api-dto-semantic-export/README.md` | `fb/2026-05-21/code-api-dto-semantic-export-v0` | `ea01447eb57c5144f44f7998324d0b8ce410f611` |
| 01-code-source-projection-capability-dto | complete | `phases/01-apis-code-scaffold/iterations/06-2026-05-21-code-source-projection-capability-dto/README.md` | `fb/2026-05-21/code-source-projection-capability-dto-v0` | `8e68b84071f44d259c6c2f170bb226a9181765e1` |
| 01-code-source-projection-resolve-package-delta | complete | `phases/01-apis-code-scaffold/iterations/07-2026-05-21-code-source-projection-resolve-package-delta/README.md` | `fb/2026-05-21/code-source-projection-resolve-package-delta-v0` | `76d7d0738f516237d2cb56406f35e093097d696f` |
| 02-services-code-local-adapter | complete | `phases/02-services-code-local-adapter/iterations/00-2026-05-19-code-service-local-adapter/README.md` | `fb/2026-05-19/code-service-local-adapter-v0` | `0f94a279b57defa6df28a5bc8a0116f8d495db99` |
| 02-code-service-layout-contract-stability | complete | `phases/02-services-code-local-adapter/iterations/01-2026-05-19-code-service-layout-contract-stability/README.md` | `fb/2026-05-19/code-service-layout-contract-stability-v0` | `7eac9b7bee1886743fc49d0fa5cd4f032e7bcbda` |
| 02-code-section-delta-runtime-resolver | complete | `phases/02-services-code-local-adapter/iterations/02-2026-05-19-code-section-delta-runtime-resolver/README.md` | `fb/2026-05-19/code-section-delta-runtime-resolver-v0` | `f5e7c68a22fad80226349458b1275f40b2b15806` |
| 02-code-semantic-contract-runtime-api-adapter | complete | `phases/02-services-code-local-adapter/iterations/03-2026-05-19-code-semantic-contract-runtime-api-adapter/README.md` | `fb/2026-05-19/code-semantic-contract-runtime-api-adapter-v0` | `07b9389048e95dcbd19e96390f97d4c247c1b4e1` |
| 03-filesystem-sdk-code-dto-consumer | planned | pending | pending | pending |
| 04-workspace-aware-dev-consumers | planned | pending | pending | pending |

## Phase 00 - Contract Lock

Goal:

- Lock Code Service API as the semantic contract DTO owner.
- Lock FileSystem SDK as the semantic-aware local filesystem helper layer.
- Lock Workspace as aggregator, not Code/FS semantic owner.

Exit criteria:

- `SPEC.md` exists.
- Invariant index and invariant folders exist.
- Phase 00 iteration artifact exists.
- Issue/feed/day index record the lock.

## Phase 01 - apis/code Scaffold

Goal:

- Add `apis/code/aware.api.toml`.
- Add Code API bindings for semantic contract DTOs and CodePackageDelta DTOs.
- Add API-owned section-delta DTOs and protocol refs before service resolver
  behavior.
- Generate/prove Python API package and service protocol package.
- Lock explicit source namespace roots so future nested DTO feature folders can
  preserve public `code.*` FQNs.
- Move Code DTO feature source under explicit-root feature folders while
  preserving generated public `code.*` FQNs.
- Add the API-owned `source_projection` capability DTO above
  `CodeSectionDeltaSet` and expose validate/normalize/fingerprint endpoint
  refs without provider execution.
- Add the Code-owned `source_projection.resolve_package_delta` bridge from
  provider result evidence to `CodePackageDelta`.

Exit criteria:

- Generated Code service API DTOs exist.
- Generated Code service DTO package is emitted from the API-owned `api_dto`
  semantic export and is importable through root Python workspace metadata.
- Generated Code service protocol exists.
- DTO validation/protocol tests prove no runtime implementation import is
  needed for DTO consumption.
- Manifest and Meta semantic-analysis tests prove explicit namespace roots are
  validated at the package boundary and consumed by OCG analysis.
- Code API compile proves the package-materialization path also consumes
  explicit roots and keeps generated API/service-protocol artifacts stable.
- Section-delta API extension proves generated DTOs and endpoint refs for
  `code.section_delta.validate`, `normalize`, `fingerprint`, and
  `resolve_package_delta` without `services/code` resolver changes.
- Source-projection API extension proves generated DTOs and endpoint refs for
  `code.source_projection.validate`, `normalize`, `fingerprint`, and
  `resolve_package_delta` while reusing `CodeSectionDeltaSet` as provider
  result evidence.

## Phase 02 - services/code Local Adapter

Goal:

- Add `services/code`.
- Implement a local service protocol adapter over `aware_code` runtime.
- Add runtime-to-DTO and DTO-to-runtime-compatible adapter tests.

Exit criteria:

- Generated protocol dispatch works in-process.
- `services/code` can serve semantic contract DTOs from current runtime
  descriptors.
- Runtime/API semantic contract adapter proves `ModuleSemanticContract` can
  roundtrip through API-owned `CodeSemanticContract` for current compatible
  fields.
- `aware-code-service` is registered as a root workspace package/dependency,
  and Code Service tests run without local `sys.path` bootstraps.
- `services/code` can resolve API-owned `CodeSectionDeltaSet` segment
  replacement intent into API-owned `CodePackageDelta` without applying
  filesystem changes.
- `services/code` can resolve API-owned `CodeSourceProjectionRequest` plus
  provider `CodeSourceProjectionResult` evidence into API-owned
  `CodePackageDelta` without provider execution or filesystem apply.
- ServiceHost/remote deployment remains optional.

## Phase 03 - FileSystem SDK Code DTO Consumer

Goal:

- Add or extend `sdks/filesystem`.
- Move reusable `CodePackageDelta -> FileSystemDeltaSet -> delta.apply`
  helpers into FileSystem SDK.
- Add semantic contract DTO layout classification helpers.

Exit criteria:

- FileSystem SDK accepts Code DTO objects directly.
- FileSystem SDK does not import Workspace runtime/service internals.
- FileSystem Service remains generic filesystem fulfillment.

## Phase 04 - Workspace / aware-dev Consumers

Goal:

- Migrate Workspace SDK and Workspace Service to consume FileSystem SDK.
- Make `aware-dev status` the local-first product proof over FS state plus Code
  semantic contract DTOs plus Workspace remote authority.

Exit criteria:

- Workspace SDK does not import Workspace runtime/service internals.
- Workspace Service does not import Workspace SDK.
- Local status can report semantic dirty groups and materialization readiness
  without treating Git as canonical truth.

## Shared Iteration Contract

All implementation iterations follow:

- `docs/specs/TEMPLATE_ITERATIONS_PROTOCOL.md`

Each iteration must map to exactly one issue and record commit evidence here
after the implementation commit lands.
