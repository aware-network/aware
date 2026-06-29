# Aware Reactivity Runtime

This module owns receipt-driven reactivity execution over canonical commits.

## Purpose

Provide one canonical rail for:

- `Change -> Condition -> Event -> Action`

without adding side-channel truth stores.

Canonical truth is always commit history + lane heads. Reactivity consumes receipts and writes evidence/actions back as commits.

## Canonical Invariants

1. Commits/lane heads are SSOT.
2. Reactivity evaluation is receipt-derived, not provider-memory-derived.
3. Condition/Event keys are consumer-agnostic domain facts.
4. Actor-specific execution intent is bound via `ActorSubscription` and action bindings.
5. Action execution side effects must reconcile to canonical commits.

## Current Runtime Shape (2026-02-11)

Node hook and bridge:

- `services/node/aware_node_service/duplex/lane_commit_receipt_bus.py`
- `services/node/aware_node_service/reactivity/agent_reactivity_bridge.py`

Runtime boundaries:

- subscription source contracts: `services/node/aware_node_service/reactivity/subscription_sources.py`
- bridge contracts: `services/node/aware_node_service/reactivity/contracts.py`
- condition evaluator: `workspaces/aware_kernel/modules/reactivity/ontology/runtime/python/aware_reactivity/condition/evaluator.py`
- canonical evidence writer: `workspaces/aware_kernel/modules/reactivity/ontology/runtime/python/aware_reactivity/evidence/writer.py`

Feature switches:

- `AWARE_NODE_AGENT_REACTIVITY_BRIDGE_ENABLED=1`
- `AWARE_NODE_AGENT_REACTIVITY_ACTION_EXECUTOR_ENABLED=1`
- `AWARE_NODE_AGENT_REACTIVITY_ACTION_EXECUTOR_FACTORY`

Canonical subscription source mode (preferred):

- API-first identity read: `Identity.list_actor_subscriptions`
- fallback materialized `ActorSubscription` lane reads
- actor subscription anchors target lane via `oig_branch -> ObjectInstanceGraphIdentity`

## Policy Install Contract (Program-First)

Policy semantics remain module-owned, but deterministic install is now canonicalized via `.aware program`.

Program asset locations:

- `modules/**/programs/reactivity/**/*.aware` (module-owned policies)
- `configs/programs/` reserved for operator/product rollups

Current baseline:

- `modules/conversation/programs/reactivity/conversation_reactivity_policies_v1.aware`

Install rails:

- env experience path mode: `--install-program <path>`
- env experience ref mode: `--install-program-ref <module_id>:<program_name>`

Program execution is commit-backed and capability-resolved; stable ids are derived from canonical stable-id rails.

Reference:

- `services/node/tests/test_env_experience_program_reactivity_policies.py`
- `workspaces/aware_kernel/modules/reactivity/ontology/runtime/python/docs/module-level-policy-runtime-contract.md`

## Validation Status (What Is Actually Proven)

As of now, reactivity is validated in layered proofs:

1. Evaluator operator-unit coverage (`workspaces/aware_kernel/modules/reactivity/ontology/runtime/python/tests/test_condition_evaluator_operator_unit.py`)
- state flags (`changed`, `exists`, `is_null`, etc.)
- numeric/coercion comparisons and range bounds
- string/collection operators (`contains`, `in`, `matches_regex`, etc.)
- delta operators (`increased`, `decreased`)
- unknown-operator fallback behavior

2. Reactivity module proofs (`workspaces/aware_kernel/modules/reactivity/ontology/runtime/python/tests/test_reactivity_module_proof.py`)
- projection roots and portals (`condition_config`, `event_config`, `action_config`)
- `ConditionConfig` constructors + nested condition branches
- `EventConfig.add_condition_config`
- `ActionConfig.create`
- `EventConfig.add_action_config`
- evidence constructors and ids: `Condition`, `Event`, `EventCondition`, `Action`

3. Identity subscription proofs (`modules/identity/runtime/tests/test_actor_subscription_module_proof.py`)
- actor subscription portal binding to reactivity event rails
- deterministic `ActorSubscription.create`
- canonical identity instance read (`Identity.list_actor_subscriptions`)

4. Bridge unit proofs (`services/node/tests/test_agent_reactivity_bridge.py`)
- dedupe/filter behavior
- canonical condition gating
- canonical action binding propagation
- action executor invocation + failure isolation behavior
- multi-action dispatch control flow:
  - stop on failure when `continue_on_fail=false`
  - continue in-order when `continue_on_fail=true`

5. Conversation integration proofs (`services/node/tests/test_conversation_reactivity_module_proof.py`)
- receipt -> condition evaluation -> event emission path
- action executor trigger with canonical `event_config_action_config` binding
- assistant-message commit performed as target agent actor

6. Program-install idempotency proof (`services/node/tests/test_env_experience_program_reactivity_policies.py`)
- module policy programs install deterministic condition/event/action config lanes
- re-apply does not drift lane heads

## Can We Claim "Reactivity Is Validated"?

Yes, with scope boundaries:

- We can claim canonical reactivity rails are validated for config modeling, binding, receipt-driven evaluation, event/action evidence persistence, and action-executor triggering in automated proofs.
- We should not claim exhaustive validation for every operator combination, every module policy set, or production-scale load/perf behavior.

## Agent ROI (Conversation)

Conversation remains the first canonical consumer:

1. Conversation receipt is the trigger.
2. Condition policies evaluate domain facts.
3. Event semantics stay consumer-agnostic.
4. Actor subscription + action binding select execution target and action type.
5. Side effects reconcile as canonical commits (for example assistant message written as agent actor).

## Next Coverage Focus

1. Expand operator-coverage proofs for condition evaluator branches.
2. Add more module policy program proofs (beyond conversation baseline).
3. Keep program-ref install path and bridge behavior aligned as default reactivity install/execution rail.
