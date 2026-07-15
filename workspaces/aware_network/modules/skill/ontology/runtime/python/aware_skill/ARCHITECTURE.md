# Skill Runtime Harness Architecture

This package owns Skill runtime orchestration. It does not own API request payloads, API outcomes, or Service fulfillment.

## Purpose

`aware_skill` should evolve into the Skill execution facade that turns committed `SkillConfig` truth into a committed `SkillRun` receipt:

```text
SkillConfig
  -> SkillRun
  -> SkillRunStep
  -> ApiCall
  -> ApiCallOutcome
  -> optional ServiceOperation
```

The Skill layer controls lifecycle and step order. API remains the lower invocation rail. Service remains the fulfillment rail.

## Ownership Boundary

Skill owns:

- authored orchestration identity: `SkillConfig`
- ordered authored steps: `SkillConfigStep`
- step target intent: `SkillConfigTarget` and `SkillConfigStepTarget`
- run lifecycle receipts: `SkillRun` and `SkillRunStep`
- boundary status: queued, running, succeeded, failed, skipped

API owns:

- endpoint request/response/stream contracts
- actor-provided request payload materialization
- `ApiCall` and `ApiCallOutcome`
- endpoint invocation truth through `ApiCapabilityEndpoint` and endpoint functions

Service owns:

- selected fulfillment candidate
- operation lifecycle through `ServiceOperation`
- execution backend and graph function invocation
- endpoint/function fulfillment coverage through `ServiceOperationConfigApiEndpoint*`

Skill must not duplicate payloads, response values, service operation state, or concrete graph mutation logic.

## Current Rails

The current ontology shape is already correct for the runtime facade:

- `SkillConfig.runs -> SkillRun[]`
- `SkillRun.steps -> SkillRunStep[]`
- `SkillRunStep.skill_config_step -> SkillConfigStep`
- `SkillRunStep.api_call -> aware_api.api.ApiCall?`
- `SkillConfigStep.skill_config_api_endpoint -> SkillConfigApiEndpoint`
- `SkillConfigStep.targets -> SkillConfigStepTarget[]`
- `SkillConfigStepTarget.skill_config_target -> SkillConfigTarget`
- `SkillConfigTarget.projection_experience_graph_identity -> ProjectionExperienceGraphIdentity`

The runtime package already has compile/materialization entry points:

- `aware_skill.compile`
- `aware_skill.compiler`
- `aware_skill.materialization.service`
- `aware_skill.ontology.materialization`
- generated ontology handler impls under `aware_skill.handlers.impl`

The next addition should be an `execution` subpackage, not another ontology root.

## Target Package Shape

Recommended package layout:

```text
aware_skill/
  execution/
    __init__.py
    models.py
    resolution.py
    api_calls.py
    harness.py
    service_dispatch.py
```

`models.py`

- Defines immutable request/plan/receipt dataclasses.
- Suggested names: `SkillRunRequest`, `SkillStepInput`, `ResolvedSkillExecutionPlan`, `ResolvedSkillExecutionStep`, `ExecutedSkillRun`.

`resolution.py`

- Loads committed `SkillConfig` state from the configured Skill lane.
- Sorts `SkillConfigStep` by authored `position`.
- Resolves each step endpoint requirement.
- Resolves each `SkillConfigStepTarget`.
- Validates step targets resolve through Skill/Experience graph identity truth.

`api_calls.py`

- Adapts Skill step input into API-owned `ApiInvocationIR`.
- Calls `aware_api_runtime.ontology.materialization.materialize_api_call`.
- Builds the resolved API invocation envelope with `build_resolved_api_invocation_envelope`.
- Does not persist request payloads outside API-owned `ApiCall`.

`harness.py`

- Public facade for running a Skill.
- Creates `SkillRun`.
- Creates one `ApiCall` per executed step.
- Creates `SkillRunStep` receipts linked to the authored step and API call.
- Updates only Skill boundary status.

`service_dispatch.py`

- Optional later adapter.
- Builds API Service dispatch plans and calls Service runtime ingress.
- Kept separate so the core Skill harness can create run/call receipts without importing Service execution as a hard dependency.

## Execution Flow V0

V0 should be minimal and commit-backed:

1. Input: `skill_config_id`, `run_key`, actor id, lane context, and per-step actor payloads.
2. Resolve committed `SkillConfig` and ordered `SkillConfigStep` rows.
3. Validate every executable step has one `SkillConfigApiEndpoint`.
4. Validate every declared step target points to a `SkillConfigTarget` over `ProjectionExperienceGraphIdentity`.
5. Create `SkillRun` with `running` status.
6. For each step, materialize an API-owned `ApiCall` using actor-provided input.
7. Create `SkillRunStep` linked to the authored `SkillConfigStep` and the resulting `ApiCall`.
8. Mark the `SkillRunStep` succeeded or failed based only on call creation and optional dispatch outcome.
9. Mark `SkillRun` succeeded if all required steps succeeded, otherwise failed.

This proves the orchestration envelope without making Skill responsible for Product B clients or Service execution.

## Validation Contract

The runtime facade should fail closed when the contract chain is incomplete:

```text
SkillConfigStep
  -> SkillConfigApiEndpoint
  -> ApiCapabilityEndpoint
  -> SkillConfigStepTarget
  -> SkillConfigTarget
  -> ProjectionExperienceGraphIdentity
```

V0 should validate the Skill-to-API side:

- step endpoint requirement exists
- API endpoint exists
- step target exists
- Skill target exists
- Skill target belongs to the same `SkillConfig`
- Skill target resolves to an Experience graph identity

The Service side should remain optional until `service_dispatch.py` is introduced:

- endpoint fulfillment candidate exists
- endpoint function fulfillment is covered
- graph identity target fulfillment is covered by the adapter policy

## API Integration

Skill should not call `ApiCapabilityEndpoint.create_call` directly for non-empty actor inputs because that handler currently creates an empty request payload. The harness should use:

- `aware_api_runtime.invocation.resolve_api_invocation_ir`
- `aware_api_runtime.ontology.materialization.materialize_api_call`
- `aware_api_runtime.invocation.build_resolved_api_invocation_envelope`

This keeps request payload materialization on the API rail and gives Service dispatch the committed envelope it already expects.

## Service Integration

Service dispatch is a later layer over the API envelope:

```text
ApiCall envelope
  -> ApiServiceDispatchPlan
  -> execute_service_api_dispatch_plan
  -> ServiceOperation
  -> ApiCallOutcome
```

The core Skill harness should depend on an adapter seam, not directly on Service host mechanics. That keeps Skill usable for dry-run planning, API call creation, and future UI run status before full Service execution is available.

## Implementation Phases

Phase 1: planner

- Add `aware_skill.execution.models`.
- Add `aware_skill.execution.resolution`.
- Prove committed Skill config resolution, step order, endpoint lock, and Experience target validation.

Phase 2: run materialization

- Add `aware_skill.execution.api_calls`.
- Add `aware_skill.execution.harness`.
- Create `SkillRun`, `ApiCall`, and `SkillRunStep` receipts.
- Do not execute Service yet.

Phase 3: Service preflight

- Add `aware_skill.execution.service_dispatch`.
- Validate Service endpoint, function, target, and target-function coverage before execution.

Phase 4: Service execution

- Use existing Service API ingress to execute selected dispatch plans.
- Reflect only boundary status back to `SkillRunStep`.
- Keep operation details in `ServiceOperation` and outcomes in `ApiCallOutcome`.

Phase 5: experience/key resolution

- Add higher-level target selection helpers.
- Resolve actor-friendly target keys to concrete graph identity through Experience contracts.
- Keep Skill target references stable while allowing runtime-selected object identity.

## Proof Strategy

Each implementation phase needs a focused module proof:

- planner proof: committed Skill config resolves ordered steps and Experience graph identity targets
- API call proof: non-empty actor payload lands only in `ApiCall.request_model`
- run proof: `SkillRunStep.api_call_id` matches the step endpoint requirement
- failure proof: missing target identity or endpoint mismatch fails before creating terminal Skill status
- Service proof: dispatch adapter validates endpoint/function and graph identity fulfillment before execution

The first implementation should stop at planner plus API call materialization. Service execution should come after the facade can prove Skill-owned run receipts over API-owned calls.
