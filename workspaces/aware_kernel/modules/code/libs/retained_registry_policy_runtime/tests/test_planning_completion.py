"""Real Code lifecycle with fixture host/issuer; no Environment qualification."""

from dataclasses import replace

import pytest
import test_operation_context as fixtures
from aware_code_retained_registry_policy_runtime import direct_host as host
from aware_code_retained_registry_policy_runtime import planning_execution as execution
from aware_code_retained_registry_policy_runtime.planning_completion import (
    retained_planning_output_body,
)
from aware_code_retained_registry_policy_runtime.planning_dependency_source import (
    retained_planning_dependency_source,
)
from aware_code_semantic_contract_runtime import (
    ContractViolation,
    PreparedSemanticEffectEnvelope,
    ProviderDerivation,
    SemanticBody,
    SemanticContractResult,
    SemanticImpactCoordinate,
    SemanticOutputEnvelope,
    SemanticTransitionEnvelope,
    TerminalStatus,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    retained_projection_body,
)
from test_contracts import body_coordinate
from test_direct_epoch_tracking import clearance
from test_planning_execution import setup


def completed(monkeypatch):
    original_profile = fixtures.planning_profile
    original_bind = execution.bind_planning_execution_origin

    def profile():
        p = original_profile()
        d = replace(
            p.providers[0],
            terminal_statuses=("delta",),
            allows_typed_empty=True,
            predecessor_required=False,
        )
        return replace(p, providers=(d,))

    def bind(h, r):
        return original_bind(h, r, terminal_mode="runtime_completion")

    with monkeypatch.context() as patch:
        patch.setattr(fixtures, "planning_profile", profile)
        patch.setattr(execution, "bind_planning_execution_origin", bind)
        values, tracker, origin, context, closure = setup(patch)
    runtime = values[0].expected.runtime
    d = runtime.profile.providers[0]
    call = replace(
        closure.invocation, requested_output_roles=runtime.profile.terminal_output_roles
    )
    closure = replace(closure, invocation=call)
    admission = selected.issue_selected_provider_execution(
        runtime, values[4], closure, operation_context=context
    )
    step = selected._execution_state(runtime, admission)[0].step_invocation
    planning = values[3].result
    planning_body = retained_projection_body(planning)
    result_body = SemanticBody(
        replace(planning_body.coordinate, role=d.result_role.role),
        planning_body.canonical_body,
    )
    transition_body = SemanticBody(
        body_coordinate("transition", d.transition_contract, "change", b"{}"), b"{}"
    )
    effect_body = SemanticBody(
        body_coordinate(d.effect_role.role, d.effect_contract, "effect", b"{}"), b"{}"
    )
    output_role = d.output_roles[0]
    output_body = SemanticBody(
        body_coordinate(
            output_role.role, output_role.contract, "meaning", b'{"meaning":1}'
        ),
        b'{"meaning":1}',
    )
    impacts = (SemanticImpactCoordinate("test", "definition", "planning"),)
    transition = SemanticTransitionEnvelope(
        d.provider_key,
        d.result_role.contract,
        d.transition_contract,
        call.predecessor,
        result_body.coordinate,
        transition_body.coordinate,
        impacts,
        step.input_closure_digest,
    )
    effect = PreparedSemanticEffectEnvelope(
        d.provider_key,
        d.effect_contract,
        transition.digest,
        call.predecessor,
        result_body.coordinate,
        effect_body.coordinate,
        (),
        impacts,
        (),
    )
    result = SemanticContractResult(
        TerminalStatus.DELTA,
        call.digest,
        transition=transition,
        effect=effect,
        outputs=(
            SemanticOutputEnvelope(
                d.provider_key, output_body.coordinate, effect.digest
            ),
        ),
    )
    values[3].result = ProviderDerivation(
        result,
        tuple(
            sorted(
                (result_body, transition_body, effect_body, output_body),
                key=lambda b: canonical_json_bytes(b.coordinate.to_wire()),
            )
        ),
    )
    completion = selected.execute_selected_provider(runtime, admission)
    return values, tracker, origin, context, completion, planning, output_body


def test_original_planning_completion_lifecycle(monkeypatch):
    values, tracker, origin, context, completion, planning, output = completed(
        monkeypatch
    )
    runtime = values[0].expected.runtime
    assert values[3].calls == 1
    assert runtime.owns_completion(completion)
    reader = retained_planning_dependency_source(origin, context)
    assert reader.read_dependencies(planning.package) == planning
    assert retained_planning_output_body(origin, context, output.coordinate) == output
    detached = retained_planning_output_body(origin, context, output.coordinate)
    object.__setattr__(detached.coordinate, "value_ref", "changed-returned-copy")
    assert retained_planning_output_body(origin, context, output.coordinate) == output
    with pytest.raises(ContractViolation):
        clearance(values[0], tracker)
    stage = execution._ORIGINS[origin][2][context]
    for change in (
        "coordinate",
        "context",
        "completion",
        "snapshot",
        "result",
        "fork",
        "stripped",
        "snapshot_copy",
    ):
        with monkeypatch.context() as patch:
            coordinate = output.coordinate
            selected_context = context
            if change == "coordinate":
                coordinate = replace(coordinate, value_ref="foreign")
            elif change == "context":
                selected_context = object()
            elif change == "completion":
                patch.setattr(stage, "completion", object())
            elif change == "snapshot":
                patch.setattr(stage, "completion_snapshot", None)
            elif change == "snapshot_copy":
                patch.setattr(
                    stage, "completion_snapshot", replace(stage.completion_snapshot)
                )
            elif change == "result":
                patch.setattr(stage, "result", object())
            elif change == "stripped":
                patch.setattr(stage, "completion", None)
                patch.setattr(stage, "completion_snapshot", None)
                with pytest.raises(ContractViolation):
                    reader.read_dependencies(planning.package)
            else:
                patch.setattr(execution.os, "getpid", lambda: -1)
            with pytest.raises((TypeError, ContractViolation)):
                retained_planning_output_body(origin, selected_context, coordinate)
    # Restoring comparison state does not change the original runtime completion.
    assert retained_planning_output_body(origin, context, output.coordinate) == output
    with runtime._publication_records_lock:
        runtime._publication_records.pop(completion)
    with pytest.raises(ContractViolation):
        reader.read_dependencies(planning.package)
    with pytest.raises(ContractViolation):
        retained_planning_output_body(origin, context, output.coordinate)
    host.close_direct_validation_host(values[1])
    with pytest.raises(ContractViolation):
        retained_planning_output_body(origin, context, output.coordinate)
