# Aware Interface Runtime

`workspaces/aware_network/modules/interface/ontology/runtime/python` owns the Python-native interface runtime for Aware.

This is the owner of local interface-runtime semantics over the interface/window ontology:

- local replicated interface backend direction
- interface-local persistence and replay/materialization semantics
- module-owned runtime behavior for interface/window objects
- host-neutral lifecycle coordination consumed by concrete interface hosts

It is not the command host. `aware-cli` is the host surface for terminal agents and should consume this runtime rather than re-own its local DB/materialization logic.

## Canonical Owner Split

- `workspaces/aware_network/modules/interface/ontology/runtime/python`
  - owns the Python-native interface runtime, local replicated backend, and host-neutral lifecycle coordination
- `modules/experience`
  - owns canonical experience/view resolution consumed by interface hosts
- `workspaces/aware_network/modules/environment`
  - owns gate policy and routing truth consumed by interface hosts
- `workspaces/aware_network/modules/interface/sdks/interface`
  - owns concrete renderer-to-Interface attachment, transport registration, and
    boot-runtime port binding
- `tools/cli`
  - owns command/render/agent host UX
- `libs/session/python`
  - remains a lower-level compatibility library hidden behind `workspaces/aware_network/modules/interface/sdks/interface`
    for renderer attachment paths
- `libs/api`
  - owns API discovery/loading and remote call helpers
- `libs/environment`
  - owns environment law, roots, and local/remote status view boundaries

## Direction

The human Flutter interface already proves the pattern: a host surface over a local interface backend with commit replay, SQLite projection, and lane-sync mechanisms.

Python should converge on the same class of mechanism here for headless and agent-facing interfaces:

- local interface DB boot
- local commit/snapshot/lane-head/projection-cursor stores
- lane sync and commit-backed materialization
- actor-scoped local interface state such as focus/layout/session cursors
- host-neutral coordinator state for:
  - bootstrap
  - gate consumption
  - section focus resolution
  - act/receipt/refresh loops

The first interface-owned host bridge now lives under:

- `workspaces/aware_network/modules/interface/ontology/runtime/python/aware_interface/host_runtime.py`
- `workspaces/aware_network/modules/interface/ontology/runtime/python/aware_interface/lifecycle/*`
- `workspaces/aware_network/modules/interface/ontology/runtime/python/aware_interface/ports/*`

Concrete hosts should bind those surfaces rather than reassembling the interface DB, lane stores, materializer, and projector locally.

The runtime owns only the host-neutral port contract:

- `aware_interface.ports.session.InterfaceSessionPort`

Concrete attachment adapters now belong to `workspaces/aware_network/modules/interface/sdks/interface`. Hosts should ask
the SDK for an attachment/runtime port instead of constructing lower-level
session wrappers in service or runtime code.

Remote commits remain the shared canonical truth. Local interface state is rebuildable replica truth owned by the interface runtime.

## Next Framework Layer

The next module-owned layer should not be another concrete host. It should be a shared host-capability framework under `aware_interface` that concrete hosts consume.

That framework should own:

- host-neutral capability contracts
- normalized capability state, action, and dependency models
- composition helpers that are still renderer-agnostic and product-agnostic
- ports that let concrete hosts bind workspace, local-runtime, identity, hosted-service, or future capability providers without re-owning the base abstraction

That framework should not own:

- Interface Host product copy or screen wording
- workspace-first product composition
- daemon / namespace / IPC concerns
- renderer shell composition

So the stable split is:

- `workspaces/aware_network/modules/interface/ontology/runtime/python`
  - owns the common host/runtime framework
- `workspaces/aware_network/modules/interface/services/interface`
  - owns the Interface Host product and local deployment boundary over that framework

This is how `Interface != Workspace` remains real even while today’s first Interface Host product still uses Workspace as a major consumer surface.

## Ownership Matrix

Use this split when deciding where new behavior lives:

- `modules/workspace` and Workspace service own workspace truth
  - workspace registry truth
  - semantic source truth
  - committed semantic package family/member truth
  - workspace materialization and preview truth
  - workspace read models and workspace DTOs
- `workspaces/aware_network/modules/interface/ontology/runtime/python` owns the shared interface host framework
  - host-capability contracts
  - normalized capability state/action/operation models
  - host-neutral coordinator and layout primitives
  - composition helpers that are still product-agnostic
- `workspaces/aware_network/modules/interface/services/interface` owns the concrete Interface Host product
  - product composition and precedence
  - host gates and host actions
  - daemon / namespace / IPC / deployment ownership
  - concrete capability consumers over workspace, local runtime, identity, and hosted services

Negative rule:

- if another non-Interface consumer would need the same truth, it does not belong in `workspaces/aware_network/modules/interface/services/interface`
- if the concern is host deployment, host gating, host sequencing, or host UX composition, it does not belong in `modules/workspace`

## Specs

The canonical contract for this owner split and runtime decomposition lives in:

- `workspaces/aware_network/modules/interface/docs/specs/runtime-flow/SPEC.md`
- `workspaces/aware_network/modules/interface/docs/specs/host-runtime-bridge/SPEC.md`
- `workspaces/aware_network/modules/interface/docs/specs/local-backend/SPEC.md`
- `workspaces/aware_network/modules/interface/docs/specs/local-db/SPEC.md`
- `workspaces/aware_network/modules/interface/docs/specs/lane-stores/SPEC.md`
- `workspaces/aware_network/modules/interface/docs/specs/commit-materialization/SPEC.md`
- `workspaces/aware_network/modules/interface/docs/specs/projection-runtime/SPEC.md`
- `workspaces/aware_network/modules/interface/docs/specs/lane-sync/SPEC.md`
