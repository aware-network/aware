# Reactivity Module Policy Contract (Program-First Install)

## Purpose

Define the canonical split between:

- policy semantic ownership,
- deterministic policy installation,
- and runtime receipt/action execution.

This contract avoids policy drift across Python/TOML/Markdown rails.

## Non-Negotiables

1. Condition/Event semantics are consumer-agnostic domain facts.
2. Module boundaries own domain policy semantics.
3. Actor reaction targeting is separate from domain-fact semantics.
4. Policy installs must be deterministic/idempotent and commit-backed.
5. TOML remains composition metadata, not dynamic policy semantic SSOT.

## Canonical Semantic Split

### What happened (reactivity policy)

- `ConditionConfig`: policy logic over commit changes
- `EventConfig`: domain semantic key raised when conditions match
- `ActionConfig`: canonical action type bound to events

Examples:

- `conversation.created`
- `conversation.message.created`

Rule:

- do not encode consumer intent in condition/event names.
- keep consumer execution intent in action binding/subscription rails.

### Who reacts (identity subscription)

- `ActorSubscription` owns actor targeting and execution preferences.
- `action_type` and execution policy are consumer linkage, not domain-fact naming.

## Declaration Contract (Runtime Declarations)

Modules may publish declaration metadata in runtime Python for discovery/versioning:

- `modules/<module>/runtime/aware_<module>/reactivity/policies.py`
- `ReactivityPolicyDeclaration`
- `ReactivityPolicyRef(module_id, policy_key, version)`

This declaration layer is the semantic/version registry, not the canonical install rail.

## Install Contract (Canonical Rail)

Canonical deterministic install rail is `.aware program`:

- module-owned programs: `modules/<module>/programs/reactivity/**/*.aware`
- executed through program executor rails (`apply_program_files`, `apply_program_ref`)
- resolved through capabilities and emitted as commit-backed function calls

Current baseline program:

- `modules/conversation/programs/reactivity/conversation_reactivity_policies_v1.aware`

Install outputs remain:

- `condition_config_id`
- `event_config_id`
- `event_config_condition_config_id`
- optional `action_config_id`
- optional `event_config_action_config_id`

## Coordinator / Installer Role

- `ReactivityPolicyCoordinator` resolves declaration identity (`module_id`, `policy_key`, `version`).
- Installer execution must remain deterministic and idempotent.
- Preferred installer implementation is program-backed, not ad-hoc per-layer UUID math.

References:

- `workspaces/aware_kernel/modules/reactivity/ontology/runtime/python/aware_reactivity/policy/contracts.py`
- `workspaces/aware_kernel/modules/reactivity/ontology/runtime/python/aware_reactivity/policy/coordinator.py`
- `services/node/tests/test_env_experience_program_reactivity_policies.py`

## Ownership Boundaries

- Reactivity runtime:
  - condition evaluation, canonical evidence writing, bridge contracts
- Module runtime:
  - semantic declaration ownership (keys/versions/descriptions)
  - module-owned policy program assets
- Identity runtime:
  - actor subscription linkage and instance-read source
- Node bridge:
  - orchestration only (`Change -> Condition -> Event -> Action` dispatch)

## Migration to Native Grammar Declarations (Later)

Long-term target can introduce first-class reactivity declarations in `.aware` grammar.

Compatibility rule:

- `policy key + version + canonical ids/edges` must remain stable.
- any future grammar declaration must compile to the same program/install/runtime contract.
