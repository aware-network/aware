# Legacy ORM + OIG Migration

Migration tracker for removing ORM/object-sync and local OIG materialization
from the Interface API package.

**Canonical Target**
- No ORM or object graph write logic in this package.
- OIG commits are produced/consumed by the node/runtime, not clients.
- Clients only handle DTOs and transport responses.

**Source Inventory (Legacy)**
- Dependencies: `aware_models`, `aware_orm`, `aware_materializer`.
- Runtime/context: `OLD/aware_interface_api_dart/runtime/**`.
- OIG/materialization: `OLD/aware_interface_api_dart/meta/graph/instance/**`.
- Primitive/ORM helpers: `workspaces/aware_network/libs/comms/dart/lib/converters.dart`,
  `OLD/aware_interface_api_dart/primitive/**`,
  `OLD/aware_interface_api_dart/contract/**`.
- Domain providers tied to ORM models: `OLD/aware_interface_api_dart/domain/**`.

**Canonical Gaps (Must Remove/Replace)**
- ORM session/context is non-canonical and duplicates runtime behavior.
- Local graph/materialization conflicts with DTO-only client philosophy.
- Model resolvers and helpers depend on legacy `aware_models`.

**Phase Plan**
- [ ] Identify remaining consumers of `aware_models` within this package.
- [ ] Remove ORM/session-based flows from API clients and services.
- [ ] Delete `meta/graph/instance` and runtime context after consumers migrate.
- [ ] Drop `aware_models`, `aware_orm`, `aware_materializer` from `pubspec.yaml`.

**Dependencies / Open Questions**
- Confirm any remaining app features depending on local materialization.
- Define replacement DTO flows for any required read models.
