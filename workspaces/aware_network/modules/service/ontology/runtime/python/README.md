# aware-service-runtime

Canonical runtime package for the `service` module.

## Ownership

- `workspaces/aware_network/modules/service/ontology/runtime/python/**` is the canonical home for shared service runtime contracts and host-neutral orchestration logic.
- Root `libs/services/**` was retired on 2026-06-21; imports must use `aware_service_runtime.*`.
- Generated `handlers/**` remain part of module proof/materialization, but they are not the owner of the generic Service host contract surface.

## Responsibilities

- publish host-neutral service request/context/response contracts
- publish service handler, router, registry, and graph-gateway protocols
- hold temporary compatibility adapters to current Environment-hosted service rails
- support thin app wrappers such as a future `services/service/**` host

## Target Package Layout

- `aware_service_runtime/contracts.py`
  - `ServiceOperationContext`
  - `ServiceOperationRequest`
  - `ServiceOperationResponse`
  - `ServiceOperationHandler`
  - `ServiceHostTransport`
  - `ServiceGraphGateway`
- `aware_service_runtime/registry.py`
  - service discovery and registration
- `aware_service_runtime/router.py`
  - request and notification dispatch
- `aware_service_runtime/gateway/`
  - host-selected graph backend adapters
- `aware_service_runtime/adapters/environment/`
  - compatibility bridge to current Environment payloads
- `aware_service_runtime/receipts.py`
  - service receipt mapping and normalization
- `aware_service_runtime/handlers/`
  - generated module handlers and proof scaffolding

## Rule

New canonical service-contract work should land here, not in root compatibility libs.
