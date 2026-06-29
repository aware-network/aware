# API_CANONICAL

Canonical-only migration tracker for the Interface API package (DTO-only, client mirror).

**Canonical Rules**
- `.aware` + `aware.toml` are the SSOT for schema, DTOs, and workflows; no hand-authored DTOs.
- API-owned DTO and service packages under `apis/*` are the SSOT; API code is plumbing only.
- The Dart API must mirror `workspaces/aware_kernel/modules/api/libs/api/python/README.md` (Python) and will move to `workspaces/aware_kernel/modules/api/libs/api/dart`.
- No ORM/object-sync, no local OIG writes, no filesystem watchers, no app domain logic.
- Any non-DTO state (context, transport config) is ephemeral and non-canonical.

**Canonical Surface (Target)**
- `AwareApiClient` generic endpoint helpers plus compatibility Environment function-call helpers until generated ontology Dart functions move to typed Environment API clients.
- `AwareFileOpsClient` (Dart mirror): compatibility `uploadFile`,
  `downloadFile` for blob storage over the mounted HTTP data-plane. Storage
  API/SDK resolution is the canonical renderer-facing contract; raw Node
  download URLs are not.
- Context: `environment/process/thread/branch/actor` for routing only (no SSOT claims).
- Transport: caller-supplied `ApiEndpointTransport` / `ApiEndpointStreamTransport`.
- DTOs: `apis/*` packages generated from API-owned `.aware` contracts.
- Session bootstrap/persistence is not owned by root API or root Session
  packages. Use Identity, Environment, Interface host/runtime, and generated
  API/SDK rails for the specific semantic operation.

**Current DTO-Only Surface (Keep For Now)**
- `workspaces/aware_network/libs/comms/dart/lib/**` (transport plumbing)
- `workspaces/aware_kernel/modules/api/libs/api/dart/lib/src/client.dart` (`AwareApiClient`) for generic endpoint calls and temporary function-call compatibility.

**Non-Canonical Inventory (Move/Delete)**
- ORM + object sync: `aware_models`, `aware_orm`, `aware_materializer`,
  `OLD/aware_interface_api_dart/meta/graph/**`,
  `OLD/aware_interface_api_dart/runtime/**` (staged),
  `OLD/aware_interface_api_dart/domain/**`,
  `OLD/aware_interface_api_dart/primitive/**`,
  `OLD/aware_interface_api_dart/contract/**`.
- Legacy env client + capability/opg resolvers:
  `OLD/aware_interface_api_dart/service/env_client/**`,
  retired root Session capability/opg resolvers.
- Root `libs/session/dart` was retired on 2026-06-20. Do not introduce
  `aware_session` imports; route behavior to Identity, Environment, Interface,
  Comms, or generated API/SDK owners.
- File system API now lives in `libs/file_system/dart` (non-canonical, local tooling).
- Local SQLite helper moved to `OLD/aware_interface_api_dart/database_helper.dart`.
- App/platform concerns (moved to OLD):
  `OLD/aware_interface_api_dart/service/cli/**`,
  `OLD/aware_interface_api_dart/service/logging_service.dart`,
  `OLD/aware_interface_api_dart/config.dart`,
  `OLD/aware_interface_api_dart/network_discovery_service.dart`,
  `OLD/aware_interface_api_dart/domain/provider/network_node_provider.dart`.
- Stdio harness behavior belongs behind Environment/API/SDK or service-host
  rails, not a root Session package.
- Legacy HTTP service + generated routes:
  `OLD/aware_interface_api_dart/comms/service/http/**`,
  `OLD/aware_interface_api_dart/gen/**`.
- Local environment config loaders:
  (removed; do not reintroduce bundled `environment.json` — use `.aware/environment.json`).

**Migration Plan (Stepwise)**
- [ ] Define the Dart `AwareApiClient` surface to mirror Python (`workspaces/aware_kernel/modules/api/libs/api/python/README.md`).
- [ ] Move any still-needed DTO-only clients/transport into
      `workspaces/aware_kernel/modules/api/libs/api/dart` or generated
      module SDKs (mirror of
      `workspaces/aware_kernel/modules/api/libs/api/python`).
- [ ] Retire legacy env-client + resolver stack once DTO client covers use cases.
- [ ] Remove ORM/object-sync graph/materialization layers from this package.
- [ ] Remove file-system API + local DB helpers from this package.
- [ ] Update this document as features are moved or retired.

**Removal Plan (Completed): Delete `apps/interface_flutter/api`**
Status: Completed on **February 3, 2026** — the deprecated shim was removed and the legacy code archived.

Exit criteria:
- `rg "aware_interface_api_dart" -n` returns empty outside `OLD/` archives and docs.
- No `pubspec.yaml` depends on `aware_interface_api_dart`.
- Dart package generation no longer injects `aware_interface_api_dart` (see `languages/dart/grammar/grammar/dart_grammar/package_strategy.py`).
- All `flutter test`/module tests pass for affected packages.

Reference-only legacy archive:
- `OLD/aware_interface_api_dart/`

**Migration Tracking Docs**
- `workspaces/aware_kernel/modules/api/libs/api/dart/docs/migrations/DTO_CLIENT.md`
- `workspaces/aware_kernel/modules/api/libs/api/dart/docs/migrations/LEGACY_ENV_CLIENT.md`
- `workspaces/aware_kernel/modules/api/libs/api/dart/docs/migrations/LEGACY_ORM_OIG.md`
- `workspaces/aware_kernel/modules/api/libs/api/dart/docs/migrations/FILE_SYSTEM.md`
- `workspaces/aware_kernel/modules/api/libs/api/dart/docs/migrations/SESSION.md`
- `workspaces/aware_kernel/modules/api/libs/api/dart/docs/MOVE_TO_OLD_PLAN.md`
