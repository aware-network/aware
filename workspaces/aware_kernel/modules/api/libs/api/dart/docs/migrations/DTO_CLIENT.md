# DTO Client Migration

Migration tracker for moving the DTO-only API client into `workspaces/aware_kernel/modules/api/libs/api/dart`
as a mirror of `workspaces/aware_kernel/modules/api/libs/api/python/README.md`.

**Canonical Target**
- Package: `workspaces/aware_kernel/modules/api/libs/api/dart` (mirror of `workspaces/aware_kernel/modules/api/libs/api/python`).
- Client: `AwareApiClient` with generic endpoint helpers plus temporary
  function-call compatibility.
- Transport: caller-supplied endpoint transport; no Riverpod dependency.
- Dependencies: no legacy module-owned Dart API DTO packages.

**Retired Source Inventory**
- Root `libs/session/dart` DTO clients were retired on 2026-06-20. If any
  behavior is still needed, expose it through generated Environment,
  Network/Node, Agent/Inference, Language/Service, or API SDK clients rather
  than reintroducing a root Session package.
- Transport: `workspaces/aware_network/libs/comms/dart/lib/**`.
- Bootstrap/context: Interface host/runtime plus Identity and Environment
  API/SDK rails own the relevant state.

**Canonical Gaps (Must Resolve)**
- Riverpod providers and app-facing context storage are coupled to API client.
- Some DTO clients may still need generated module SDK surfaces rather than a
  single root `AwareApiClient` surface.
- Transport config is mixed with app/session logic.

**Phase Plan**
- [x] Define `AwareApiConfig` + `AwareApiContext` in `workspaces/aware_kernel/modules/api/libs/api/dart`.
- [x] Build `AwareApiClient` around endpoint operations (ensure ready, capabilities, invoke).
- [ ] Move/duplicate minimal transport pieces into `workspaces/aware_kernel/modules/api/libs/api/dart` (or shared comms).
- [ ] Replace Riverpod providers with explicit dependency injection.
- [x] Remove deprecated shim package (`apps/interface_flutter/api`) once all consumers migrated (**completed February 3, 2026**).

**Dependencies / Open Questions**
- Confirm the canonical comms boundary for Dart (`workspaces/aware_network/libs/comms` vs local).
- Define streaming DTO surfaces (inference/language) in the owning module APIs
  or SDKs.
