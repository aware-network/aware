# Move-To-OLD Plan

Plan for moving non-canonical API code into repo-root `OLD/aware_interface_api_dart/`
once App canonical migrations remove dependencies.

**Status (Completed February 3, 2026)**: Legacy Interface API code has been moved to `OLD/aware_interface_api_dart/` and the deprecated package `apps/interface_flutter/api` has been deleted.

**Goal**
- Keep only DTO-only client plumbing in the API package.
- Move/remove everything else in coordinated batches with the App team.

**Phase 0: Dependency Audit (App → API)**
- App currently imports: `comms/**`, `session/**`, `environment/**`, `service/**`,
  `domain/**`, `file_system/**`, `runtime/**`, `database_helper.dart`,
  and legacy `object/**` + `comms/gen/**` (from older API eras).
- Canonical-only target should only need DTO client + transport.

**Phase 1: Freeze Non-Canonical Surfaces**
- No new app/module imports from `domain/**`, `file_system/**`, `runtime/**`,
  `env_client/**`, `environment_*_resolver*`, or legacy `object/**`.
- New usage must go through DTO clients or module representation packages.

**Phase 2: Move To OLD (Batch-Gated by App Migrations)**
- [x] Batch 0: Session + node selection moved to `libs/session/dart`; comms moved to `workspaces/aware_network/libs/comms/dart`
  - Paths: `lib/session/**`, `lib/environment/**`,
    `lib/service/environment_dto_client.dart`,
    `lib/service/network_node_dto_client.dart`,
    `lib/service/node_selection_service.dart`,
    `lib/domain/util/find_aware_root.dart`.
  - Comms: `lib/comms/**` → `workspaces/aware_network/libs/comms/dart/lib/**`.
  - Status: SSOT in `libs/session/dart`; imports point directly to `aware_session`.
- [x] Batch A: File system + local DB
  - Paths: `lib/file_system/**` → `libs/file_system/dart/lib/file_system/**`
  - DB helper: `lib/database_helper.dart` → `OLD/aware_interface_api_dart/database_helper.dart`
  - Status: file system is now a standalone package (`aware_file_system`) with no interface_api deps.
- [ ] Batch B: Legacy env client + resolvers
  - Paths: `lib/service/env_client/**`,
    `lib/session/environment_capability_resolver_provider.dart`,
    `lib/session/environment_opg_resolver_provider.dart`,
    `lib/domain/util/fqn_resolver.dart`
  - Gate: App invokes functions via DTO-only clients or `AwareApiClient`.
  - Status: env_client moved to `OLD/aware_interface_api_dart/service/env_client/**`.
- [ ] Batch C: ORM/OIG/runtime/materialization
  - Paths: `lib/runtime/**`, `lib/meta/graph/**`, `lib/primitive/**`,
    `lib/domain/**`, `lib/contract/**`
  - Gate: App removes OIG/materializer usage; modules supply DTO-first surfaces.
  - Status: runtime moved to `lib/OLD/runtime/**` (compatibility only),
    primitive moved to `lib/OLD/primitive/**`,
    contract moved to `lib/OLD/contract/**`.
- [ ] Batch D: CLI + discovery helpers
  - Paths: `lib/service/cli/**`, `lib/service/network_discovery_service.dart`,
    `lib/domain/provider/network_node_provider.dart`
  - Gate: App shell has canonical replacement or removes these features.
- [x] Batch G: Node discovery + comms state (legacy)
  - Paths: `lib/domain/provider/{network_node,dns,finance_entity}_provider.dart`
    `lib/comms/{constant,model,provider}/**`,
    `lib/comms/service/duplex/webrtc/**`,
    `lib/comms/service/environment_operation_transport.dart`
  - Status: moved to `OLD/aware_interface_api_dart/**` (node selection now lives in `libs/session`).
- [x] Batch H: Streaming service rails
  - Paths: `lib/service/inference_stream_service.dart`,
    `lib/service/language_service_stream_service.dart`
  - Status: moved to `libs/session/dart/lib/service/**`.
- [x] Batch I: CLI + logging + stdio harness
  - Paths: `lib/service/cli/**`, `lib/service/logging_service.dart`,
    `lib/service/environment_dto_stdio_client.dart`
  - Status: CLI/logging moved to `OLD/aware_interface_api_dart/service/**`;
    stdio harness moved to `libs/session/dart/lib/service/environment_dto_stdio_client.dart`.
- [x] Batch K: App config constants
  - Paths: `lib/config.dart`
  - Status: moved to `OLD/aware_interface_api_dart/config.dart`.
- [x] Batch J: Domain + meta graph stack
  - Paths: `lib/domain/**`, `lib/meta/**`
  - Status: moved to `OLD/aware_interface_api_dart/domain/**` and
    `OLD/aware_interface_api_dart/meta/**` (imports now reference OLD).
- [ ] Batch E: Legacy generated routes/handlers
  - Paths: `lib/comms/gen/**`, any `lib/object/**` if reintroduced
  - Gate: No app references or tests rely on legacy sync routes.
 - [x] Batch F: Legacy HTTP service + generated HTTP routes
   - Paths: `lib/comms/service/http/**`, `lib/comms/gen/http/**`,
     `lib/comms/gen/http_routes.dart`, `lib/comms/gen/http_registry.dart`,
     `lib/domain/provider/auth_session_provider.dart`
   - Status: moved to `OLD/aware_interface_api_dart/**` (no non-OLD imports).

**Phase 3: Canonical Consolidation**
- [ ] Define `workspaces/aware_kernel/modules/api/libs/api/dart` mirror of `workspaces/aware_kernel/modules/api/libs/api/python/README.md`.
- [x] Removed the deprecated shim package `apps/interface_flutter/api` (use `workspaces/aware_kernel/modules/api/libs/api/dart` directly).
- [ ] Remove `OLD/aware_interface_api_dart/` once app + modules are canonical.

**Notes**
- Interim moves may land under `lib/OLD/**` to keep package imports compiling.
- Final move to repo-root `OLD/aware_interface_api_dart/` happens after App removes imports.
- Prefer “move to OLD” before delete, then delete once canonical is stable.
