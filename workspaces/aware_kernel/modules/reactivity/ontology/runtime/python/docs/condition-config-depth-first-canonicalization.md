# Reactivity Canonicalization Status: Condition -> Event -> Action

## Purpose

Track canonical rollout status for reactivity rails:

1. `ConditionConfig` policy truth
2. `Event` emission truth
3. `Action` integration truth

and keep a precise view of what is already delivered versus what is still open.

## Non-Negotiables

1. Policy installs must use canonical constructors and deterministic ids.
2. No side-channel DTO/filter rails become SSOT.
3. Receipt-driven behavior remains commit-anchored.
4. Condition/Event keys stay consumer-agnostic domain facts.
5. Action execution remains plugin-boundary based, but evidence and linkage are canonical.

## Ownership

- Reactivity ontology/runtime: condition/event/action config + evidence rails
- Identity runtime: actor subscription binding rails
- Node bridge: receipt orchestration + evaluator/action-executor wiring
- Agent/provider runtime: action execution implementation

## Status by Gate (2026-02-11)

### Gate 1: ConditionConfig in depth

Status: delivered and validated in module/service proofs.

Delivered:

- canonical `ConditionConfig` constructors and nested branches
- primitive/enum/relationship policy modeling rails
- receipt-driven evaluator path in node reactivity bridge

Validated by:

- `workspaces/aware_kernel/modules/reactivity/ontology/runtime/python/tests/test_reactivity_module_proof.py`
- `services/node/tests/test_conversation_reactivity_module_proof.py`
- `services/node/tests/test_agent_reactivity_bridge.py`

### Gate 2: EventConfig -> Event

Status: delivered for canonical event evidence emission.

Delivered:

- `EventConfig` binding to `ConditionConfig`
- canonical runtime evidence persistence for `Event` and `EventCondition`
- projection roots/portals for event rails

Validated by:

- `workspaces/aware_kernel/modules/reactivity/ontology/runtime/python/tests/test_reactivity_module_proof.py`
- `services/node/tests/test_conversation_reactivity_module_proof.py`

### Gate 3: Event -> Action

Status: delivered for canonical action modeling + executor dispatch.

Delivered:

- `ActionConfig.create`
- `EventConfig.add_action_config`
- runtime evidence `Event.add_action` -> canonical `Action`
- bridge dispatch of canonical action bindings to action executor plugin boundary

Validated by:

- `workspaces/aware_kernel/modules/reactivity/ontology/runtime/python/tests/test_reactivity_module_proof.py`
- `services/node/tests/test_agent_reactivity_bridge.py`
- `services/node/tests/test_conversation_reactivity_module_proof.py`

## Program Install Alignment

Policy object instantiation is now aligned with program rails:

- module programs: `modules/**/programs/reactivity/**/*.aware`
- baseline: `modules/conversation/programs/reactivity/conversation_reactivity_policies_v1.aware`
- install proofs: `services/node/tests/test_env_experience_program_reactivity_policies.py`

This keeps policy install deterministic and commit-backed instead of per-layer ad-hoc seeding.

## Remaining Gaps (Do Not Overclaim)

1. Exhaustive operator matrix coverage is not complete across all modules/policies.
2. Production-scale load/perf behavior is not covered by these proofs.
3. Live external-provider behavior is validated by plugin contract tests, not full multi-node E2E in this module suite.

## Next Focus

1. Expand condition evaluator operator-coverage tests.
2. Expand module-owned policy program proofs beyond conversation baseline.
3. Keep bridge and program-install rails aligned so policy semantics are never duplicated outside canonical commits.
