# aware-api-runtime

Runtime package for `aware.api.toml` binding workspaces.

## Scope

`workspaces/aware_kernel/modules/api/ontology/runtime/python` owns the runtime/compiler path for API binding packages.

It does not own API type package compilation.

The split is:

- `apis/<api_name>/packages/...`
  - real `kind = "api"` packages colocated under one API package root
  - compiled through the normal package / OCG rails
- `apis/<api_name>/bindings/...`
  - reference-only `.apis.aware` files for that API package root
  - compiled through `aware.api.toml`
  - owned by `workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime`

- `apis/<api_name>/aware.api.toml`
  - API linker/build manifest for that package root

This means API runtime is the linker/runtime layer between:

- API type DTO classes
- API binding declarations
- canonical graph invocation

## Current Compile Pipeline

Today the binding compiler path is:

1. [workspace.py](/home/luis/aware/workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/workspace.py)
   - loads `aware.api.toml`
   - scans binding sources only
2. [compiler.py](/home/luis/aware/workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/compiler.py)
   - parses `api { ... }` binding declarations
   - builds ownership rows
3. [builder.py](/home/luis/aware/workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/builder.py)
   - emits `api.compile_plan.json`
   - includes both `api_ownership` and `api_ontology`
4. [graph/ontology.py](/home/luis/aware/workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/graph/ontology.py)
   - lowers ownership into canonical API ontology operations

The compile plan ontology is the runtime contract.

Runtime must not depend on reparsing `.apis.aware` text after compile.

## Canonical Runtime Target

The target runtime model is ontology-only.

That means API resolution should run from compiled ontology objects like:

- `ApiCapabilityEndpoint`
- `ApiCapabilityEndpointFunction`
- `ApiGraphProjectionContract`
- `ApiGraphCapabilityFunction`
- `ApiGraphFunction`

and not from:

- raw binding text
- ad-hoc string anchors
- transport-specific routing hacks

The boundary is:

- keys answer which instance
- endpoint functions answer which action
- runtime bridges both onto canonical graph invocation

## Resolution Model

Runtime resolution should follow this order:

1. accept world-facing key payloads plus endpoint intent
2. resolve the projection key contract through `ApiGraphProjectionContract`
3. derive the target class instance identity from those keys
4. resolve the endpoint function through `ApiCapabilityEndpointFunction`
5. follow that binding to `ApiGraphCapabilityFunction`
6. follow graph capability binding to canonical `ApiGraphFunction`
7. hand off resolved graph-call intent to the API-owned service protocol or generated service SDK/API rail
8. invoke committed graph mutation through Environment SDK/API when environment context is required, or through Meta API when the service is Meta itself
9. emit `ApiCall`, Meta commit, and service receipt evidence without making API runtime the graph mutation owner

In plain terms:

- projection rails resolve identity
- endpoint rails resolve action
- runtime performs the bridge

API consumers must never need to provide:

- internal class-instance ids
- internal graph paths
- projection internals

## Runtime Primitives

Target production dependencies are:

- compiled API ontology and endpoint metadata
- generated public API package
- generated API-owned service protocol package
- `ServiceApiDispatchRequest` / resolved invocation envelopes as downstream handoff truth
- generated Environment SDK/API for environment-scoped graph execution
- generated Meta API/SDK for Meta graph mutation authority

Compatibility-only dependencies during migration:

- `FunctionCallInvoker`
- `RuntimeHarness`
- `AwareRuntimeIndex`
- environment/runtime resolver rails used by local proof/materialization paths
- legacy lane-operation receipts from direct runtime invocation

The important non-goal:

- [runtime_harness.py](/home/luis/aware/libs/runtime/aware_runtime/harness/runtime_harness.py) is not the production API resolution owner

`RuntimeHarness` is a proof/testing helper:

- manifest bootstrap
- lane binding for tests
- direct invoke helpers for module proofs

It is useful for proofs of the API runtime contract, but it should not become the architecture boundary for API request resolution.

## Current Repo State

The repo is currently in a mixed state.

New canonical ontology rails already exist in generated API ontology:

- `ApiCapabilityEndpointFunction`
- `ApiGraphProjectionContract`
- `ApiGraphCapabilityFunction`

But part of the runtime/materialization layer is still legacy:

- [materialization/service.py](/home/luis/aware/workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/materialization/service.py)
- legacy `ProjectionApi*` imports/rows still appear there
- some generated handler rails still reference `ProjectionApi` / `ProjectionApiContract`

That legacy state should be treated as migration debt, not as the target architecture.

## Direction Lock

Runtime evolution should happen in this order:

1. read compiled ontology only
2. resolve keys to class instance identity
3. resolve endpoint function to canonical graph function
4. materialize `ApiCall` under API runtime ownership
5. hand off to generated API-owned service protocol surfaces
6. use generated Environment SDK/API or Meta API for committed graph mutation
7. emit API, Meta commit, and service receipt provenance
8. remove legacy `ProjectionApi*` materialization/runtime assumptions
9. quarantine and then retire direct `FunctionCallInvoker`/`RuntimeHarness` production use
10. only then expand authored grammar for explicit endpoint blocks

This order matters because grammar is authored surface, while identity-plus-action resolution is the actual product boundary.

## Package Boundary

[package/spec.py](/home/luis/aware/workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/package/spec.py) owns the `aware.api.toml` contract for binding packages.

That package contract is separate from API type package contracts:

- API type packages use the normal `aware.toml` package rails under `packages/`
- API binding packages use `aware.api.toml` at the API package root

This split must remain explicit.

## Proof Expectation

The first undeniable runtime proof for this module is:

1. API consumer submits world keys plus endpoint intent
2. runtime resolves the existing instance through projection key ontology
3. runtime resolves the callable action through endpoint-function ontology
4. generated service protocol or SDK/API rail invokes the graph mutation through Environment or Meta API
5. Meta commit receipts prove graph truth, while service receipts prove orchestration

The home-story sample should remain the anchor for that proof.
